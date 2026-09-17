from app.services.state_sync import restore_vessel, restore_yard
from app.services.vessel_state import VesselState
from app.services.yard_state import SlotOccupant, YardState


def decked(container_id="ABCD1234567", block="A", row=1, bay=1, tier=1, weight=25000.0, reefer=False):
    return {
        "containerId": container_id,
        "weightKg": weight,
        "reefer": reefer,
        "status": "DECKED",
        "assignedBlock": block,
        "assignedRow": row,
        "assignedBay": bay,
        "assignedTier": tier,
        "dwellTimeEstimate": 4.2,
        "checkInTime": "2026-01-01T00:00:00",
    }


def loaded(container_id="WXYZ7654321", bay=1, row=1, tier=1, weight=25000.0):
    return {
        "containerId": container_id,
        "weightKg": weight,
        "reefer": False,
        "status": "LOADED",
        "vesselBay": bay,
        "vesselRow": row,
        "vesselTier": tier,
        "checkInTime": "2026-01-01T00:00:00",
    }


# ---------- yard ----------

def test_restore_puts_decked_containers_back_at_their_recorded_coordinates():
    yard = YardState()
    report = restore_yard([decked("ABCD1234567", "R", 1, 1, 2)], yard)

    assert report["restored"] == 1
    assert yard.find_slot_by_container_id("ABCD1234567") == ("R", 1, 1, 2)


def test_restore_preserves_weight_reefer_and_dwell_so_risk_scoring_still_works():
    yard = YardState()
    restore_yard([decked("ABCD1234567", "R", 1, 1, 1, weight=26000.0, reefer=True)], yard)

    occupant = yard.occupant_below("R", 1, 1, 2)
    assert occupant.weight_kg == 26000.0
    assert occupant.reefer is True
    assert occupant.dwell_time_estimate == 4.2


def test_restore_ignores_containers_that_already_left():
    yard = YardState()
    records = [
        decked("AAAA1111111"),
        {**decked("BBBB2222222", bay=2), "status": "DEPARTED"},
        {**decked("CCCC3333333", bay=3), "status": "REJECTED"},
        {**decked("DDDD4444444", bay=4), "status": "LOADED"},
    ]
    report = restore_yard(records, yard)

    assert report["restored"] == 1
    assert yard.occupied_count() == 1


def test_restore_skips_decked_rows_missing_a_full_coordinate():
    """Rows decked before row/bay were recorded cannot be placed."""
    yard = YardState()
    incomplete = {**decked("ABCD1234567"), "assignedRow": None, "assignedBay": None}
    report = restore_yard([incomplete], yard)

    assert report["skipped_incomplete"] == 1
    assert yard.occupied_count() == 0


def test_restore_skips_a_second_container_claiming_the_same_slot():
    yard = YardState()
    records = [decked("AAAA1111111", "A", 1, 1, 1), decked("BBBB2222222", "A", 1, 1, 1)]
    report = restore_yard(records, yard)

    assert report["restored"] == 1
    assert report["skipped_conflict"] == 1


def test_restore_is_idempotent_and_clears_stale_state_first():
    yard = YardState()
    records = [decked("AAAA1111111", "A", 1, 1, 1)]

    restore_yard(records, yard)
    restore_yard(records, yard)
    assert yard.occupied_count() == 1

    # a container that has since departed disappears on the next sync
    restore_yard([], yard)
    assert yard.occupied_count() == 0


def test_restored_yard_supports_normal_operations():
    """The rebuilt grid must behave exactly like one built by live check-ins —
    a restored container still blocks the slot and can still be released."""
    from app.services.decking_engine import release_container

    yard = YardState()
    restore_yard([decked("ABCD1234567", "A", 1, 1, 1)], yard)

    assert yard.is_open("A", 1, 1, 1) is False
    assert release_container("ABCD1234567", yard).released is True
    assert yard.occupied_count() == 0


# ---------- vessel ----------

def test_restore_puts_loaded_containers_back_on_the_vessel():
    vessel = VesselState()
    report = restore_vessel([loaded("WXYZ7654321", 2, 1, 3)], vessel)

    assert report["restored"] == 1
    assert vessel.find_slot_by_container_id("WXYZ7654321") == (2, 1, 3)


def test_restored_vessel_recomputes_stability_violations():
    vessel = VesselState()
    restore_vessel([loaded("WXYZ7654321", 1, 1, 3, weight=26000.0)], vessel)

    violations = vessel.upper_deck_heavy_violations()
    assert len(violations) == 1
    assert vessel.total_weight() == 26000.0


def test_restore_vessel_skips_out_of_bounds_coordinates():
    vessel = VesselState()
    report = restore_vessel([loaded("WXYZ7654321", 999, 1, 1)], vessel)

    assert report["skipped_conflict"] == 1
    assert vessel.occupied_count() == 0


def test_an_unreachable_ledger_must_not_wipe_a_populated_yard(monkeypatch):
    """Regression: resync used to clear the grids before fetching, so a gateway
    that was merely unreachable would silently empty a full yard."""
    import app.services.state_sync as sync
    from app.services.yard_state import yard_state

    yard_state.clear()
    yard_state.place("A", 1, 1, 1, SlotOccupant(
        "KEEP0000001", 25000.0, False, 5.0, __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc)))

    monkeypatch.setattr(sync, "fetch_ledger", lambda *a, **k: None)
    result = sync.resync()

    assert result["skipped"] is True
    assert yard_state.occupied_count() == 1, "grid must survive an unreadable ledger"
    yard_state.clear()


def test_an_empty_ledger_does_clear_the_yard(monkeypatch):
    """An empty ledger is real information — everything left — unlike a failure."""
    import app.services.state_sync as sync
    from app.services.yard_state import yard_state

    yard_state.clear()
    yard_state.place("A", 1, 1, 1, SlotOccupant(
        "GONE0000001", 25000.0, False, 5.0, __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc)))

    monkeypatch.setattr(sync, "fetch_ledger", lambda *a, **k: [])
    sync.resync()

    assert yard_state.occupied_count() == 0


def test_restored_timestamps_are_timezone_aware(monkeypatch):
    """Regression: the gateway serialises LocalDateTime with no offset, so a
    restored container carried a naive placed_at while live placements are
    aware. The first subtraction between them raised TypeError and took down
    every placement request after a resync."""
    from datetime import timezone

    yard = YardState()
    restore_yard([decked("ABCD1234567", "A", 1, 1, 1)], yard)

    occupant = yard.occupant_below("A", 1, 1, 2)
    assert occupant.placed_at.tzinfo is not None
    assert occupant.placed_at.utcoffset() == timezone.utc.utcoffset(None)


def test_relocation_search_survives_a_restored_yard():
    """The end-to-end shape of the bug above: rebuild from the ledger, then ask
    for a suggestion. This must not raise."""
    from app.models.schemas import DeckingRequest
    from app.services.decking_engine import find_best_slot

    yard = YardState()
    records = []
    for block in ("A", "B", "C"):
        for row, bay in yard.candidate_stacks(block):
            records.append(decked(f"L{block}{row}{bay}".ljust(11, "0")[:11], block, row, bay, 1, weight=5000.0))
    restore_yard(records, yard)

    response = find_best_slot(DeckingRequest(containerId="HVYA0000001", weightKg=26_000, reefer=False), yard)
    assert response.placed is False
    assert response.suggestion is not None
