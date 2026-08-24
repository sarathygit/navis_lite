"""Vessel stowage planning: loading yard containers onto the docked vessel's
bayplan, with a structural stability check on every placement.
"""

from datetime import datetime, timezone

from app.core.config import HEAVY_WEIGHT_THRESHOLD_KG, VESSEL_UPPER_DECK_MIN_TIER
from app.models.schemas import LoadVesselRequest, LoadVesselResponse
from app.services.vessel_state import VesselOccupant, VesselState


def load_container(request: LoadVesselRequest, vessel: VesselState) -> LoadVesselResponse:
    with vessel.lock():
        if not vessel.in_bounds(request.bay, request.row, request.tier):
            return LoadVesselResponse(
                loaded=False,
                reason=f"Bay {request.bay} row {request.row} tier {request.tier} is outside the vessel's grid",
            )

        if not vessel.is_open(request.bay, request.row, request.tier):
            return LoadVesselResponse(
                loaded=False,
                reason=f"Vessel slot bay={request.bay} row={request.row} tier={request.tier} is already occupied",
            )

        occupant = VesselOccupant(
            container_id=request.container_id,
            weight_kg=request.weight_kg,
            placed_at=datetime.now(timezone.utc),
        )
        vessel.place(request.bay, request.row, request.tier, occupant)

        stability_warning = (
            request.tier >= VESSEL_UPPER_DECK_MIN_TIER and request.weight_kg > HEAVY_WEIGHT_THRESHOLD_KG
        )
        warning_message = (
            f"Container {request.container_id} ({request.weight_kg:.0f} kg) is on upper deck "
            f"tier {request.tier}, above the {HEAVY_WEIGHT_THRESHOLD_KG:.0f} kg stability threshold"
            if stability_warning
            else None
        )

        return LoadVesselResponse(
            loaded=True,
            bay=request.bay,
            row=request.row,
            tier=request.tier,
            stability_warning=stability_warning,
            warning_message=warning_message,
            total_deck_weight=vessel.total_weight(),
            reason=f"Loaded {request.container_id} at bay={request.bay} row={request.row} tier={request.tier}",
        )
