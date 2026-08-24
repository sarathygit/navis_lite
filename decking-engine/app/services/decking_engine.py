"""Expert Decking algorithm.

Given an incoming container, generates every structurally legal candidate slot,
scores each with the ML dwell-time model plus a shuffle-risk heuristic, and
selects the best one. Two hard constraints gate candidate generation before
scoring ever happens:

  1. Weight policy: heavy cargo (>20,000 kg) is restricted to Tier 1-2; light
     cargo is restricted to Tier 3-5. Stacks fill bottom-up, so this also means
     a stack needs a heavy "base" before it can accept a light container above it.
  2. Reefer policy: REEFER containers may only be placed in the powered Block-R;
     non-reefer containers may never be placed in Block-R (it's a hard boundary
     in both directions, not just a preference).
"""

from datetime import datetime, timezone
from typing import Optional

from app.core.config import (
    HEAVY_ALLOWED_TIERS,
    HEAVY_WEIGHT_THRESHOLD_KG,
    LIGHT_ALLOWED_TIERS,
    MAX_REHANDLE_DELTA_DAYS,
    REEFER_BLOCK,
    REHANDLE_PENALTY_HIGH_THRESHOLD,
    REHANDLE_PENALTY_MEDIUM_THRESHOLD,
    STANDARD_BLOCKS,
)
from app.models.schemas import DeckingRequest, DeckingResponse, ReleaseSlotResponse
from app.services.ml_model import dwell_time_model
from app.services.yard_state import SlotOccupant, YardState


def allowed_tiers_for_weight(weight_kg: float) -> tuple[int, ...]:
    return HEAVY_ALLOWED_TIERS if weight_kg > HEAVY_WEIGHT_THRESHOLD_KG else LIGHT_ALLOWED_TIERS


def eligible_blocks(reefer: bool) -> list[str]:
    return [REEFER_BLOCK] if reefer else list(STANDARD_BLOCKS)


def compute_shuffle_risk(candidate_dwell_days: float, below: Optional[SlotOccupant]) -> float:
    """Risk that this container will be buried under something that needs to
    stay after it leaves. Zero if nothing is below, or if the container below
    has an equal-or-shorter remaining dwell than this one (it'll clear out
    first, or at the same time, so no shuffle is ever forced)."""
    if below is None:
        return 0.0
    return max(0.0, candidate_dwell_days - below.dwell_time_estimate)


def normalize_penalty(raw_risk_days: float) -> tuple[float, str]:
    """Converts a raw day-delta rehandle risk into a 0-100% score and a
    HIGH/MEDIUM/LOW flag, saturating at MAX_REHANDLE_DELTA_DAYS."""
    score = round(min(100.0, (raw_risk_days / MAX_REHANDLE_DELTA_DAYS) * 100.0), 1)
    if score >= REHANDLE_PENALTY_HIGH_THRESHOLD:
        flag = "HIGH"
    elif score >= REHANDLE_PENALTY_MEDIUM_THRESHOLD:
        flag = "MEDIUM"
    else:
        flag = "LOW"
    return score, flag


class Candidate:
    __slots__ = ("block", "row", "bay", "tier", "dwell_days", "shuffle_risk")

    def __init__(self, block: str, row: int, bay: int, tier: int, dwell_days: float, shuffle_risk: float):
        self.block = block
        self.row = row
        self.bay = bay
        self.tier = tier
        self.dwell_days = dwell_days
        self.shuffle_risk = shuffle_risk

    def score(self) -> float:
        # Shuffle risk dominates the ranking; dwell time is the tiebreaker.
        return self.shuffle_risk * 10.0 + self.dwell_days


def find_best_slot(request: DeckingRequest, yard: YardState) -> DeckingResponse:
    tiers = allowed_tiers_for_weight(request.weight_kg)
    blocks = eligible_blocks(request.reefer)

    candidates: list[Candidate] = []
    with yard.lock():
        for block in blocks:
            for row, bay in yard.candidate_stacks(block):
                open_tier = yard.next_open_tier(block, row, bay)
                if open_tier is None or open_tier not in tiers:
                    continue
                dwell_days = dwell_time_model.predict(request.weight_kg, request.reefer, open_tier)
                below = yard.occupant_below(block, row, bay, open_tier)
                risk = compute_shuffle_risk(dwell_days, below)
                candidates.append(Candidate(block, row, bay, open_tier, dwell_days, risk))

        if not candidates:
            return DeckingResponse(
                placed=False,
                reason=(
                    f"No open slot available for weight={request.weight_kg}kg "
                    f"reefer={request.reefer} within allowed tiers {tiers}"
                ),
            )

        best = min(candidates, key=Candidate.score)

        occupant = SlotOccupant(
            container_id=request.container_id,
            weight_kg=request.weight_kg,
            reefer=request.reefer,
            dwell_time_estimate=best.dwell_days,
            placed_at=datetime.now(timezone.utc),
        )
        yard.place(best.block, best.row, best.bay, best.tier, occupant)

    penalty_score, penalty_flag = normalize_penalty(best.shuffle_risk)

    return DeckingResponse(
        block=best.block,
        row=best.row,
        bay=best.bay,
        tier=best.tier,
        dwell_time_estimate=best.dwell_days,
        shuffle_risk_score=penalty_score,
        penalty_flag=penalty_flag,
        placed=True,
        reason=f"Assigned to {best.block}-{best.row:02d}-{best.bay:02d} tier {best.tier}",
    )


def live_slot_risk(yard: YardState, block: str, row: int, bay: int, tier: int, occupant: SlotOccupant) -> tuple[float, str]:
    """Recomputes an already-placed occupant's rehandle risk against whatever
    is below it right now (used for yard tooltips and the terminal-wide
    efficiency index, as opposed to the risk computed once at placement time)."""
    below = yard.occupant_below(block, row, bay, tier)
    raw_risk = compute_shuffle_risk(occupant.dwell_time_estimate, below)
    return normalize_penalty(raw_risk)


def release_container(container_id: str, yard: YardState) -> ReleaseSlotResponse:
    """Pulls a container out of the yard for gate-out, if it's physically
    reachable. A container buried under others cannot be pulled directly —
    this mirrors real yard ops, where a crane operator (not the TOS) decides
    the shuffle sequence to clear what's on top first."""
    with yard.lock():
        coord = yard.find_slot_by_container_id(container_id)
        if coord is None:
            return ReleaseSlotResponse(
                released=False,
                reason=f"Container {container_id} was not found in the yard",
            )

        block, row, bay, tier = coord
        above = yard.occupants_above(block, row, bay, tier)
        if above:
            blocking_ids = [occupant.container_id for occupant in above]
            return ReleaseSlotResponse(
                released=False,
                block=block,
                row=row,
                bay=bay,
                tier=tier,
                blocking_container_ids=blocking_ids,
                reason=(
                    f"Container {container_id} is buried under {len(blocking_ids)} "
                    f"container(s) at {block}-{row:02d}-{bay:02d}: {', '.join(blocking_ids)}"
                ),
            )

        yard.release(block, row, bay, tier)
        return ReleaseSlotResponse(
            released=True,
            block=block,
            row=row,
            bay=bay,
            tier=tier,
            reason=f"Released {container_id} from {block}-{row:02d}-{bay:02d} tier {tier}",
        )
