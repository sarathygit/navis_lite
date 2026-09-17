"""Rebuilds the yard and vessel grids from the gateway's transaction ledger.

The grids live in this process's memory, which means a restart would otherwise
lose them while MySQL still holds every container and its coordinates — leaving
the ledger claiming a container sits at R-01-01 while the yard map shows the
slot empty.

Rather than give the engine a second place to persist state, the ledger is
treated as the single source of truth and the grids are rebuilt from it. That
keeps exactly one authority over where a container is, and makes a restart
self-healing instead of destructive.

Runs at start-up, and can be re-triggered at any time via POST /api/state/resync.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from app.core.config import GATEWAY_TIMEOUT_SECONDS, GATEWAY_URL
from app.services.vessel_state import VesselOccupant, VesselState, vessel_state
from app.services.yard_state import SlotOccupant, YardState, yard_state

logger = logging.getLogger(__name__)


def fetch_ledger(timeout: float = GATEWAY_TIMEOUT_SECONDS) -> Optional[list[dict[str, Any]]]:
    """Reads the durable transaction ledger from the gateway.

    Returns None when the ledger could not be read at all — deliberately
    distinct from an empty list, which means "the ledger really is empty".
    Conflating the two would let an unreachable gateway wipe a populated yard.
    """
    url = f"{GATEWAY_URL}/api/gate/transactions"
    try:
        response = httpx.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.warning("Could not read ledger from %s: %s", url, exc)
        return None


def _parse_timestamp(value: Optional[str]) -> datetime:
    """Always returns an aware UTC datetime.

    The gateway serialises LocalDateTime without an offset, so parsing gives a
    naive value while everything placed live is aware. Mixing the two raises
    TypeError on the first subtraction, so the boundary is normalised here.
    """
    if value:
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            parsed = None
        if parsed is not None:
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
    return datetime.now(timezone.utc)


def restore_yard(records: list[dict[str, Any]], yard: YardState) -> dict[str, Any]:
    """Re-places every container the ledger still considers to be in the yard."""
    report = {"restored": 0, "skipped_incomplete": 0, "skipped_conflict": 0}

    yard.clear()
    for tx in records:
        if tx.get("status") != "DECKED":
            continue

        block, row = tx.get("assignedBlock"), tx.get("assignedRow")
        bay, tier = tx.get("assignedBay"), tx.get("assignedTier")

        # A DECKED row without a full coordinate cannot be placed. This happens
        # for containers decked before row/bay were recorded on the ledger.
        if None in (block, row, bay, tier):
            report["skipped_incomplete"] += 1
            continue

        if not yard.is_open(block, row, bay, tier):
            report["skipped_conflict"] += 1
            continue

        yard.place(
            block, row, bay, tier,
            SlotOccupant(
                container_id=tx["containerId"],
                weight_kg=float(tx["weightKg"]),
                reefer=bool(tx["reefer"]),
                dwell_time_estimate=float(tx.get("dwellTimeEstimate") or 0.0),
                placed_at=_parse_timestamp(tx.get("checkInTime")),
            ),
        )
        report["restored"] += 1

    return report


def restore_vessel(records: list[dict[str, Any]], vessel: VesselState) -> dict[str, Any]:
    """Re-places every container the ledger still considers loaded on the vessel."""
    report = {"restored": 0, "skipped_incomplete": 0, "skipped_conflict": 0}

    vessel.clear()
    for tx in records:
        if tx.get("status") != "LOADED":
            continue

        bay, row, tier = tx.get("vesselBay"), tx.get("vesselRow"), tx.get("vesselTier")
        if None in (bay, row, tier):
            report["skipped_incomplete"] += 1
            continue

        if not vessel.in_bounds(bay, row, tier) or not vessel.is_open(bay, row, tier):
            report["skipped_conflict"] += 1
            continue

        vessel.place(
            bay, row, tier,
            VesselOccupant(
                container_id=tx["containerId"],
                weight_kg=float(tx["weightKg"]),
                placed_at=_parse_timestamp(tx.get("checkInTime")),
            ),
        )
        report["restored"] += 1

    return report


def resync() -> dict[str, Any]:
    """Rebuilds both grids to match the ledger. Safe to call repeatedly."""
    records = fetch_ledger()

    if records is None:
        # The ledger is the source of truth; without it there is nothing to
        # rebuild from. Leave the grids exactly as they are rather than
        # clearing them on the strength of a failed request.
        logger.warning("Skipping resync: ledger unavailable, keeping current grid state")
        return {
            "skipped": True,
            "reason": "ledger unavailable",
            "yard_occupied": yard_state.occupied_count(),
            "vessel_occupied": vessel_state.occupied_count(),
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }

    # Clear and refill under the lock so no request ever observes the
    # momentarily-empty grid between the two steps.
    with yard_state.lock(), vessel_state.lock():
        yard_report = restore_yard(records, yard_state)
        vessel_report = restore_vessel(records, vessel_state)

    summary = {
        "ledger_records": len(records),
        "yard": yard_report,
        "vessel": vessel_report,
        "yard_occupied": yard_state.occupied_count(),
        "vessel_occupied": vessel_state.occupied_count(),
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "State resync: %s yard slots and %s vessel slots restored from %s ledger records",
        yard_report["restored"], vessel_report["restored"], len(records),
    )
    return summary
