from typing import Any

from fastapi import APIRouter, Query

from app.core.config import VESSEL_UPPER_DECK_MIN_TIER
from app.models.schemas import (
    Alert,
    DeckingRequest,
    DeckingResponse,
    EfficiencyIndexResponse,
    LoadVesselRequest,
    LoadVesselResponse,
    ModelMetricsResponse,
    ReleaseSlotRequest,
    ReleaseSlotResponse,
    RestoreSlotRequest,
    RestoreSlotResponse,
    TelemetryReading,
    VesselSlot,
    VesselStabilityResponse,
    VesselStabilityViolation,
    VesselStateResponse,
    YardSlot,
    YardStateResponse,
)
from app.services.decking_engine import (
    find_best_slot,
    live_slot_risk,
    release_container,
    restore_container,
)
from app.services.ml_model import dwell_time_model
from app.services.state_sync import resync
from app.services.telemetry import telemetry_simulator
from app.services.vessel_engine import load_container
from app.services.vessel_state import vessel_state
from app.services.yard_state import yard_state

router = APIRouter(prefix="/api")


@router.post("/predict-decking", response_model=DeckingResponse, response_model_by_alias=True)
def predict_decking(request: DeckingRequest) -> DeckingResponse:
    return find_best_slot(request, yard_state)


@router.post("/release-slot", response_model=ReleaseSlotResponse, response_model_by_alias=True)
def release_slot(request: ReleaseSlotRequest) -> ReleaseSlotResponse:
    return release_container(request.container_id, yard_state)


@router.post("/restore-slot", response_model=RestoreSlotResponse, response_model_by_alias=True)
def restore_slot(request: RestoreSlotRequest) -> RestoreSlotResponse:
    """Undoes a release when the vessel refuses the container (see restore_container)."""
    return restore_container(request, yard_state)


@router.get("/yard", response_model=YardStateResponse, response_model_by_alias=True)
def get_yard_state() -> YardStateResponse:
    slots = []
    for block, row, bay, tier, occupant in yard_state.all_slots():
        risk_score, penalty_flag = (
            live_slot_risk(yard_state, block, row, bay, tier, occupant) if occupant else (None, None)
        )
        slots.append(
            YardSlot(
                block=block,
                row=row,
                bay=bay,
                tier=tier,
                occupied=occupant is not None,
                reefer=block == "R",
                container_id=occupant.container_id if occupant else None,
                weight_kg=occupant.weight_kg if occupant else None,
                dwell_time_estimate=occupant.dwell_time_estimate if occupant else None,
                placed_at=occupant.placed_at if occupant else None,
                shuffle_risk_score=risk_score,
                penalty_flag=penalty_flag,
            )
        )
    return YardStateResponse(slots=slots)


@router.get("/yard/efficiency-index", response_model=EfficiencyIndexResponse, response_model_by_alias=True)
def get_efficiency_index() -> EfficiencyIndexResponse:
    risk_scores = []
    for block, row, bay, tier, occupant in yard_state.all_slots():
        if occupant is None:
            continue
        risk_score, _ = live_slot_risk(yard_state, block, row, bay, tier, occupant)
        risk_scores.append(risk_score)

    avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
    return EfficiencyIndexResponse(
        efficiency_index=round(100.0 - avg_risk, 1),
        occupied_slots=len(risk_scores),
    )


@router.get("/telemetry", response_model=list[TelemetryReading], response_model_by_alias=True)
def get_telemetry() -> list[TelemetryReading]:
    return telemetry_simulator.get_readings()


@router.get("/alerts", response_model=list[Alert], response_model_by_alias=True)
def get_alerts(since_id: int = Query(0, alias="sinceId")) -> list[Alert]:
    return telemetry_simulator.get_alerts(since_id=since_id)


@router.post("/vessel/load", response_model=LoadVesselResponse, response_model_by_alias=True)
def load_to_vessel(request: LoadVesselRequest) -> LoadVesselResponse:
    return load_container(request, vessel_state)


@router.get("/vessel", response_model=VesselStateResponse, response_model_by_alias=True)
def get_vessel_state() -> VesselStateResponse:
    slots = [
        VesselSlot(
            bay=bay,
            row=row,
            tier=tier,
            occupied=occupant is not None,
            container_id=occupant.container_id if occupant else None,
            weight_kg=occupant.weight_kg if occupant else None,
            placed_at=occupant.placed_at if occupant else None,
            upper_deck=tier >= VESSEL_UPPER_DECK_MIN_TIER,
        )
        for bay, row, tier, occupant in vessel_state.all_slots()
    ]
    return VesselStateResponse(slots=slots)


@router.get("/vessel/stability", response_model=VesselStabilityResponse, response_model_by_alias=True)
def get_vessel_stability() -> VesselStabilityResponse:
    violations = [
        VesselStabilityViolation(container_id=occ.container_id, bay=bay, row=row, tier=tier, weight_kg=occ.weight_kg)
        for bay, row, tier, occ in vessel_state.upper_deck_heavy_violations()
    ]
    return VesselStabilityResponse(total_deck_weight=vessel_state.total_weight(), violations=violations)


@router.get("/model/metrics", response_model=ModelMetricsResponse, response_model_by_alias=True)
def get_model_metrics() -> ModelMetricsResponse:
    return ModelMetricsResponse(**dwell_time_model.get_metrics())


@router.post("/model/retrain", response_model=ModelMetricsResponse, response_model_by_alias=True)
def retrain_model() -> ModelMetricsResponse:
    """Rebuilds the dwell model from current gate history.

    Exposed because a freshly started terminal has no history to learn from —
    once real check-in/check-out cycles have accumulated, this promotes the
    model off the synthetic corpus without a restart.
    """
    return ModelMetricsResponse(**dwell_time_model.retrain_from_history())


@router.post("/state/resync")
def resync_state() -> dict[str, Any]:
    """Rebuilds the yard and vessel grids from the gateway's ledger.

    The grids are in-memory, so this is what makes a restart survivable: the
    ledger is the single source of truth and these grids are a view of it.
    Runs automatically at start-up; exposed here for manual recovery.
    """
    return resync()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "OK"}
