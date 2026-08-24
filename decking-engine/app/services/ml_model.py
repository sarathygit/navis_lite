"""Dwell-time prediction model for the Expert Decking Engine.

There is no historical terminal dataset to train on for this MVP, so a
RandomForestRegressor is fit once at process start against a synthetic but
domain-plausible dataset (reefer cargo tends to move faster/time-sensitive;
heavier cargo tends to dwell longer; upper tiers see slightly faster pulls
since they're easier to access). The trained estimator is then used to score
every candidate slot returned by the decking algorithm.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

_FEATURE_COLUMNS = ["weight_kg", "reefer", "tier"]


def _generate_synthetic_training_data(n_samples: int = 2000, seed: int = 7) -> pd.DataFrame:
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

    return pd.DataFrame(
        {
            "weight_kg": weight_kg,
            "reefer": reefer,
            "tier": tier,
            "dwell_days": dwell_days,
        }
    )


class DwellTimeModel:
    def __init__(self) -> None:
        training_data = _generate_synthetic_training_data()
        self._model = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=7)
        self._model.fit(training_data[_FEATURE_COLUMNS], training_data["dwell_days"])

    def predict(self, weight_kg: float, reefer: bool, tier: int) -> float:
        features = pd.DataFrame(
            [[weight_kg, int(reefer), tier]],
            columns=_FEATURE_COLUMNS,
        )
        prediction = self._model.predict(features)[0]
        return round(float(prediction), 2)


dwell_time_model = DwellTimeModel()
