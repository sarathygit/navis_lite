"""Dwell-time prediction model for the Expert Decking Engine.

Predicts how many days a container will occupy a slot, which the decking
algorithm uses to rank candidate placements and to score rehandle risk.

The model is evaluated, not just fitted. Every training run holds out a test
set, runs k-fold cross-validation, and compares itself against a naive
mean-predicting baseline. If the ensemble cannot beat "always guess the
average", that is worth knowing and is reported rather than buried — a model
that does not beat its baseline is not earning the complexity it costs.

Metrics are exposed at /api/model/metrics so an operator can see how much to
trust the placement decisions being made on their behalf.
"""

import logging
import threading
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split

from app.core.config import (
    CROSS_VALIDATION_FOLDS,
    DEGENERATE_TARGET_STD_DAYS,
    MODEL_RANDOM_STATE,
    TEST_SET_FRACTION,
)
from app.services.training_data import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    generate_synthetic_training_data,
    load_training_data,
)

logger = logging.getLogger(__name__)


def _candidate_models() -> dict[str, Any]:
    """The estimators that compete for deployment on every training run.

    A RandomForest is not assumed to be the right answer. When the underlying
    relationship is close to linear — which it is in the synthetic corpus, and
    may well be in a real terminal — a linear model is both more accurate and
    dramatically cheaper. Selection is decided by measurement, not by preference.
    """
    return {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(
            n_estimators=100, max_depth=8, random_state=MODEL_RANDOM_STATE
        ),
    }


def evaluate(frame: pd.DataFrame) -> tuple[Any, dict[str, Any]]:
    """Selects, fits and honestly measures the dwell-time model.

    Every candidate is scored by cross-validated MAE on the training split; the
    winner is then measured on a test set it has never seen and refitted on the
    full frame so no data is wasted in production.
    """
    features = frame[FEATURE_COLUMNS]
    target = frame[TARGET_COLUMN]

    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=TEST_SET_FRACTION, random_state=MODEL_RANDOM_STATE
    )

    folds = min(CROSS_VALIDATION_FOLDS, len(x_train))

    # --- model selection: cross-validate each candidate, lowest MAE wins ---
    selection: dict[str, float] = {}
    for name, candidate in _candidate_models().items():
        if folds >= 2:
            scores = -cross_val_score(
                candidate, x_train, y_train, cv=folds, scoring="neg_mean_absolute_error"
            )
            selection[name] = round(float(np.mean(scores)), 4)
        else:
            candidate.fit(x_train, y_train)
            selection[name] = round(
                float(mean_absolute_error(y_train, candidate.predict(x_train))), 4
            )

    selected_name = min(selection, key=selection.get)
    model = _candidate_models()[selected_name]

    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    # Naive baseline: predict the training mean for every container. Any model
    # worth deploying must beat this by a clear margin.
    baseline = DummyRegressor(strategy="mean")
    baseline.fit(x_train, y_train)
    baseline_predictions = baseline.predict(x_test)

    model_mae = float(mean_absolute_error(y_test, predictions))
    baseline_mae = float(mean_absolute_error(y_test, baseline_predictions))

    # k-fold CV for the selected model, scored as MAE (sklearn returns it
    # negated because its convention is "higher is better").
    if folds >= 2:
        cv_scores = -cross_val_score(
            model, x_train, y_train, cv=folds, scoring="neg_mean_absolute_error"
        )
        cv_mae_mean = float(np.mean(cv_scores))
        cv_mae_std = float(np.std(cv_scores))
    else:
        cv_mae_mean = None
        cv_mae_std = None

    improvement = (
        round((baseline_mae - model_mae) / baseline_mae * 100.0, 1)
        if baseline_mae > 0
        else 0.0
    )

    # Degenerate-target guard. If every container in the corpus dwelled for
    # essentially the same time, MAE collapses toward zero and "beats the
    # baseline" becomes a vacuous claim — there was nothing to predict. This
    # happens for real: a freshly seeded demo terminal where containers are
    # checked in and straight back out produces dwell times measured in seconds.
    # Surface it rather than reporting a meaningless win.
    target_std = float(np.std(target))
    target_range = float(np.max(target) - np.min(target))
    degenerate = target_std < DEGENERATE_TARGET_STD_DAYS

    # Feature attribution, however the selected estimator expresses it.
    #
    # Trees report impurity-based importances directly. Linear coefficients need
    # care: they live on each feature's own scale, so weight_kg (thousands) gets
    # a numerically tiny coefficient next to reefer (0/1) even when weight is the
    # far stronger driver. Multiplying by the feature's standard deviation gives
    # the standardised coefficient — the effect of a one-SD move in that feature —
    # which is comparable across features. Without this, weight_kg reports as ~0
    # importance, which is precisely backwards.
    if hasattr(model, "feature_importances_"):
        raw_attribution = np.asarray(model.feature_importances_, dtype=float)
        attribution_kind = "impurity_importance"
    else:
        standardised = np.abs(
            np.asarray(model.coef_, dtype=float) * features.std(axis=0).to_numpy()
        )
        total = standardised.sum()
        raw_attribution = standardised / total if total > 0 else standardised
        attribution_kind = "standardised_abs_coefficient"

    metrics: dict[str, Any] = {
        "selected_model": selected_name,
        "model_selection": selection,
        "attribution_kind": attribution_kind,
        "training_rows": int(len(frame)),
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "mae_days": round(model_mae, 5),
        "rmse_days": round(float(np.sqrt(mean_squared_error(y_test, predictions))), 5),
        "r2": round(float(r2_score(y_test, predictions)), 3),
        "baseline_mae_days": round(baseline_mae, 5),
        "beats_baseline": bool(model_mae < baseline_mae),
        "improvement_over_baseline_pct": improvement,
        "target_std_days": round(target_std, 5),
        "target_range_days": round(target_range, 5),
        "degenerate_target": degenerate,
        "metrics_meaningful": not degenerate,
        "cv_folds": folds if folds >= 2 else None,
        "cv_mae_days": round(cv_mae_mean, 5) if cv_mae_mean is not None else None,
        "cv_mae_std": round(cv_mae_std, 5) if cv_mae_std is not None else None,
        "feature_importances": {
            name: round(float(importance), 3)
            for name, importance in zip(FEATURE_COLUMNS, raw_attribution)
        },
    }

    # Refit on everything now that the honest measurement is taken.
    model.fit(features, target)
    return model, metrics


class DwellTimeModel:
    """Thread-safe wrapper around the fitted estimator.

    Starts on the synthetic corpus so the service is usable the instant it
    boots — no network call in the import path — then retrains from real
    history once the gateway is reachable.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        frame = generate_synthetic_training_data()
        model, metrics = evaluate(frame)
        self._model = model
        self._metrics = {
            **metrics,
            "data_source": "synthetic",
            "provenance": {"source": "synthetic", "reason": "initial start-up, history not yet queried"},
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }

    def retrain_from_history(self) -> dict[str, Any]:
        """Rebuilds the model from real operating history when enough exists."""
        frame, provenance = load_training_data()
        model, metrics = evaluate(frame)

        with self._lock:
            self._model = model
            self._metrics = {
                **metrics,
                "data_source": provenance.get("source", "unknown"),
                "provenance": provenance,
                "trained_at": datetime.now(timezone.utc).isoformat(),
            }
            snapshot = dict(self._metrics)

        logger.info(
            "Dwell model retrained from %s: %s rows, MAE %.3f days (baseline %.3f)",
            snapshot["data_source"],
            snapshot["training_rows"],
            snapshot["mae_days"],
            snapshot["baseline_mae_days"],
        )
        return snapshot

    def predict(self, weight_kg: float, reefer: bool, tier: int) -> float:
        from app.core.config import HEAVY_WEIGHT_THRESHOLD_KG

        features = pd.DataFrame(
            [[weight_kg, int(reefer), tier, int(weight_kg > HEAVY_WEIGHT_THRESHOLD_KG)]],
            columns=FEATURE_COLUMNS,
        )
        with self._lock:
            prediction = self._model.predict(features)[0]
        return round(float(prediction), 2)

    def get_metrics(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._metrics)


dwell_time_model = DwellTimeModel()
