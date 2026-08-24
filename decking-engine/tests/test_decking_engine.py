from datetime import datetime, timezone

from app.models.schemas import DeckingRequest
from app.services.decking_engine import (
    allowed_tiers_for_weight,
    compute_shuffle_risk,
    eligible_blocks,
    find_best_slot,
    live_slot_risk,
    normalize_penalty,
    release_container,
)
from app.services.yard_state import SlotOccupant, YardState


def test_allowed_tiers_for_weight_heavy():
    assert allowed_tiers_for_weight(25_000) == (1, 2)


def test_allowed_tiers_for_weight_light():
    assert allowed_tiers_for_weight(5_000) == (3, 4, 5)


def test_allowed_tiers_boundary_is_exclusive():
    # exactly 20,000kg is not "heavy" (spec: >20,000kg)
    assert allowed_tiers_for_weight(20_000) == (3, 4, 5)


def test_eligible_blocks_reefer_restricted_to_block_r():
    assert eligible_blocks(reefer=True) == ["R"]


def test_eligible_blocks_dry_excludes_block_r():
    blocks = eligible_blocks(reefer=False)
    assert "R" not in blocks
    assert set(blocks) == {"A", "B", "C"}


def test_compute_shuffle_risk_no_container_below_is_zero():
    assert compute_shuffle_risk(candidate_dwell_days=5.0, below=None) == 0.0


def test_compute_shuffle_risk_positive_when_this_container_outlasts_the_one_below():
    below = SlotOccupant("X", 21000, False, dwell_time_estimate=3.0, placed_at=datetime.now(timezone.utc))
    # this container will dwell 5 days, longer than the 3-day container below it:
    # the one below wants out first but this one blocks it -> risk
    assert compute_shuffle_risk(candidate_dwell_days=5.0, below=below) == 2.0


def test_compute_shuffle_risk_zero_when_below_outlasts_this_container():
    below = SlotOccupant("X", 21000, False, dwell_time_estimate=10.0, placed_at=datetime.now(timezone.utc))
    assert compute_shuffle_risk(candidate_dwell_days=4.0, below=below) == 0.0


def test_reefer_container_never_placed_outside_block_r():
    yard = YardState()
    request = DeckingRequest(containerId="ABCD1234567", weightKg=25_000, reefer=True)
    response = find_best_slot(request, yard)
    assert response.placed is True
    assert response.block == "R"
    assert response.tier in (1, 2)


def test_non_reefer_container_never_placed_in_block_r():
    yard = YardState()
    request = DeckingRequest(containerId="ABCD1234567", weightKg=25_000, reefer=False)
    response = find_best_slot(request, yard)
    assert response.placed is True
    assert response.block in ("A", "B", "C")


def test_heavy_container_only_ever_assigned_tier_1_or_2():
    yard = YardState()
    request = DeckingRequest(containerId="ABCD1234567", weightKg=27_500, reefer=False)
    response = find_best_slot(request, yard)
    assert response.placed is True
    assert response.tier in (1, 2)


def test_light_container_rejected_when_no_structural_base_exists():
    # empty yard: tier 1/2 are unoccupied everywhere, so a light container has
    # nothing to stack on top of yet (tiers 3-5 would be physically unsupported)
    yard = YardState()
    request = DeckingRequest(containerId="ABCD1234567", weightKg=5_000, reefer=False)
    response = find_best_slot(request, yard)
    assert response.placed is False
    assert response.reason is not None


def test_light_container_placed_once_base_layer_exists():
    yard = YardState()
    base_occupant = SlotOccupant("BASE0000001", 22_000, False, dwell_time_estimate=15.0, placed_at=datetime.now(timezone.utc))
    yard.place("A", 1, 1, 1, base_occupant)
    yard.place("A", 1, 1, 2, base_occupant)

    request = DeckingRequest(containerId="ABCD1234567", weightKg=5_000, reefer=False)
    response = find_best_slot(request, yard)

    assert response.placed is True
    assert response.tier == 3
    assert response.block == "A"


def test_release_container_not_found():
    yard = YardState()
    response = release_container("ABCD1234567", yard)
    assert response.released is False
    assert response.blocking_container_ids == []


def test_release_container_succeeds_when_nothing_stacked_above():
    yard = YardState()
    occupant = SlotOccupant("ABCD1234567", 22_000, False, dwell_time_estimate=5.0, placed_at=datetime.now(timezone.utc))
    yard.place("A", 1, 1, 1, occupant)

    response = release_container("ABCD1234567", yard)

    assert response.released is True
    assert response.block == "A"
    assert response.tier == 1
    assert yard.find_slot_by_container_id("ABCD1234567") is None


def test_release_container_blocked_when_buried():
    yard = YardState()
    base1 = SlotOccupant("BASE0000001", 22_000, False, dwell_time_estimate=15.0, placed_at=datetime.now(timezone.utc))
    base2 = SlotOccupant("BASE0000002", 21_000, False, dwell_time_estimate=15.0, placed_at=datetime.now(timezone.utc))
    on_top = SlotOccupant("TOPC0000001", 5_000, False, dwell_time_estimate=2.0, placed_at=datetime.now(timezone.utc))
    yard.place("A", 1, 1, 1, base1)
    yard.place("A", 1, 1, 2, base2)
    yard.place("A", 1, 1, 3, on_top)

    response = release_container("BASE0000001", yard)

    assert response.released is False
    assert response.blocking_container_ids == ["BASE0000002", "TOPC0000001"]
    # nothing was actually removed
    assert yard.find_slot_by_container_id("BASE0000001") == ("A", 1, 1, 1)


def test_release_container_succeeds_after_blocker_cleared():
    yard = YardState()
    base = SlotOccupant("BASE0000001", 22_000, False, dwell_time_estimate=15.0, placed_at=datetime.now(timezone.utc))
    on_top = SlotOccupant("TOPC0000001", 5_000, False, dwell_time_estimate=2.0, placed_at=datetime.now(timezone.utc))
    yard.place("A", 1, 1, 1, base)
    yard.place("A", 1, 1, 2, on_top)

    # clear the blocker first
    top_response = release_container("TOPC0000001", yard)
    assert top_response.released is True

    # now the base container is reachable
    base_response = release_container("BASE0000001", yard)
    assert base_response.released is True


def test_normalize_penalty_zero_risk_is_low():
    score, flag = normalize_penalty(0.0)
    assert score == 0.0
    assert flag == "LOW"


def test_normalize_penalty_saturates_at_max_delta():
    score, flag = normalize_penalty(999.0)  # far beyond MAX_REHANDLE_DELTA_DAYS
    assert score == 100.0
    assert flag == "HIGH"


def test_normalize_penalty_medium_boundary():
    # MAX_REHANDLE_DELTA_DAYS=10, MEDIUM threshold=33% -> 3.3 days raw risk
    score, flag = normalize_penalty(4.0)
    assert score == 40.0
    assert flag == "MEDIUM"


def test_normalize_penalty_low_below_medium_threshold():
    score, flag = normalize_penalty(2.0)
    assert score == 20.0
    assert flag == "LOW"


def test_live_slot_risk_reflects_current_yard_state_not_placement_time():
    yard = YardState()
    long_dwell_below = SlotOccupant("BASE0000001", 22_000, False, dwell_time_estimate=15.0, placed_at=datetime.now(timezone.utc))
    short_dwell_above = SlotOccupant("TOPC0000001", 5_000, False, dwell_time_estimate=2.0, placed_at=datetime.now(timezone.utc))
    yard.place("A", 1, 1, 1, long_dwell_below)
    yard.place("A", 1, 1, 2, short_dwell_above)

    # the container below has a LONGER dwell than what's stacked above it, so no risk
    score, flag = live_slot_risk(yard, "A", 1, 1, 1, long_dwell_below)
    assert score == 0.0
    assert flag == "LOW"


def test_live_slot_risk_flags_high_when_a_container_traps_a_shorter_stay_one_below_it():
    yard = YardState()
    short_dwell_below = SlotOccupant("BASE0000001", 22_000, False, dwell_time_estimate=1.0, placed_at=datetime.now(timezone.utc))
    long_dwell_above = SlotOccupant("TOPC0000001", 5_000, False, dwell_time_estimate=11.0, placed_at=datetime.now(timezone.utc))
    yard.place("A", 1, 1, 1, short_dwell_below)
    yard.place("A", 1, 1, 2, long_dwell_above)

    # the container below wants to leave in 1 day, but the one on top of it is staying
    # for 11 -> the risk belongs to the one on top, since it's the one trapping the other
    score, flag = live_slot_risk(yard, "A", 1, 1, 2, long_dwell_above)
    assert flag == "HIGH"

    # the trapped container itself has nothing below it, so its own live risk is zero
    below_score, below_flag = live_slot_risk(yard, "A", 1, 1, 1, short_dwell_below)
    assert below_flag == "LOW"
