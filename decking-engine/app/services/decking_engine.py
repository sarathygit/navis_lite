"""Expert Decking algorithm.

Given an incoming container, generates every structurally legal candidate slot,
scores each with the ML dwell-time model plus a shuffle-risk heuristic, and
selects the best one. Two hard constraints gate candidate generation before
scoring ever happens. When nothing is legal, the engine proposes the single
best housekeeping move that would make the container placeable.

  1. Stacking policy: tier 1 is the ground and accepts anything; above it a
     container may only rest on one at least as heavy, so stacks build
     heaviest-at-the-bottom. Stacks also fill bottom-up — no floating slots.
  2. Reefer policy: REEFER containers may only be placed in the powered Block-R;
     non-reefer containers may never be placed in Block-R (it's a hard boundary
     in both directions, not just a preference).
"""

from datetime import datetime, timezone
from typing import Optional

from app.core.config import (
    HEAVY_WEIGHT_THRESHOLD_KG,
    MAX_REHANDLE_DELTA_DAYS,
    REEFER_BLOCK,
    RELOCATION_URGENCY_HORIZON_DAYS,
    REHANDLE_PENALTY_HIGH_THRESHOLD,
    REHANDLE_PENALTY_MEDIUM_THRESHOLD,
    STANDARD_BLOCKS,
)
from app.models.schemas import (
    DeckingRequest,
    DeckingResponse,
    RelocationSuggestion,
    ReleaseSlotResponse,
)
from app.services.ml_model import dwell_time_model
from app.services.yard_state import SlotOccupant, YardState


def can_stack_on(candidate_weight_kg: float, below: Optional[SlotOccupant]) -> bool:
    """Whether a container may physically rest on what is beneath it.

    Tier 1 is the ground: anything may be set down on a free ground slot, which
    is how a real terminal behaves — a light container arriving at an empty yard
    is simply placed, never turned away.

    Above ground, a container may only sit on one at least as heavy. A container's
    corner posts carry a rated stacking load, and putting a heavier box on a
    lighter one both risks crushing it and lifts the stack's centre of gravity.
    The effect is that stacks naturally build heaviest-at-the-bottom.
    """
    if below is None:
        return True
    return candidate_weight_kg <= below.weight_kg


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


def _legal_candidates(weight_kg: float, reefer: bool, yard: YardState,
                       exclude_stack: Optional[tuple[str, int, int]] = None) -> list["Candidate"]:
    """Every slot this container could legally occupy right now, scored.

    `exclude_stack` removes one whole stack from consideration during a
    relocation search. It has to be the whole stack, not just the slot being
    vacated: lifting a container off a stack changes that stack's geometry, so
    the slot immediately above it is only "open" while the container is still
    there holding it up. Proposing that slot would tell the crane to set the
    container back down on top of itself.
    """
    candidates: list[Candidate] = []
    for block in eligible_blocks(reefer):
        for row, bay in yard.candidate_stacks(block):
            open_tier = yard.next_open_tier(block, row, bay)
            if open_tier is None:
                continue
            if exclude_stack is not None and (block, row, bay) == exclude_stack:
                continue
            below = yard.occupant_below(block, row, bay, open_tier)
            if not can_stack_on(weight_kg, below):
                continue
            dwell_days = dwell_time_model.predict(weight_kg, reefer, open_tier)
            risk = compute_shuffle_risk(dwell_days, below)
            candidates.append(Candidate(block, row, bay, open_tier, dwell_days, risk))
    return candidates


def _remaining_dwell(occupant: SlotOccupant) -> float:
    """Roughly how much longer this container is expected to stay.

    The model predicts total dwell at placement time, so what is left is that
    estimate minus the time already served. Never negative — an overdue
    container is treated as leaving imminently.
    """
    placed_at = occupant.placed_at
    if placed_at.tzinfo is None:
        # Defensive: a naive timestamp from any source would otherwise raise
        # TypeError here and fail the whole placement request.
        placed_at = placed_at.replace(tzinfo=timezone.utc)
    elapsed_days = (datetime.now(timezone.utc) - placed_at).total_seconds() / 86_400.0
    return max(0.0, occupant.dwell_time_estimate - elapsed_days)


def suggest_relocation(request: DeckingRequest, yard: YardState) -> Optional[RelocationSuggestion]:
    """Finds the single best container to move so the arriving one can be placed.

    Only proposes a move that actually solves the problem: the container must be
    liftable (nothing stacked on it), it must have somewhere legal to go, and
    freeing its slot must genuinely make the arriving container placeable.

    Among the moves that work, the cheapest is chosen. Cost has two parts:

      * the destination's own shuffle risk, so relocating does not simply create
        tomorrow's rehandle somewhere else; and
      * an urgency penalty for disturbing a container that is about to leave —
        moving a box that departs in hours is wasted crane work, while one
        staying for days has to sit somewhere regardless.
    """
    best: Optional[RelocationSuggestion] = None
    best_cost: Optional[float] = None

    for block, row, bay, tier, occupant in list(yard.all_slots()):
        if occupant is None:
            continue

        # Only the top of a stack can be lifted.
        if yard.occupants_above(block, row, bay, tier):
            continue

        # Where could this container go instead? Never back into its own stack.
        destinations = _legal_candidates(
            occupant.weight_kg, occupant.reefer, yard, exclude_stack=(block, row, bay)
        )
        if not destinations:
            continue
        destination = min(destinations, key=Candidate.score)

        # Would freeing this slot actually let the arriving container in?
        below_origin = yard.occupant_below(block, row, bay, tier)
        if not can_stack_on(request.weight_kg, below_origin):
            continue
        if request.reefer != (block == REEFER_BLOCK):
            continue

        urgency_penalty = max(0.0, RELOCATION_URGENCY_HORIZON_DAYS - _remaining_dwell(occupant))
        cost = destination.shuffle_risk * 10.0 + urgency_penalty

        if best_cost is None or cost < best_cost:
            best_cost = cost
            best = RelocationSuggestion(
                move_container_id=occupant.container_id,
                from_block=block, from_row=row, from_bay=bay, from_tier=tier,
                to_block=destination.block, to_row=destination.row,
                to_bay=destination.bay, to_tier=destination.tier,
                then_place_at_block=block, then_place_at_row=row,
                then_place_at_bay=bay, then_place_at_tier=tier,
                reason=(
                    f"Relocate {occupant.container_id} from "
                    f"{block}-{row:02d}-{bay:02d} tier {tier} to "
                    f"{destination.block}-{destination.row:02d}-{destination.bay:02d} "
                    f"tier {destination.tier}, freeing {block}-{row:02d}-{bay:02d} "
                    f"tier {tier} for {request.container_id}"
                ),
            )

    return best


def find_best_slot(request: DeckingRequest, yard: YardState) -> DeckingResponse:
    with yard.lock():
        candidates = _legal_candidates(request.weight_kg, request.reefer, yard)

        if not candidates:
            suggestion = suggest_relocation(request, yard)
            return DeckingResponse(
                placed=False,
                reason=(
                    f"No slot available for {request.container_id} "
                    f"({request.weight_kg:.0f}kg, {'reefer' if request.reefer else 'dry'})"
                ),
                suggestion=suggestion,
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
