"""In-memory digital-twin yard grid.

Each addressable coordinate is (block, row, bay, tier). Stacks fill bottom-up:
a tier may only be occupied once every tier below it in the same (block, row, bay)
stack is occupied. This is what gives the weight-tier policy physical meaning —
heavy containers form the structural base a lighter container can be stacked on.

The yard starts empty. Every occupied slot corresponds to a real container that
came through /api/predict-decking, so this state always agrees with the
gateway-service ledger (the ledger is the durable record; this is its live
mirror). A light container checked into a fresh yard will be rejected until
enough heavy containers have arrived to form a structural base — that's the
weight-tier rule working as intended, not a bug.
"""

import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.core.config import (
    MAX_TIER,
    REEFER_BLOCK,
    REEFER_BLOCK_BAYS,
    REEFER_BLOCK_ROWS,
    STANDARD_BLOCK_BAYS,
    STANDARD_BLOCK_ROWS,
    STANDARD_BLOCKS,
)


@dataclass
class SlotOccupant:
    container_id: str
    weight_kg: float
    reefer: bool
    dwell_time_estimate: float
    placed_at: datetime


class YardState:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        # occupancy[(block, row, bay, tier)] -> SlotOccupant
        self._occupancy: dict[tuple[str, int, int, int], SlotOccupant] = {}
        self._stack_dims: dict[str, tuple[int, int]] = {
            **{b: (STANDARD_BLOCK_ROWS, STANDARD_BLOCK_BAYS) for b in STANDARD_BLOCKS},
            REEFER_BLOCK: (REEFER_BLOCK_ROWS, REEFER_BLOCK_BAYS),
        }

    def blocks(self) -> dict[str, tuple[int, int]]:
        return dict(self._stack_dims)

    def next_open_tier(self, block: str, row: int, bay: int) -> Optional[int]:
        """Lowest unoccupied tier in this stack, or None if the stack is full."""
        for tier in range(1, MAX_TIER + 1):
            if (block, row, bay, tier) not in self._occupancy:
                return tier
        return None

    def occupant_below(self, block: str, row: int, bay: int, tier: int) -> Optional[SlotOccupant]:
        if tier <= 1:
            return None
        return self._occupancy.get((block, row, bay, tier - 1))

    def find_slot_by_container_id(self, container_id: str) -> Optional[tuple[str, int, int, int]]:
        with self._lock:
            for coord, occupant in self._occupancy.items():
                if occupant.container_id == container_id:
                    return coord
        return None

    def occupants_above(self, block: str, row: int, bay: int, tier: int) -> list[SlotOccupant]:
        """Occupants stacked on top of this tier, bottom-most first. Bottom-up
        fill means these are contiguous, so this call must physically clear
        top-down before the container at `tier` can be pulled."""
        with self._lock:
            above = []
            for t in range(tier + 1, MAX_TIER + 1):
                occupant = self._occupancy.get((block, row, bay, t))
                if occupant is None:
                    break
                above.append(occupant)
            return above

    def release(self, block: str, row: int, bay: int, tier: int) -> Optional[SlotOccupant]:
        with self._lock:
            return self._occupancy.pop((block, row, bay, tier), None)

    def is_open(self, block: str, row: int, bay: int, tier: int) -> bool:
        with self._lock:
            return (block, row, bay, tier) not in self._occupancy

    def clear(self) -> None:
        with self._lock:
            self._occupancy.clear()

    def occupied_count(self) -> int:
        with self._lock:
            return len(self._occupancy)

    def candidate_stacks(self, block: str):
        rows, bays = self._stack_dims[block]
        for row in range(1, rows + 1):
            for bay in range(1, bays + 1):
                yield row, bay

    def place(self, block: str, row: int, bay: int, tier: int, occupant: SlotOccupant) -> None:
        with self._lock:
            self._occupancy[(block, row, bay, tier)] = occupant

    def lock(self) -> threading.RLock:
        return self._lock

    def all_slots(self):
        """Yields (block, row, bay, tier, occupant_or_None) for every addressable coordinate."""
        for block, (rows, bays) in self._stack_dims.items():
            for row in range(1, rows + 1):
                for bay in range(1, bays + 1):
                    for tier in range(1, MAX_TIER + 1):
                        yield block, row, bay, tier, self._occupancy.get((block, row, bay, tier))

    def occupied_reefer_slots(self):
        with self._lock:
            return [
                (block, row, bay, tier, occ)
                for (block, row, bay, tier), occ in self._occupancy.items()
                if block == REEFER_BLOCK
            ]


yard_state = YardState()
