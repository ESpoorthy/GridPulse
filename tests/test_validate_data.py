"""Unit tests for the local dataset validation utility."""
from __future__ import annotations

import csv
from datetime import datetime, timedelta
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")

from scripts.validate_data import inspect_dataset  # noqa: E402

HEADER = [
    "Date", "Time", "Global_active_power", "Global_reactive_power",
    "Voltage", "Global_intensity", "Sub_metering_1", "Sub_metering_2",
    "Sub_metering_3",
]


def _row(timestamp: datetime, power: str) -> list[str]:
    return [
        timestamp.strftime("%d/%m/%Y"),
        timestamp.strftime("%H:%M:%S"),
        power, "0.1", "230.0", "1.0", "0.0", "0.0", "0.0",
    ]


def _write_fixture(path: Path) -> None:
    start = datetime(2007, 1, 1, 0, 0)
    rows: list[list[str]] = []
    for minute in range(60):
        ts = start + timedelta(minutes=minute)
        rows.append(_row(ts, "1.0"))
        if minute == 30:
            rows.append(_row(ts, "1.0"))
    for minute in range(60, 120):
        ts = start + timedelta(minutes=minute)
        rows.append(_row(ts, "2.0" if minute < 104 else "?"))
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(HEADER)
        writer.writerows(rows)


def test_inspection_reports_missing_values_duplicates_and_hourly_bins(tmp_path: Path) -> None:
    source = tmp_path / "household_power_consumption.txt"
    _write_fixture(source)
    report, hourly = inspect_dataset(
        source, min_valid_minutes_per_hour=45, expected_rows=None, chunksize=17
    )

    assert report["row_count"] == 121
    assert report["row_count_matches_expected"] is True
    assert report["timestamp_parse_failures"] == 0
    assert report["timestamps_chronological"] is True
    assert report["duplicate_timestamp_count"] == 1
    assert report["missing_numeric_values"]["Global_active_power"] == 16
    assert report["hourly_aggregation"]["hourly_bins_in_time_range"] == 2
    assert report["hourly_aggregation"]["eligible_hours"] == 1
    assert len(hourly) == 1
    assert hourly.loc[0, "global_active_power_mean_kw"] == pytest.approx(1.0)
    assert int(hourly.loc[0, "valid_minutes"]) == 61


def test_rejects_wrong_schema(tmp_path: Path) -> None:
    source = tmp_path / "bad.csv"
    source.write_text(
        "Date;Time;power\n01/01/2007;00:00:00;1.0\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="missing columns"):
        inspect_dataset(source, expected_rows=None)


def test_missing_file_has_actionable_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Download the file"):
        inspect_dataset(tmp_path / "missing.txt")
