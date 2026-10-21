from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.features import build_feature_row, build_features, get_feature_columns
from ml.forecasting import evaluate_recursive_horizon, recursive_forecast


class LastValueModel:
    feature_cols = ["lag_1h"]

    def predict(self, frame):
        return frame["lag_1h"].to_numpy()


def test_recursive_forecast_returns_consecutive_future_points_without_actuals():
    history = pd.DataFrame({
        "timestamp": pd.date_range("2020-01-01", periods=180, freq="h"),
        "global_active_power_mean_kw": np.arange(180, dtype=float),
    })
    result = recursive_forecast(LastValueModel(), history, horizon=24)
    assert len(result) == 24
    assert result.timestamp.iloc[0] == history.timestamp.iloc[-1] + pd.Timedelta(hours=1)
    assert result.timestamp.iloc[-1] == history.timestamp.iloc[-1] + pd.Timedelta(hours=24)
    assert result.predicted.tolist() == [179.0] * 24


def test_recursive_forecast_rejects_missing_hour_gaps():
    history = pd.DataFrame({
        "timestamp": [pd.Timestamp("2020-01-01"), pd.Timestamp("2020-01-01 02:00")],
        "global_active_power_mean_kw": [1.0, 2.0],
    })
    with pytest.raises(ValueError, match="contiguous"):
        recursive_forecast(LastValueModel(), history)


def test_single_row_inference_features_match_batch_feature_builder():
    history = pd.DataFrame({
        "timestamp": pd.date_range("2020-01-01", periods=180, freq="h"),
        "global_active_power_mean_kw": np.sin(np.arange(180) / 8) + 2,
    })
    future_timestamp = history.timestamp.iloc[-1] + pd.Timedelta(hours=1)
    batch = build_features(pd.concat([history, pd.DataFrame({
        "timestamp": [future_timestamp],
        "global_active_power_mean_kw": [np.nan],
    })], ignore_index=True)).iloc[-1]
    one_row = build_feature_row(future_timestamp, history.global_active_power_mean_kw.to_numpy()).iloc[0]
    columns = get_feature_columns()["all"]
    np.testing.assert_allclose(one_row[columns].astype(float), batch[columns].astype(float))


def test_recursive_horizon_evaluation_uses_complete_fixed_stride_windows():
    hourly = pd.DataFrame({
        "timestamp": pd.date_range("2020-01-01", periods=600, freq="h"),
        "global_active_power_mean_kw": np.arange(600, dtype=float),
    })
    results = evaluate_recursive_horizon(
        LastValueModel(), hourly, test_start=hourly.timestamp.iloc[400],
        test_end=hourly.timestamp.iloc[599], horizon=24, origin_stride_hours=24,
    )
    assert results["horizon_hours"] == 24
    assert results["forecast_origins"] > 0
    assert results["evaluated_hours"] == results["forecast_origins"] * 24
    assert results["metrics"]["mae"] == pytest.approx(12.5)
    assert set(results["step_group_metrics"]) == {"hours_1_6", "hours_7_12", "hours_13_24"}
    assert results["step_group_metrics"]["hours_1_6"]["mae"] == pytest.approx(3.5)
