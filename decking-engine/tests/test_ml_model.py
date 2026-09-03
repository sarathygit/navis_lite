import numpy as np
import pandas as pd

from app.services.ml_model import dwell_time_model, evaluate
from app.services.training_data import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    generate_synthetic_training_data,
)


def test_model_beats_a_naive_mean_baseline():
    """The point of the ensemble is to be better than guessing the average.

    If this ever fails, the model is not earning its complexity and a simpler
    estimator should replace it.
    """
    _, metrics = evaluate(generate_synthetic_training_data(n_samples=800))

    assert metrics["beats_baseline"] is True
    assert metrics["mae_days"] < metrics["baseline_mae_days"]
    assert metrics["improvement_over_baseline_pct"] > 0


def test_evaluation_holds_out_a_genuine_test_set():
    frame = generate_synthetic_training_data(n_samples=500)
    _, metrics = evaluate(frame)

    assert metrics["training_rows"] == 500
    assert metrics["train_rows"] + metrics["test_rows"] == 500
    # default split is 20% held out
    assert metrics["test_rows"] == 100


def test_cross_validation_runs_and_reports_spread():
    _, metrics = evaluate(generate_synthetic_training_data(n_samples=400))

    assert metrics["cv_folds"] == 5
    assert metrics["cv_mae_days"] > 0
    assert metrics["cv_mae_std"] >= 0


def test_metrics_include_the_standard_regression_measures():
    _, metrics = evaluate(generate_synthetic_training_data(n_samples=400))

    assert metrics["mae_days"] > 0
    assert metrics["rmse_days"] >= metrics["mae_days"]  # RMSE penalises large errors harder
    assert -1.0 <= metrics["r2"] <= 1.0


def test_feature_attribution_covers_every_feature_and_sums_to_one():
    _, metrics = evaluate(generate_synthetic_training_data(n_samples=400))
    importances = metrics["feature_importances"]

    assert set(importances) == set(FEATURE_COLUMNS)
    assert abs(sum(importances.values()) - 1.0) < 0.02
    assert metrics["attribution_kind"] in ("impurity_importance", "standardised_abs_coefficient")


def test_weight_is_recognised_as_the_dominant_driver_of_dwell():
    """Guards a real bug: raw linear coefficients are on each feature's own scale,
    so weight_kg (thousands) looked like ~0 importance next to reefer (0/1) even
    though the corpus is built with weight as the strongest driver. Attribution
    must be scale-corrected before it means anything."""
    _, metrics = evaluate(generate_synthetic_training_data(n_samples=800))
    importances = metrics["feature_importances"]

    assert importances["weight_kg"] > 0.10, "weight must not be crushed by feature scale"
    assert importances["weight_kg"] == max(importances.values())


def test_model_selection_compares_every_candidate_and_picks_the_lowest_mae():
    _, metrics = evaluate(generate_synthetic_training_data(n_samples=600))
    selection = metrics["model_selection"]

    assert set(selection) == {"linear_regression", "random_forest"}
    # the deployed model must be the measured winner, not a preferred default
    assert metrics["selected_model"] == min(selection, key=selection.get)


def test_linear_model_wins_on_the_synthetic_corpus():
    """The synthetic generator builds dwell from a linear formula, so a linear
    estimator should beat the ensemble. This documents a real measured finding:
    the RandomForest was not earning its complexity here."""
    _, metrics = evaluate(generate_synthetic_training_data(n_samples=800))

    assert metrics["selected_model"] == "linear_regression"
    assert metrics["model_selection"]["linear_regression"] < metrics["model_selection"]["random_forest"]


def test_healthy_corpus_is_not_flagged_as_degenerate():
    _, metrics = evaluate(generate_synthetic_training_data(n_samples=400))

    assert metrics["degenerate_target"] is False
    assert metrics["metrics_meaningful"] is True
    assert metrics["target_std_days"] > 0.01


def test_degenerate_target_is_flagged_so_a_vacuous_win_is_not_trusted():
    """Every container dwelling the same few seconds — as happens on a demo
    terminal checked straight in and out — leaves nothing to predict. MAE
    collapses to ~0 and 'beats the baseline' becomes meaningless, so the result
    must be marked untrustworthy rather than reported as a good model."""
    flat = pd.DataFrame(
        {
            "weight_kg": np.linspace(4000, 30000, 60),
            "reefer": [i % 2 for i in range(60)],
            "tier": [(i % 5) + 1 for i in range(60)],
            "is_heavy": [1 if w > 20000 else 0 for w in np.linspace(4000, 30000, 60)],
            "dwell_days": [0.0001] * 60,  # all checked out within seconds
        }
    )[FEATURE_COLUMNS + [TARGET_COLUMN]]

    _, metrics = evaluate(flat)

    assert metrics["degenerate_target"] is True
    assert metrics["metrics_meaningful"] is False


def test_evaluate_survives_a_tiny_dataset_without_crashing():
    tiny = pd.DataFrame(
        {
            "weight_kg": [5000.0, 25000.0, 12000.0, 30000.0, 8000.0],
            "reefer": [0, 1, 0, 1, 0],
            "tier": [3, 1, 4, 2, 5],
            "is_heavy": [0, 1, 0, 1, 0],
            "dwell_days": [2.0, 6.0, 3.0, 7.5, 2.5],
        }
    )[FEATURE_COLUMNS + [TARGET_COLUMN]]

    model, metrics = evaluate(tiny)

    assert metrics["training_rows"] == 5
    assert model.predict(tiny[FEATURE_COLUMNS].head(1))[0] > 0


def test_deployed_model_predicts_a_plausible_dwell():
    prediction = dwell_time_model.predict(weight_kg=24000, reefer=False, tier=1)
    assert 0 < prediction < 30


def test_deployed_model_exposes_its_metrics():
    metrics = dwell_time_model.get_metrics()

    assert "mae_days" in metrics
    assert "data_source" in metrics
    assert metrics["data_source"] in ("synthetic", "history")
    assert "trained_at" in metrics


def test_heavier_cargo_is_predicted_to_dwell_longer():
    """Directional sanity check against the domain assumption, at matched tier."""
    light = dwell_time_model.predict(weight_kg=4000, reefer=False, tier=1)
    heavy = dwell_time_model.predict(weight_kg=30000, reefer=False, tier=1)
    assert heavy > light
