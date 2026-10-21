import numpy as np
import pandas as pd
import pytest

from ml.anomaly_detection import detect_seasonal_anomalies


def test_threshold_boundaries_ordering_ids_and_zero_baseline_are_deterministic():
    index = pd.date_range("2020-01-01", periods=240, freq="h")
    values = np.zeros(len(index))
    values[-3:] = [0.1, 0.5, 1.0]
    series = pd.Series(values, index=index)
    thresholds = {"low": 0.1, "medium": 0.5, "high": 1.0}

    events, counts, start, end = detect_seasonal_anomalies(series, thresholds)
    again, _, _, _ = detect_seasonal_anomalies(series, thresholds)

    assert [event["severity"] for event in events] == ["high", "medium", "low"]
    assert events[0]["deviation"] is None  # expected power is exactly zero
    assert [event["id"] for event in events] == [event["id"] for event in again]
    assert counts == {"low": 1, "medium": 1, "high": 1}
    assert end == index[-1]
    assert start == end - pd.Timedelta(days=7)


def test_missing_observations_are_skipped_and_empty_series_rejected():
    index = pd.date_range("2020-01-01", periods=240, freq="h")
    values = np.ones(len(index))
    values[-1] = np.nan
    events, counts, _, _ = detect_seasonal_anomalies(pd.Series(values, index=index), {"low": .1, "medium": .2, "high": .3})
    assert events == []
    assert sum(counts.values()) == 0
    with pytest.raises(ValueError, match="nonempty"):
        detect_seasonal_anomalies(pd.Series(dtype=float), {"low": .1, "medium": .2, "high": .3})


def test_thresholds_must_be_ordered():
    series = pd.Series([1.0], index=pd.DatetimeIndex(["2020-01-01"]))
    with pytest.raises(ValueError, match="ordered"):
        detect_seasonal_anomalies(series, {"low": .3, "medium": .2, "high": .1})
