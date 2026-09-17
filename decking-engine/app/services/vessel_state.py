"""In-memory digital-twin vessel grid.

A single fixed docked vessel with a Bay x Row x Tier grid, separate from the
yard grid. Unlike the yard, there's no bottom-up physical fill requirement
here — an operator explicitly picks the bay/row/tier coordinate to load a
container onto (this mirrors real stowage planning, where a human plans the
bayplan rather than an algorithm filling slots bottom-up), so any open
coordinate can be targeted directly. The only constraint enforced here is
structural: a heavy container above the upper-deck threshold trips a
stability warning.
"""

import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.core.config import (
    HEAVY_WEIGHT_THRESHOLD_KG,
    VESSEL_BAYS,
    VESSEL_ROWS,
    VESSEL_TIERS,
    VESSEL_UPPER_DECK_MIN_TIER,
)


@dataclass
class VesselOccupant:
    container_id: str
    weight_kg: float
    placed_at: datetime


class VesselState:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        # occupancy[(bay, row, tier)] -> VesselOccupant
        self._occupancy: dict[tuple[int, int, int], VesselOccupant] = {}

    def lock(self) -> threading.RLock:
        return self._lock

    def in_bounds(self, bay: int, row: int, tier: int) -> bool:
        return 1 <= bay <= VESSEL_BAYS and 1 <= row <= VESSEL_ROWS and 1 <= tier <= VESSEL_TIERS

    def is_open(self, bay: int, row: int, tier: int) -> bool:
        return (bay, row, tier) not in self._occupancy

    def place(self, bay: int, row: int, tier: int, occupant: VesselOccupant) -> None:
        with self._lock:
            self._occupancy[(bay, row, tier)] = occupant

    def clear(self) -> None:
        with self._lock:
            self._occupancy.clear()

    def occupied_count(self) -> int:
        with self._lock:
            return len(self._occupancy)

    def find_slot_by_container_id(self, container_id: str) -> Optional[tuple[int, int, int]]:
        with self._lock:
            for coord, occupant in self._occupancy.items():
                if occupant.container_id == container_id:
                    return coord
        return None

    def all_slots(self):
        """Yields (bay, row, tier, occupant_or_None) for every addressable coordinate."""
        for bay in range(1, VESSEL_BAYS + 1):
            for row in range(1, VESSEL_ROWS + 1):
                for tier in range(1, VESSEL_TIERS + 1):
                    yield bay, row, tier, self._occupancy.get((bay, row, tier))

    def total_weight(self) -> float:
        with self._lock:
            return sum(occ.weight_kg for occ in self._occupancy.values())

    def upper_deck_heavy_violations(self) -> list[tuple[int, int, int, VesselOccupant]]:
        with self._lock:
            return [
                (bay, row, tier, occ)
                for (bay, row, tier), occ in self._occupancy.items()
                if tier >= VESSEL_UPPER_DECK_MIN_TIER and occ.weight_kg > HEAVY_WEIGHT_THRESHOLD_KG
            ]


vessel_state = VesselState()
