from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DeckingRequest(BaseModel):
    container_id: str = Field(..., alias="containerId", min_length=11, max_length=11)
    weight_kg: float = Field(..., alias="weightKg", gt=0)
    reefer: bool
    destination: Optional[str] = None

    model_config = {"populate_by_name": True}


class DeckingResponse(BaseModel):
    block: Optional[str] = None
    row: Optional[int] = None
    bay: Optional[int] = None
    tier: Optional[int] = None
    dwell_time_estimate: Optional[float] = Field(None, alias="dwellTimeEstimate")
    shuffle_risk_score: Optional[float] = Field(None, alias="shuffleRiskScore")
    penalty_flag: Optional[str] = Field(None, alias="penaltyFlag")
    placed: bool
    reason: Optional[str] = None

    model_config = {"populate_by_name": True, "by_alias": True}


class ReleaseSlotRequest(BaseModel):
    container_id: str = Field(..., alias="containerId", min_length=11, max_length=11)

    model_config = {"populate_by_name": True}


class ReleaseSlotResponse(BaseModel):
    released: bool
    block: Optional[str] = None
    row: Optional[int] = None
    bay: Optional[int] = None
    tier: Optional[int] = None
    blocking_container_ids: list[str] = Field(default_factory=list, alias="blockingContainerIds")
    reason: Optional[str] = None

    model_config = {"populate_by_name": True, "by_alias": True}


class YardSlot(BaseModel):
    block: str
    row: int
    bay: int
    tier: int
    occupied: bool
    reefer: bool
    container_id: Optional[str] = Field(None, alias="containerId")
    weight_kg: Optional[float] = Field(None, alias="weightKg")
    dwell_time_estimate: Optional[float] = Field(None, alias="dwellTimeEstimate")
    placed_at: Optional[datetime] = Field(None, alias="placedAt")
    shuffle_risk_score: Optional[float] = Field(None, alias="shuffleRiskScore")
    penalty_flag: Optional[str] = Field(None, alias="penaltyFlag")

    model_config = {"populate_by_name": True, "by_alias": True}


class YardStateResponse(BaseModel):
    slots: list[YardSlot]


class EfficiencyIndexResponse(BaseModel):
    efficiency_index: float = Field(..., alias="efficiencyIndex")
    occupied_slots: int = Field(..., alias="occupiedSlots")

    model_config = {"populate_by_name": True, "by_alias": True}


class TelemetryReading(BaseModel):
    block: str
    row: int
    bay: int
    tier: int
    container_id: str = Field(..., alias="containerId")
    temperature_c: float = Field(..., alias="temperatureC")
    humidity_pct: float = Field(..., alias="humidityPct")
    powered: bool
    timestamp: datetime

    model_config = {"populate_by_name": True, "by_alias": True}


class Alert(BaseModel):
    id: int
    severity: str
    message: str
    block: str
    row: int
    bay: int
    tier: int
    container_id: str = Field(..., alias="containerId")
    timestamp: datetime

    model_config = {"populate_by_name": True, "by_alias": True}


class LoadVesselRequest(BaseModel):
    container_id: str = Field(..., alias="containerId", min_length=11, max_length=11)
    weight_kg: float = Field(..., alias="weightKg", gt=0)
    bay: int = Field(..., gt=0)
    row: int = Field(..., gt=0)
    tier: int = Field(..., gt=0)

    model_config = {"populate_by_name": True}


class LoadVesselResponse(BaseModel):
    loaded: bool
    bay: Optional[int] = None
    row: Optional[int] = None
    tier: Optional[int] = None
    stability_warning: bool = Field(False, alias="stabilityWarning")
    warning_message: Optional[str] = Field(None, alias="warningMessage")
    total_deck_weight: Optional[float] = Field(None, alias="totalDeckWeight")
    reason: Optional[str] = None

    model_config = {"populate_by_name": True, "by_alias": True}


class VesselSlot(BaseModel):
    bay: int
    row: int
    tier: int
    occupied: bool
    container_id: Optional[str] = Field(None, alias="containerId")
    weight_kg: Optional[float] = Field(None, alias="weightKg")
    placed_at: Optional[datetime] = Field(None, alias="placedAt")
    upper_deck: bool = Field(False, alias="upperDeck")

    model_config = {"populate_by_name": True, "by_alias": True}


class VesselStateResponse(BaseModel):
    slots: list[VesselSlot]


class VesselStabilityViolation(BaseModel):
    container_id: str = Field(..., alias="containerId")
    bay: int
    row: int
    tier: int
    weight_kg: float = Field(..., alias="weightKg")

    model_config = {"populate_by_name": True, "by_alias": True}


class VesselStabilityResponse(BaseModel):
    total_deck_weight: float = Field(..., alias="totalDeckWeight")
    violations: list[VesselStabilityViolation]

    model_config = {"populate_by_name": True, "by_alias": True}
