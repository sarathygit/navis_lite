"""Training-data acquisition and wrangling for the dwell-time model.

Pulls raw gate-transaction history from the Java gateway and turns it into a
clean, modelling-ready frame. The gateway deliberately hands over unfiltered
records — including containers still sitting in the yard and containers that
never received a slot — so every cleaning decision is made here, explicitly,
where it can be tested and reasoned about.

The one that matters most is right-censoring. A container still in the yard has
no departure time: we know its dwell is *at least* (now - check_in), but not what
it will actually be. Those observations are excluded from the target, because
treating a lower bound as a completed value would drag every prediction
downward. Excluding them is not free either — it biases the sample toward cargo
that leaves quickly (survivorship bias) — so the censoring rate is measured and
reported rather than hidden, and a high rate is surfaced in the model metrics.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
import numpy as np
import pandas as pd

from app.core.config import (
    GATEWAY_TIMEOUT_SECONDS,
    GATEWAY_URL,
    HEAVY_WEIGHT_THRESHOLD_KG,
    MAX_PLAUSIBLE_DWELL_DAYS,
    MIN_TRAINING_ROWS,
)

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = ["weight_kg", "reefer", "tier", "is_heavy"]
TARGET_COLUMN = "dwell_days"


def fetch_raw_history(timeout: float = GATEWAY_TIMEOUT_SECONDS) -> list[dict[str, Any]]:
    """Retrieves raw transaction records from the gateway.

    Returns an empty list rather than raising if the gateway is unreachable —
    at container start-up the gateway may not be listening yet, and the caller
    is expected to fall back to synthetic data in that case.
    """
    url = f"{GATEWAY_URL}/api/gate/training-data"
    try:
        response = httpx.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.warning("Could not fetch training history from %s: %s", url, exc)
        return []


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def wrangle(raw_records: list[dict[str, Any]]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Cleans raw transaction records into a modelling frame.

    Returns the frame plus a provenance report describing exactly what was
    dropped and why, so the cleaning is auditable instead of implicit.
    """
    report: dict[str, Any] = {
        "raw_records": len(raw_records),
        "dropped_no_slot": 0,
        "censored_still_in_yard": 0,
        "dropped_bad_timestamps": 0,
        "dropped_implausible_dwell": 0,
        "usable_rows": 0,
        "censoring_rate": 0.0,
    }

    if not raw_records:
        return pd.DataFrame(columns=FEATURE_COLUMNS + [TARGET_COLUMN]), report

    frame = pd.DataFrame(raw_records)

    # 1. A container that never received a slot (REJECTED at the gate, or HELD
    #    before decking) has no placement to learn from.
    has_slot = frame["assignedTier"].notna()
    report["dropped_no_slot"] = int((~has_slot).sum())
    frame = frame[has_slot]

    if frame.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS + [TARGET_COLUMN]), report

    # 2. Right-censored observations: still in the yard, so the true dwell is
    #    unknown. Counted, then excluded from the target.
    completed = frame["departureTime"].notna()
    report["censored_still_in_yard"] = int((~completed).sum())
    placed_rows = len(frame)
    report["censoring_rate"] = round(float((~completed).sum()) / placed_rows, 3) if placed_rows else 0.0
    frame = frame[completed]

    if frame.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS + [TARGET_COLUMN]), report

    # 3. Derive the observed dwell from the two timestamps.
    check_in = frame["checkInTime"].map(_parse_timestamp)
    departure = frame["departureTime"].map(_parse_timestamp)

    parseable = check_in.notna() & departure.notna()
    report["dropped_bad_timestamps"] = int((~parseable).sum())
    frame = frame[parseable]
    check_in = check_in[parseable]
    departure = departure[parseable]

    if frame.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS + [TARGET_COLUMN]), report

    dwell_days = (departure - check_in).map(lambda d: d.total_seconds() / 86_400.0)

    # 4. Guard against clock skew and absurd values. A non-positive dwell is
    #    impossible; an enormous one is a data fault, not a signal.
    plausible = (dwell_days > 0) & (dwell_days <= MAX_PLAUSIBLE_DWELL_DAYS)
    report["dropped_implausible_dwell"] = int((~plausible).sum())
    frame = frame[plausible]
    dwell_days = dwell_days[plausible]

    if frame.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS + [TARGET_COLUMN]), report

    # 5. Feature engineering. `is_heavy` encodes the terminal's structural
    #    weight threshold explicitly, so the model does not have to rediscover
    #    a boundary the business already defines.
    clean = pd.DataFrame(
        {
            "weight_kg": frame["weightKg"].astype(float).to_numpy(),
            "reefer": frame["reefer"].astype(bool).astype(int).to_numpy(),
            "tier": frame["assignedTier"].astype(int).to_numpy(),
            "dwell_days": dwell_days.astype(float).to_numpy(),
        }
    )
    clean["is_heavy"] = (clean["weight_kg"] > HEAVY_WEIGHT_THRESHOLD_KG).astype(int)

    report["usable_rows"] = len(clean)
    return clean[FEATURE_COLUMNS + [TARGET_COLUMN]], report


def generate_synthetic_training_data(n_samples: int = 2000, seed: int = 7) -> pd.DataFrame:
    """Fallback corpus for a terminal with no operating history yet.

    The relationships encoded here are domain assumptions, not observations:
    heavier cargo dwells longer, reefers are time-sensitive and move faster,
    upper tiers are easier to reach and clear sooner. Any model trained on this
    is reproducing those assumptions — which is exactly why real history is
    preferred the moment enough of it exists.
    """
    rng = np.random.default_rng(seed)

    weight_kg = rng.uniform(1_000, 32_000, n_samples)
    reefer = rng.integers(0, 2, n_samples)
    tier = rng.integers(1, 6, n_samples)

    base_dwell = 3.0
    weight_effect = weight_kg / 12_000.0
    reefer_effect = np.where(reefer == 1, -1.2, 0.0)
    tier_effect = -0.15 * tier
    noise = rng.normal(0, 1.0, n_samples)

    dwell_days = np.clip(base_dwell + weight_effect + reefer_effect + tier_effect + noise, 0.5, 30.0)

    frame = pd.DataFrame(
        {
            "weight_kg": weight_kg,
            "reefer": reefer,
            "tier": tier,
            "dwell_days": dwell_days,
        }
    )
    frame["is_heavy"] = (frame["weight_kg"] > HEAVY_WEIGHT_THRESHOLD_KG).astype(int)
    return frame[FEATURE_COLUMNS + [TARGET_COLUMN]]


def load_training_data() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Returns the best available training corpus and its provenance.

    Prefers real operating history; falls back to synthetic when the terminal
    has not yet accumulated enough completed moves to learn from.
    """
    raw = fetch_raw_history()
    real_frame, report = wrangle(raw)

    if len(real_frame) >= MIN_TRAINING_ROWS:
        report["source"] = "history"
        report["min_rows_required"] = MIN_TRAINING_ROWS
        return real_frame, report

    report["source"] = "synthetic"
    report["min_rows_required"] = MIN_TRAINING_ROWS
    report["fallback_reason"] = (
        f"only {len(real_frame)} usable historical rows, need {MIN_TRAINING_ROWS}"
    )
    return generate_synthetic_training_data(), report
