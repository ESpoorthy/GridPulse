"""Validate the UCI household power dataset and export hourly averages.

Usage:
    python scripts/validate_data.py --input data/raw/household_power_consumption.txt

The raw dataset is never uploaded by this script. Reports and hourly data are
written locally to ignored paths by default.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

EXPECTED_ROWS = 2_075_259
COLUMNS = [
    "Date", "Time", "Global_active_power", "Global_reactive_power",
    "Voltage", "Global_intensity", "Sub_metering_1", "Sub_metering_2",
    "Sub_metering_3",
]
NUMERIC_COLUMNS = COLUMNS[2:]
TARGET = "Global_active_power"


def inspect_dataset(
    input_path: str | Path,
    *,
    min_valid_minutes_per_hour: int = 45,
    expected_rows: int | None = EXPECTED_ROWS,
    chunksize: int = 100_000,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Inspect source rows in chunks and return a quality report plus hourly data."""
    path = Path(input_path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {path}. Download the file from the official UCI "
            "dataset page and place it at data/raw/household_power_consumption.txt."
        )
    if not 1 <= min_valid_minutes_per_hour <= 60:
        raise ValueError("min_valid_minutes_per_hour must be between 1 and 60.")
    if chunksize < 1:
        raise ValueError("chunksize must be positive.")

    rows = 0
    bad_timestamps = 0
    missing_values = dict.fromkeys(NUMERIC_COLUMNS, 0)
    numeric_parse_errors = dict.fromkeys(NUMERIC_COLUMNS, 0)
    negative_target_count = 0
    timestamp_arrays: list[np.ndarray] = []
    hourly_parts: list[pd.DataFrame] = []
    chronological = True
    previous_timestamp: pd.Timestamp | None = None
    target_min: float | None = None
    target_max: float | None = None

    reader = pd.read_csv(
        path,
        sep=";",
        dtype=str,
        keep_default_na=False,
        chunksize=chunksize,
        encoding="utf-8-sig",
    )

    for chunk in reader:
        chunk.columns = [str(c).replace("\ufeff", "").strip() for c in chunk.columns]
        missing_columns = sorted(set(COLUMNS) - set(chunk.columns))
        if missing_columns:
            raise ValueError("Unexpected dataset schema; missing columns: " + ", ".join(missing_columns))

        rows += len(chunk)
        timestamp = pd.to_datetime(
            chunk["Date"].astype("string").str.strip()
            + " "
            + chunk["Time"].astype("string").str.strip(),
            format="%d/%m/%Y %H:%M:%S",
            errors="coerce",
        )
        bad_timestamps += int(timestamp.isna().sum())
        timestamp_arrays.append(timestamp.to_numpy(dtype="datetime64[ns]"))

        valid_timestamp = timestamp.dropna()
        if not valid_timestamp.empty:
            if not valid_timestamp.is_monotonic_increasing:
                chronological = False
            if previous_timestamp is not None and valid_timestamp.iloc[0] < previous_timestamp:
                chronological = False
            previous_timestamp = valid_timestamp.iloc[-1]

        numbers: dict[str, pd.Series] = {}
        for name in NUMERIC_COLUMNS:
            raw = chunk[name].astype("string").str.strip()
            missing = raw.isna() | raw.isin(["", "?"])
            parsed = pd.to_numeric(raw.mask(missing), errors="coerce")
            missing_values[name] += int(missing.sum())
            numeric_parse_errors[name] += int((~missing & parsed.isna()).sum())
            numbers[name] = parsed

        target = numbers[TARGET]
        negative_target_count += int((target < 0).sum())
        observed = target.dropna()
        if not observed.empty:
            chunk_min, chunk_max = float(observed.min()), float(observed.max())
            target_min = chunk_min if target_min is None else min(target_min, chunk_min)
            target_max = chunk_max if target_max is None else max(target_max, chunk_max)

        aggregation = pd.DataFrame({"hour": timestamp.dt.floor("h"), "target": target})
        aggregation = aggregation.dropna(subset=["hour", "target"])
        if not aggregation.empty:
            hourly_parts.append(
                aggregation.groupby("hour", as_index=False)["target"]
                .agg(total="sum", valid_minutes="count")
            )

    if rows == 0 or not timestamp_arrays:
        raise ValueError("The dataset file contains no records.")
    timestamps = pd.DatetimeIndex(np.concatenate(timestamp_arrays))
    timestamps = timestamps[~timestamps.isna()]
    if timestamps.empty:
        raise ValueError("No timestamps could be parsed; check date/time formats.")

    hour_index = pd.date_range(timestamps.min().floor("h"), timestamps.max().floor("h"), freq="h")
    if hourly_parts:
        grouped = pd.concat(hourly_parts, ignore_index=True).groupby("hour")[["total", "valid_minutes"]].sum()
        grouped = grouped.reindex(hour_index, fill_value=0)
    else:
        grouped = pd.DataFrame({"total": 0.0, "valid_minutes": 0}, index=hour_index)

    eligible = grouped["valid_minutes"] >= min_valid_minutes_per_hour
    hourly = pd.DataFrame({
        "timestamp": grouped.index[eligible],
        "global_active_power_mean_kw": (
            grouped.loc[eligible, "total"] / grouped.loc[eligible, "valid_minutes"]
        ).to_numpy(),
        "valid_minutes": grouped.loc[eligible, "valid_minutes"].astype(int).to_numpy(),
    }).reset_index(drop=True)

    matches_expected = expected_rows is None or rows == expected_rows
    duplicate_count = int(timestamps.duplicated().sum())
    report: dict[str, Any] = {
        "dataset_name": "UCI Individual Household Electric Power Consumption",
        "input_file": path.name,
        "file_size_bytes": path.stat().st_size,
        "row_count": rows,
        "expected_row_count": expected_rows,
        "row_count_matches_expected": matches_expected,
        "required_columns": COLUMNS,
        "missing_numeric_values": missing_values,
        "numeric_parse_errors": numeric_parse_errors,
        "timestamp_parse_failures": bad_timestamps,
        "timestamps_chronological": chronological,
        "duplicate_timestamp_count": duplicate_count,
        "first_timestamp": timestamps.min().isoformat(),
        "last_timestamp": timestamps.max().isoformat(),
        "global_active_power_min_kw": target_min,
        "global_active_power_max_kw": target_max,
        "negative_active_power_value_count": negative_target_count,
        "hourly_aggregation": {
            "minimum_valid_minutes_per_hour": min_valid_minutes_per_hour,
            "hourly_bins_in_time_range": len(hour_index),
            "eligible_hours": int(eligible.sum()),
            "excluded_hours_below_coverage_threshold": int((~eligible).sum()),
            "output_hourly_rows": len(hourly),
        },
    }

    warnings: list[str] = []
    if not matches_expected:
        warnings.append(
            f"Row count {rows} differs from published expected count {expected_rows}; "
            "check the download and header handling."
        )
    if bad_timestamps:
        warnings.append(f"{bad_timestamps} timestamp(s) could not be parsed.")
    if not chronological:
        warnings.append("Input timestamps are not in chronological order.")
    if duplicate_count:
        warnings.append(f"{duplicate_count} duplicate timestamp(s) detected.")
    parse_error_total = sum(numeric_parse_errors.values())
    if parse_error_total:
        warnings.append(f"{parse_error_total} non-missing numeric value(s) could not be parsed.")
    if negative_target_count:
        warnings.append(f"{negative_target_count} negative active-power value(s) need inspection.")
    if any(missing_values.values()):
        warnings.append("Missing numeric readings detected; this script does not impute them.")

    report["warnings"] = warnings
    report["validation_status"] = "passed_with_warnings" if warnings else "passed"
    return report, hourly


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate UCI household power data.")
    parser.add_argument("--input", default="data/raw/household_power_consumption.txt")
    parser.add_argument("--min-valid-minutes-per-hour", type=int, default=45)
    parser.add_argument(
        "--expected-rows",
        type=int,
        default=EXPECTED_ROWS,
        help="Set to 0 to disable the expected row-count comparison.",
    )
    parser.add_argument("--report-out", default="reports/generated/dataset_validation.json")
    parser.add_argument("--hourly-out", default="data/processed/hourly_power.csv")
    args = parser.parse_args()

    try:
        report, hourly = inspect_dataset(
            args.input,
            min_valid_minutes_per_hour=args.min_valid_minutes_per_hour,
            expected_rows=None if args.expected_rows == 0 else args.expected_rows,
        )
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        parser.error(str(exc))

    report_path, hourly_path = Path(args.report_out), Path(args.hourly_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    hourly_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    hourly.to_csv(hourly_path, index=False, date_format="%Y-%m-%dT%H:%M:%S")
    print(json.dumps(report, indent=2))
    print(f"Validation report: {report_path}")
    print(f"Eligible hourly series: {hourly_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
