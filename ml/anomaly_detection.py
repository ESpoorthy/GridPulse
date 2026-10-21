"""Validation-calibrated seasonal residual anomaly detection."""
from __future__ import annotations

import hashlib

import pandas as pd


def detect_seasonal_anomalies(
    series: pd.Series,
    thresholds: dict[str, float],
    *,
    end: pd.Timestamp | None = None,
    lookback_days: int = 7,
    seasonal_period_hours: int = 24,
) -> tuple[list[dict], dict[str, int], pd.Timestamp, pd.Timestamp]:
    """Flag unusual seasonal residuals using frozen validation thresholds.

    The input series contains observed hourly mean power in kW. Expected power
    is the value one seasonal period earlier. Events indicate unusual values;
    they do not establish a cause or calibrated probability.
    """
    if lookback_days < 1 or seasonal_period_hours < 1:
        raise ValueError("lookback_days and seasonal_period_hours must be positive")
    required = {"low", "medium", "high"}
    if not required.issubset(thresholds):
        raise ValueError("thresholds must contain low, medium, and high bands")
    low, medium, high = (float(thresholds[key]) for key in ("low", "medium", "high"))
    if not (0 <= low <= medium <= high):
        raise ValueError("anomaly thresholds must be nonnegative and ordered")
    if series.empty:
        raise ValueError("anomaly detection requires a nonempty hourly series")
    if not isinstance(series.index, pd.DatetimeIndex):
        raise ValueError("anomaly detection requires a DatetimeIndex")
    if series.index.has_duplicates:
        raise ValueError("anomaly detection requires unique hourly timestamps")
    values = pd.to_numeric(series, errors="coerce").sort_index().asfreq("h")
    end = pd.Timestamp(end) if end is not None else pd.Timestamp(values.index.max())
    start = end - pd.Timedelta(days=lookback_days)
    expected = values.shift(seasonal_period_hours)
    residual = values - expected
    window = pd.DataFrame({"observed": values, "expected": expected, "residual": residual}).loc[start:end]
    events: list[dict] = []
    counts = {"low": 0, "medium": 0, "high": 0}
    for timestamp, row in window.dropna().iterrows():
        magnitude = abs(float(row.residual))
        severity = "high" if magnitude >= high else "medium" if magnitude >= medium else "low" if magnitude >= low else None
        if severity is None:
            continue
        counts[severity] += 1
        expected_power = float(row.expected)
        residual_value = float(row.residual)
        deviation = residual_value / expected_power * 100 if expected_power > 0 else None
        direction = "above" if residual_value > 0 else "below"
        events.append({
            "id": hashlib.sha256(timestamp.isoformat().encode()).hexdigest()[:12],
            "timestamp": timestamp.isoformat(),
            "observed_power": float(row.observed),
            "expected_power": expected_power,
            "deviation": deviation,
            "severity": severity,
            "reason": f"Observed power was {magnitude:.3f} kW {direction} the {seasonal_period_hours}-hour seasonal baseline.",
        })
    order = {"high": 0, "medium": 1, "low": 2}
    events.sort(key=lambda event: (order[event["severity"]], event["timestamp"]))
    return events, counts, start, end
