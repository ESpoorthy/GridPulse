"""Reproducible training, validation-based model selection, and test reporting."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.baselines import PersistenceBaseline, SeasonalNaiveBaseline  # noqa: E402
from ml.data_loader import download_uci_dataset, load_hourly_data, prepare_for_training  # noqa: E402
from ml.evaluation import calculate_metrics  # noqa: E402
from ml.models import (  # noqa: E402
    create_hist_gradient_boosting,
    create_linear_regression,
    create_random_forest,
)
from ml.forecasting import evaluate_recursive_horizon  # noqa: E402
from scripts.validate_data import inspect_dataset  # noqa: E402

RAW = ROOT / "data/raw/household_power_consumption.txt"
HOURLY = ROOT / "data/processed/hourly_power.csv"
VALIDATION = ROOT / "reports/generated/dataset_validation.json"
RESULTS = ROOT / "reports/generated/real_data_results.json"
ARTIFACT = ROOT / "artifacts/selected_model.joblib"


def run() -> dict:
    raw_path = download_uci_dataset(RAW.parent)
    validation, hourly = inspect_dataset(raw_path)
    HOURLY.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION.parent.mkdir(parents=True, exist_ok=True)
    hourly.to_csv(HOURLY, index=False, date_format="%Y-%m-%dT%H:%M:%S")
    VALIDATION.write_text(json.dumps(validation, indent=2), encoding="utf-8")

    data = prepare_for_training(load_hourly_data(HOURLY))
    features = data["features"].dropna(subset=data["feature_columns"] + ["global_active_power_mean_kw"])
    # Define chronological boundaries after applying the shared complete-row policy.
    n = len(features)
    train_end, val_end = int(n * .70), int(n * .85)
    train, valid, test = features.iloc[:train_end], features.iloc[train_end:val_end], features.iloc[val_end:]
    target = "global_active_power_mean_kw"
    columns = data["feature_columns"]
    definitions = {
        "persistence": lambda: PersistenceBaseline(),
        "seasonal_naive_daily": lambda: SeasonalNaiveBaseline(24),
        "linear_regression": lambda: create_linear_regression(columns),
        "random_forest": lambda: create_random_forest(columns, n_estimators=100, max_depth=15, random_state=42),
        "hist_gradient_boosting": lambda: create_hist_gradient_boosting(columns, max_iter=100, max_depth=10),
    }
    scores: dict[str, dict] = {}
    X_train, X_val, X_test = train[columns], valid[columns], test[columns]
    y_train, y_val, y_test = train[target], valid[target], test[target]
    refit_X = pd_concat(train, valid, columns)
    refit_y = pd_concat_y(train, valid, target)
    for name, factory in definitions.items():
        model = factory()
        model.fit(X_train, y_train)
        val_metrics = calculate_metrics(y_val, model.predict(X_val))
        recursive_validation = evaluate_recursive_horizon(
            model,
            load_hourly_data(HOURLY),
            test_start=pd_timestamp(valid.timestamp.min()),
            test_end=pd_timestamp(valid.timestamp.max()),
            horizon=24,
            origin_stride_hours=72,
        )
        scores[name] = {
            "validation": val_metrics,
            "recursive_validation": recursive_validation,
        }
        print(f"Completed 24-hour validation for {name}.", flush=True)

    selected_name = min(
        scores,
        key=lambda name: (scores[name]["recursive_validation"]["metrics"]["mae"], name),
    )
    selected_model = None
    for name, factory in definitions.items():
        final_model = factory()
        final_model.fit(refit_X, refit_y)
        scores[name]["test"] = calculate_metrics(y_test, final_model.predict(X_test))
        print(f"Completed one-step held-out test scoring for {name}.", flush=True)
        if name == selected_name:
            selected_model = final_model
    recursive_test = evaluate_recursive_horizon(
        selected_model,
        load_hourly_data(HOURLY),
        test_start=pd_timestamp(test.timestamp.min()),
        test_end=pd_timestamp(test.timestamp.max()),
        horizon=24,
        origin_stride_hours=72,
    )
    print("Completed selected-model 24-hour held-out evaluation.", flush=True)

    # Validation-only seasonal residual calibration. The 2.5 sigma threshold
    # is used by the API; no test observations participate in calibration.
    val_residuals = (valid[target] - valid["lag_24h"]).dropna()
    residual_center = float(val_residuals.mean())
    residual_std = float(val_residuals.std(ddof=1))
    abs_residuals = val_residuals.abs()
    threshold_low, threshold_medium, threshold_high = (float(abs_residuals.quantile(q)) for q in (.95, .99, .995))
    metadata = {
        "artifact_format_version": 1,
        "model_version": "gridpulse-classical-v1",
        "dataset": validation["dataset_name"],
        "dataset_quality": validation,
        "target": target,
        "target_units": "kW",
        "forecast_strategy": "recursive one-step model",
        "one_step_ahead_only": False,
        "horizon_hours": 24,
        "selection_metric": "24-hour recursive validation MAE",
        "recursive_evaluation_config": {"horizon_hours": 24, "origin_stride_hours": 72},
        "split_ratio": "70/15/15",
        "feature_count": len(columns),
        "feature_columns": columns,
        "training_parameters": {
            "random_seed": 42,
            "random_forest": {"n_estimators": 100, "max_depth": 15, "min_samples_split": 2, "random_state": 42, "n_jobs": 1},
            "hist_gradient_boosting": {"max_iter": 100, "max_depth": 10, "random_state": 42},
            "hourly_min_valid_minutes": 45,
            "train_validation_test_ratio": [0.70, 0.15, 0.15],
        },
        "train_samples": len(train),
        "fit_samples": len(refit_X),
        "validation_samples": len(valid),
        "test_samples": len(test),
        "train_period": {"start": str(train.timestamp.min()), "end": str(train.timestamp.max())},
        "validation_period": {"start": str(valid.timestamp.min()), "end": str(valid.timestamp.max())},
        "test_period": {"start": str(test.timestamp.min()), "end": str(test.timestamp.max())},
        "models": scores,
        "best_model": selected_name,
        "recursive_test": recursive_test,
        "anomaly_calibration": {
            "method": "absolute 24-hour seasonal-naive validation residual quantiles (95th, 99th, 99.5th percentiles)",
            "validation_residual_mean_kw": residual_center,
            "validation_residual_std_kw": residual_std,
            "threshold_high_kw": threshold_high,
            "threshold_medium_kw": threshold_medium,
            "threshold_low_kw": threshold_low,
        },
    }
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": selected_model, "metadata": metadata}, ARTIFACT)
    return metadata


def pd_concat(first, second, columns):
    import pandas as pd
    return pd.concat([first[columns], second[columns]], ignore_index=True)


def pd_concat_y(first, second, target):
    import pandas as pd
    return pd.concat([first[target], second[target]], ignore_index=True)


def pd_timestamp(value):
    import pandas as pd
    return pd.Timestamp(value)


if __name__ == "__main__":
    result = run()
    print(json.dumps({"selected_model": result["best_model"], "test_metrics": result["models"][result["best_model"]]["test"]}, indent=2))
