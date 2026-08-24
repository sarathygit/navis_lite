from app.models.schemas import LoadVesselRequest
from app.services.vessel_engine import load_container
from app.services.vessel_state import VesselState


def test_load_container_onto_open_slot_succeeds():
    vessel = VesselState()
    request = LoadVesselRequest(containerId="ABCD1234567", weightKg=15000, bay=1, row=1, tier=1)

    response = load_container(request, vessel)

    assert response.loaded is True
    assert response.bay == 1 and response.row == 1 and response.tier == 1
    assert response.total_deck_weight == 15000
    assert vessel.find_slot_by_container_id("ABCD1234567") == (1, 1, 1)


def test_load_container_onto_occupied_slot_is_rejected():
    vessel = VesselState()
    first = LoadVesselRequest(containerId="ABCD1234567", weightKg=15000, bay=1, row=1, tier=1)
    load_container(first, vessel)

    second = LoadVesselRequest(containerId="WXYZ7654321", weightKg=10000, bay=1, row=1, tier=1)
    response = load_container(second, vessel)

    assert response.loaded is False
    assert vessel.find_slot_by_container_id("WXYZ7654321") is None


def test_load_container_out_of_bounds_is_rejected():
    vessel = VesselState()
    request = LoadVesselRequest(containerId="ABCD1234567", weightKg=15000, bay=999, row=1, tier=1)

    response = load_container(request, vessel)

    assert response.loaded is False


def test_load_heavy_container_on_lower_deck_has_no_stability_warning():
    vessel = VesselState()
    request = LoadVesselRequest(containerId="ABCD1234567", weightKg=25000, bay=1, row=1, tier=1)

    response = load_container(request, vessel)

    assert response.loaded is True
    assert response.stability_warning is False


def test_load_heavy_container_on_upper_deck_triggers_stability_warning():
    vessel = VesselState()
    request = LoadVesselRequest(containerId="ABCD1234567", weightKg=25000, bay=1, row=1, tier=3)

    response = load_container(request, vessel)

    assert response.loaded is True
    assert response.stability_warning is True
    assert response.warning_message is not None


def test_load_light_container_on_upper_deck_has_no_stability_warning():
    vessel = VesselState()
    request = LoadVesselRequest(containerId="ABCD1234567", weightKg=5000, bay=1, row=1, tier=4)

    response = load_container(request, vessel)

    assert response.loaded is True
    assert response.stability_warning is False


def test_vessel_state_tracks_total_weight_across_multiple_placements():
    vessel = VesselState()
    load_container(LoadVesselRequest(containerId="ABCD1234567", weightKg=15000, bay=1, row=1, tier=1), vessel)
    load_container(LoadVesselRequest(containerId="WXYZ7654321", weightKg=10000, bay=2, row=1, tier=1), vessel)

    assert vessel.total_weight() == 25000


def test_upper_deck_heavy_violations_lists_only_heavy_upper_deck_containers():
    vessel = VesselState()
    load_container(LoadVesselRequest(containerId="ABCD1234567", weightKg=25000, bay=1, row=1, tier=1), vessel)  # heavy, lower deck
    load_container(LoadVesselRequest(containerId="WXYZ7654321", weightKg=5000, bay=2, row=1, tier=3), vessel)  # light, upper deck
    load_container(LoadVesselRequest(containerId="MSKU9070323", weightKg=22000, bay=3, row=1, tier=3), vessel)  # heavy, upper deck: violation

    violations = vessel.upper_deck_heavy_violations()

    assert len(violations) == 1
    _, _, _, occupant = violations[0]
    assert occupant.container_id == "MSKU9070323"
