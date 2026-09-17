from datetime import datetime, timezone

from app.models.schemas import DeckingRequest
from app.services.decking_engine import (
    can_stack_on,
    compute_shuffle_risk,
    eligible_blocks,
    find_best_slot,
    live_slot_risk,
    normalize_penalty,
    release_container,
)
from app.services.yard_state import SlotOccupant, YardState





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


# ---------- stacking-compatibility rule ----------

def occ(cid, weight, dwell=5.0, reefer=False, age_days=0.0):
    from datetime import timedelta
    return SlotOccupant(cid, weight, reefer, dwell_time_estimate=dwell,
                        placed_at=datetime.now(timezone.utc) - timedelta(days=age_days))


def test_anything_may_rest_on_an_empty_ground_slot():
    assert can_stack_on(5_000, None) is True
    assert can_stack_on(30_000, None) is True


def test_a_container_may_sit_on_a_heavier_one():
    assert can_stack_on(5_000, occ("X", 25_000)) is True


def test_equal_weights_may_stack():
    assert can_stack_on(20_000, occ("X", 20_000)) is True


def test_a_heavier_container_may_not_sit_on_a_lighter_one():
    assert can_stack_on(25_000, occ("X", 5_000)) is False


def test_light_container_is_placed_on_the_ground_of_an_empty_yard():
    """The old tier rule turned this truck away. A real terminal just puts the
    box down — tier 1 is the ground and accepts anything."""
    yard = YardState()
    response = find_best_slot(DeckingRequest(containerId="LGHT0000001", weightKg=6_200, reefer=False), yard)

    assert response.placed is True
    assert response.tier == 1


def test_heavy_container_is_never_stacked_on_a_lighter_one():
    yard = YardState()
    # fill every dry ground slot with light cargo
    for block in ("A", "B", "C"):
        for row, bay in yard.candidate_stacks(block):
            yard.place(block, row, bay, 1, occ(f"L{block}{row}{bay}".ljust(11, "0")[:11], 5_000))

    response = find_best_slot(DeckingRequest(containerId="HVYA0000001", weightKg=26_000, reefer=False), yard)

    assert response.placed is False, "26t must not be stacked on 5t"


# ---------- relocation suggestion ----------

def test_rejection_suggests_a_relocation_that_actually_frees_a_slot():
    yard = YardState()
    for block in ("A", "B", "C"):
        for row, bay in yard.candidate_stacks(block):
            yard.place(block, row, bay, 1, occ(f"L{block}{row}{bay}".ljust(11, "0")[:11], 5_000))

    response = find_best_slot(DeckingRequest(containerId="HVYA0000001", weightKg=26_000, reefer=False), yard)

    assert response.placed is False
    s = response.suggestion
    assert s is not None, "a relocation exists, so one must be proposed"
    # the freed slot is where the arriving container goes
    assert (s.then_place_at_block, s.then_place_at_row, s.then_place_at_bay, s.then_place_at_tier) == \
           (s.from_block, s.from_row, s.from_bay, s.from_tier)
    # and the destination is a different stack entirely (see the test below)
    assert (s.to_block, s.to_row, s.to_bay) != (s.from_block, s.from_row, s.from_bay)


def test_suggestion_never_moves_a_container_within_its_own_stack():
    """Regression: the search excluded only the slot being vacated, so the slot
    directly above it still looked open and got proposed as the destination —
    telling the crane to lift a container and set it back down on top of itself.
    That slot is only open while the container is still there holding it up."""
    yard = YardState()
    for block in ("A", "B", "C"):
        for row, bay in yard.candidate_stacks(block):
            yard.place(block, row, bay, 1, occ(f"L{block}{row}{bay}".ljust(11, "0")[:11], 5_000))

    response = find_best_slot(DeckingRequest(containerId="HVYA0000001", weightKg=26_000, reefer=False), yard)

    s = response.suggestion
    assert s is not None
    assert (s.from_block, s.from_row, s.from_bay) != (s.to_block, s.to_row, s.to_bay), \
        "a container cannot be relocated within the stack it is being lifted off"


def test_suggestion_never_proposes_moving_a_buried_container():
    yard = YardState()
    for block in ("A", "B", "C"):
        for row, bay in yard.candidate_stacks(block):
            yard.place(block, row, bay, 1, occ(f"L{block}{row}{bay}".ljust(11, "0")[:11], 5_000))
    # bury one of them
    yard.place("A", 1, 1, 2, occ("TOPC0000001", 4_000))

    response = find_best_slot(DeckingRequest(containerId="HVYA0000001", weightKg=26_000, reefer=False), yard)

    if response.suggestion:
        assert response.suggestion.move_container_id != "LA11000000"[:11], "buried container is not liftable"


def test_suggestion_avoids_disturbing_an_imminent_departure_when_alternatives_tie():
    """Relocating a container that leaves in hours is wasted crane work.

    The urgency penalty is a tiebreaker, not an override: it is capped at
    RELOCATION_URGENCY_HORIZON_DAYS while shuffle risk is weighted x10, so it
    decides between destinations that are otherwise equally good. This sets all
    the shuffle risks equal so urgency is what is actually under test.
    """
    yard = YardState()
    for block in ("A", "B", "C"):
        for row, bay in yard.candidate_stacks(block):
            # long dwell everywhere, so every destination scores zero shuffle risk
            yard.place(block, row, bay, 1, occ(f"L{block}{row}{bay}".ljust(11, "0")[:11], 5_000, dwell=30.0))
    # one container is about to leave; moving it would be the wasted move
    yard.place("B", 2, 2, 1, occ("IMMINENT001", 5_000, dwell=0.05))

    response = find_best_slot(DeckingRequest(containerId="HVYA0000001", weightKg=26_000, reefer=False), yard)

    assert response.suggestion is not None
    assert response.suggestion.move_container_id != "IMMINENT001"


def test_no_suggestion_when_the_yard_is_genuinely_full():
    yard = YardState()
    for block in ("A", "B", "C"):
        for row, bay in yard.candidate_stacks(block):
            for tier in range(1, 6):
                yard.place(block, row, bay, tier, occ(f"F{block}{row}{bay}{tier}".ljust(11, "0")[:11], 30_000))

    response = find_best_slot(DeckingRequest(containerId="HVYA0000001", weightKg=26_000, reefer=False), yard)

    assert response.placed is False
    assert response.suggestion is None, "no move helps when every slot is taken"
