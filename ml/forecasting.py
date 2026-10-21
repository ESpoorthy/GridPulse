"""Recursive multi-step forecasting using a fitted one-step model."""
from __future__ import annotations

import pandas as pd
import numpy as np

from ml.evaluation import calculate_metrics
from ml.features import build_feature_row, build_feature_rows

TARGET = "global_active_power_mean_kw"


def recursive_forecast(
    model,
    hourly: pd.DataFrame,
    *,
    horizon: int = 24,
    timestamp_col: str = "timestamp",
    target_col: str = TARGET,
) -> pd.DataFrame:
    """Predict future hours recursively, feeding predictions back as history.

    No future actual values are accepted by this function. Each step's
    prediction becomes the only target value available to later steps.
    """
    if horizon < 1:
        raise ValueError("horizon must be positive")
    if timestamp_col not in hourly or target_col not in hourly:
        raise ValueError(f"hourly must include {timestamp_col!r} and {target_col!r}")
    history = hourly[[timestamp_col, target_col]].copy()
    history[timestamp_col] = pd.to_datetime(history[timestamp_col], errors="coerce")
    history[target_col] = pd.to_numeric(history[target_col], errors="coerce")
    history = history.dropna().sort_values(timestamp_col).reset_index(drop=True)
    if history.empty:
        raise ValueError("hourly history has no valid observations")
    if history[timestamp_col].duplicated().any():
        raise ValueError("hourly history contains duplicate timestamps")
    if (history[timestamp_col].diff().dropna() != pd.Timedelta(hours=1)).any():
        raise ValueError("hourly history must be contiguous; missing hours cannot be bridged")

    # The default feature set reaches back 168 hours (including a complete
    # 168-hour rolling window). Keep only that window plus the new row so
    # repeated recursive scoring does not rebuild features over the full
    # multi-decade history at every prediction step.
    history = history.tail(168).reset_index(drop=True)
    target_values = history[target_col].astype(float).tolist()
    last_timestamp = history[timestamp_col].iloc[-1]

    forecasts: list[dict[str, object]] = []
    for _ in range(horizon):
        next_timestamp = last_timestamp + pd.Timedelta(hours=1)
        row = build_feature_row(next_timestamp, target_values)
        feature_columns = getattr(
            model,
            "feature_cols",
            [column for column in row.columns if column not in {timestamp_col, target_col, "valid_minutes"}],
        )
        missing = [column for column in feature_columns if column not in row.columns or pd.isna(row.iloc[0][column])]
        if missing:
            raise ValueError(f"insufficient contiguous history for model features: {missing}")
        prediction = float(model.predict(row)[0])
        forecasts.append({"timestamp": next_timestamp, "predicted": prediction})
        target_values.append(prediction)
        last_timestamp = next_timestamp

    return pd.DataFrame(forecasts)


def evaluate_recursive_horizon(
    model,
    hourly: pd.DataFrame,
    *,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
    horizon: int = 24,
    origin_stride_hours: int = 24,
    minimum_history_hours: int = 169,
) -> dict:
    """Walk-forward score a recursive forecast on complete held-out windows.

    Origins are selected at a fixed cadence. Incomplete actual target windows
    and origins without sufficient contiguous history are skipped and counted.
    At each origin inference receives only observations at or before that time.
    """
    if horizon < 1 or origin_stride_hours < 1:
        raise ValueError("horizon and origin_stride_hours must be positive")
    hourly = hourly.sort_values("timestamp").reset_index(drop=True)
    series = hourly.set_index("timestamp")[TARGET].asfreq("h")
    start, end = pd.Timestamp(test_start), pd.Timestamp(test_end)
    first_origin = start - pd.Timedelta(hours=1)
    last_origin = end - pd.Timedelta(hours=horizon)
    origins: list[pd.Timestamp] = []
    actual_windows: list[np.ndarray] = []
    history_windows: list[np.ndarray] = []
    skipped_incomplete = 0
    skipped_history = 0
    origin = first_origin
    while origin <= last_origin:
        target_times = pd.date_range(origin + pd.Timedelta(hours=1), periods=horizon, freq="h")
        actual = series.reindex(target_times)
        if actual.isna().any():
            skipped_incomplete += 1
            origin += pd.Timedelta(hours=origin_stride_hours)
            continue
        history = hourly.loc[hourly["timestamp"] <= origin, ["timestamp", TARGET]].copy().reset_index(drop=True)
        gap_positions = np.flatnonzero(history["timestamp"].diff().ne(pd.Timedelta(hours=1)).to_numpy())
        if len(gap_positions):
            history = history.iloc[gap_positions[-1]:]
        if len(history) < minimum_history_hours:
            skipped_history += 1
            origin += pd.Timedelta(hours=origin_stride_hours)
            continue
        origins.append(origin)
        actual_windows.append(actual.astype(float).to_numpy())
        history_windows.append(history[TARGET].tail(168).astype(float).to_numpy())
        origin += pd.Timedelta(hours=origin_stride_hours)
    if not actual_windows:
        raise ValueError("No complete recursive forecast windows were available in the test period")
    histories = np.stack(history_windows)
    actual_values = np.stack(actual_windows)
    predicted_values = np.empty_like(actual_values)
    model_features = getattr(model, "feature_cols", None)
    for step in range(horizon):
        future_times = pd.DatetimeIndex([origin + pd.Timedelta(hours=step + 1) for origin in origins])
        feature_frame = build_feature_rows(future_times, histories)
        if model_features is not None:
            missing = [column for column in model_features if column not in feature_frame or feature_frame[column].isna().any()]
            if missing:
                raise ValueError(f"insufficient contiguous history for model features: {missing}")
            feature_frame = feature_frame[model_features]
        predictions = np.asarray(model.predict(feature_frame), dtype=float).reshape(-1)
        predicted_values[:, step] = predictions
        histories = np.concatenate((histories[:, 1:], predictions[:, None]), axis=1)
    y_true = actual_values.ravel().tolist()
    y_pred = predicted_values.ravel().tolist()
    return {
        "metrics": calculate_metrics(y_true, y_pred),
        "step_group_metrics": {
            label: calculate_metrics(
                actual_values[:, first - 1:last].ravel().tolist(),
                predicted_values[:, first - 1:last].ravel().tolist(),
            )
            for label, first, last in (
                ("hours_1_6", 1, min(6, horizon)),
                ("hours_7_12", 7, min(12, horizon)),
                ("hours_13_24", 13, min(24, horizon)),
            )
            if first <= horizon
        },
        "horizon_hours": horizon,
        "forecast_origins": len(origins),
        "evaluated_hours": len(y_true),
        "skipped_incomplete_windows": skipped_incomplete,
        "skipped_insufficient_history": skipped_history,
        "origin_stride_hours": origin_stride_hours,
        "evaluation_period": {
            "start": (origins[0] + pd.Timedelta(hours=1)).isoformat(),
            "end": (origins[-1] + pd.Timedelta(hours=horizon)).isoformat(),
        },
        "first_origin": origins[0].isoformat(),
        "last_origin": origins[-1].isoformat(),
    }
