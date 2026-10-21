"""Leakage-safe time-series feature engineering for energy forecasting.

This module implements calendar, lag, and rolling features with strict temporal
guarantees: features at timestamp T use only observations strictly before T.

Key principles:
- Rolling features are shifted so they never include the current target hour
- Lag features reference historical observations only
- Calendar features are known in advance and never leak future information
- Missing values are preserved and documented; rows are not silently dropped
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def build_features(
    df: pd.DataFrame,
    *,
    timestamp_col: str = "timestamp",
    target_col: str = "global_active_power_mean_kw",
    lag_hours: list[int] | None = None,
    rolling_windows: list[int] | None = None,
) -> pd.DataFrame:
    """
    Build calendar, lag, and rolling features from hourly time series.
    
    This function creates features suitable for predicting the target at each
    timestamp using only information available before that timestamp.
    
    **IMPORTANT:** The function ensures time-based correctness by reindexing the
    input to a complete hourly range from min to max timestamp. Any gaps in the
    input timestamps are filled with NaN in the target, ensuring lag_Nh always
    references exactly N hours ago, not N positions ago.
    
    Parameters
    ----------
    df : pd.DataFrame
        Hourly series with at least timestamp and target columns.
        Timestamps need not be continuous; gaps are handled automatically.
        Duplicate timestamps will raise ValueError.
    timestamp_col : str, default "timestamp"
        Name of timestamp column (must be datetime64 dtype).
    target_col : str, default "global_active_power_mean_kw"
        Name of target column to create lag and rolling features from.
    lag_hours : list of int, optional
        List of lag offsets to create (e.g., [1, 2, 3, 24, 48, 168]).
        Default: [1, 2, 3, 24, 48, 168]
    rolling_windows : list of int, optional
        List of window sizes for rolling statistics (e.g., [3, 24, 168]).
        Default: [3, 24, 168]
    
    Returns
    -------
    pd.DataFrame
        Complete hourly series from min to max timestamp with feature columns.
        Rows for missing hours in input have NaN target and propagated NaN features.
        Output length may exceed input length if gaps are filled.
    
    Features Created
    ----------------
    Calendar features (known in advance, never missing):
    - hour_of_day: 0-23
    - day_of_week: 0-6 (Monday=0)
    - is_weekend: 1 if Saturday/Sunday, 0 otherwise
    - month: 1-12
    - hour_sin, hour_cos: cyclical encoding of hour (period=24)
    - dow_sin, dow_cos: cyclical encoding of day of week (period=7)
    
    Lag features (historical observations):
    - lag_{N}h: target value exactly N hours before current timestamp
    
    Rolling features (historical statistics, excluding current hour):
    - rolling_mean_{N}h: mean of target over last N hours (not including current)
    - rolling_std_{N}h: std of target over last N hours (not including current)
    
    Leakage Prevention
    ------------------
    - Rolling features use full windows (min_periods=window) and shift(1).
      At hour H, rolling_mean_24h uses hours [H-24, H-1], never hour H.
    - Lag features reference time-based history: lag_1h at 10:00 references 09:00.
    - Calendar features are derived from timestamp only.
    - Hourly reindexing ensures lag_Nh is exactly N hours ago, not N positions.
    
    Missing Values
    --------------
    - Initial hours lack sufficient history:
      * lag_Nh: first N hours are NaN
      * rolling_mean_Nh: first N hours are NaN (requires full window)
      * rolling_std_Nh: first N hours are NaN
    - Gaps in input timestamps: filled hours have NaN target, propagate to features
    - Missing target values propagate to lag and rolling features
    - Caller must decide how to handle NaN (drop, impute, use subset of features)
    
    Raises
    ------
    ValueError
        If timestamp_col is not datetime64 dtype.
        If required columns are missing.
        If dataframe is empty.
        If duplicate timestamps are present.
    
    Examples
    --------
    >>> hourly = pd.DataFrame({
    ...     'timestamp': pd.date_range('2007-01-01', periods=200, freq='h'),
    ...     'global_active_power_mean_kw': np.random.rand(200) + 1.0,
    ... })
    >>> features = build_features(hourly, lag_hours=[1, 24], rolling_windows=[24])
    >>> # Output has complete hourly index with 24 NaN rows for lag_24h/rolling_24h
    """
    if lag_hours is None:
        lag_hours = [1, 2, 3, 24, 48, 168]
    if rolling_windows is None:
        rolling_windows = [3, 24, 168]
    
    # Validation
    if df.empty:
        raise ValueError("Input dataframe is empty.")
    if timestamp_col not in df.columns:
        raise ValueError(f"Timestamp column '{timestamp_col}' not found in dataframe.")
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe.")
    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
        raise ValueError(
            f"Timestamp column '{timestamp_col}' must be datetime64 dtype, "
            f"got {df[timestamp_col].dtype}."
        )
    
    # Create a copy to avoid modifying input
    result = df.copy()
    
    # Ensure chronological order (required for lag/rolling correctness)
    result = result.sort_values(timestamp_col).reset_index(drop=True)
    
    # Check for duplicate timestamps
    if result[timestamp_col].duplicated().any():
        dup_count = result[timestamp_col].duplicated().sum()
        raise ValueError(
            f"Input contains {dup_count} duplicate timestamp(s). "
            "Each timestamp must be unique. Remove duplicates before feature engineering."
        )
    
    # Reindex to complete hourly range to ensure time-based lag correctness
    # This makes any gaps explicit as NaN rows, ensuring lag_Nh references exactly N hours ago
    ts_min = result[timestamp_col].min()
    ts_max = result[timestamp_col].max()
    complete_hourly_index = pd.date_range(
        start=ts_min,
        end=ts_max,
        freq='h',
        tz=result[timestamp_col].dt.tz  # Preserve timezone if present
    )
    
    # Reindex: missing hours filled with NaN in target column
    result = result.set_index(timestamp_col).reindex(complete_hourly_index).reset_index()
    result = result.rename(columns={'index': timestamp_col})
    
    # Extract timestamp as series for feature creation
    ts = result[timestamp_col]
    target = result[target_col]
    
    # ========================================================================
    # Calendar features (known in advance)
    # ========================================================================
    result["hour_of_day"] = ts.dt.hour
    result["day_of_week"] = ts.dt.dayofweek  # Monday=0, Sunday=6
    result["is_weekend"] = (ts.dt.dayofweek >= 5).astype(int)
    result["month"] = ts.dt.month
    
    # Cyclical encodings for periodic features
    # Hour of day: 24-hour period
    hour_rad = 2 * np.pi * ts.dt.hour / 24.0
    result["hour_sin"] = np.sin(hour_rad)
    result["hour_cos"] = np.cos(hour_rad)
    
    # Day of week: 7-day period
    dow_rad = 2 * np.pi * ts.dt.dayofweek / 7.0
    result["dow_sin"] = np.sin(dow_rad)
    result["dow_cos"] = np.cos(dow_rad)
    
    # ========================================================================
    # Lag features (historical observations)
    # ========================================================================
    for lag in sorted(lag_hours):
        if lag < 1:
            raise ValueError(f"Lag must be >= 1, got {lag}.")
        result[f"lag_{lag}h"] = target.shift(lag)
    
    # ========================================================================
    # Rolling features (historical statistics, excluding current hour)
    # ========================================================================
    # Key: compute rolling stats on target, then shift(1) to exclude current hour
    for window in sorted(rolling_windows):
        if window < 1:
            raise ValueError(f"Rolling window must be >= 1, got {window}.")
        
        # Compute rolling stats with min_periods=window (require full window)
        # This ensures early hours without sufficient history have NaN
        rolling_obj = target.rolling(window=window, min_periods=window)
        rolling_mean = rolling_obj.mean()
        rolling_std = rolling_obj.std()
        
        # Shift to exclude current hour: at time T, feature = stats of [T-window, T-1]
        result[f"rolling_mean_{window}h"] = rolling_mean.shift(1)
        result[f"rolling_std_{window}h"] = rolling_std.shift(1)
    
    return result


def build_feature_row(
    timestamp: pd.Timestamp,
    target_history: list[float] | np.ndarray,
    *,
    lag_hours: list[int] | None = None,
    rolling_windows: list[int] | None = None,
) -> pd.DataFrame:
    """Build one future feature row from prior targets only."""
    values = np.asarray(target_history, dtype=float).reshape(1, -1)
    return build_feature_rows(
        pd.DatetimeIndex([pd.Timestamp(timestamp)]), values,
        lag_hours=lag_hours, rolling_windows=rolling_windows,
    )


def build_feature_rows(
    timestamps: pd.DatetimeIndex,
    target_histories: np.ndarray,
    *,
    lag_hours: list[int] | None = None,
    rolling_windows: list[int] | None = None,
) -> pd.DataFrame:
    """Vectorized future feature rows from equally sized prior target windows."""
    if lag_hours is None:
        lag_hours = [1, 2, 3, 24, 48, 168]
    if rolling_windows is None:
        rolling_windows = [3, 24, 168]
    timestamps = pd.DatetimeIndex(timestamps)
    values = np.asarray(target_histories, dtype=float)
    if values.ndim != 2 or len(values) != len(timestamps):
        raise ValueError("target_histories must be a 2D array with one row per timestamp")
    ts = pd.Series(timestamps)
    hour, day = ts.dt.hour.to_numpy(), ts.dt.dayofweek.to_numpy()
    rows: dict[str, np.ndarray] = {
        "hour_of_day": hour,
        "day_of_week": day,
        "is_weekend": (day >= 5).astype(int),
        "month": ts.dt.month.to_numpy(),
        "hour_sin": np.sin(2 * np.pi * hour / 24.0),
        "hour_cos": np.cos(2 * np.pi * hour / 24.0),
        "dow_sin": np.sin(2 * np.pi * day / 7.0),
        "dow_cos": np.cos(2 * np.pi * day / 7.0),
    }
    for lag in sorted(lag_hours):
        if lag < 1:
            raise ValueError(f"Lag must be >= 1, got {lag}.")
        rows[f"lag_{lag}h"] = values[:, -lag] if values.shape[1] >= lag else np.full(len(values), np.nan)
    for window in sorted(rolling_windows):
        if window < 1:
            raise ValueError(f"Rolling window must be >= 1, got {window}.")
        recent = values[:, -window:]
        if recent.shape[1] < window:
            mean = std = np.full(len(values), np.nan)
        else:
            valid = np.isfinite(recent).all(axis=1)
            mean = np.where(valid, np.mean(recent, axis=1), np.nan)
            std = np.where(valid, np.std(recent, axis=1, ddof=1) if window > 1 else np.nan, np.nan)
        rows[f"rolling_mean_{window}h"] = mean
        rows[f"rolling_std_{window}h"] = std
    return pd.DataFrame(rows, index=timestamps.rename("timestamp"))


def get_feature_columns(
    lag_hours: list[int] | None = None,
    rolling_windows: list[int] | None = None,
) -> dict[str, list[str]]:
    """
    Return dictionary of feature column names by category.
    
    Useful for selecting feature subsets and understanding feature types.
    
    Parameters
    ----------
    lag_hours : list of int, optional
        Lag offsets. Default: [1, 2, 3, 24, 48, 168]
    rolling_windows : list of int, optional
        Rolling window sizes. Default: [3, 24, 168]
    
    Returns
    -------
    dict with keys:
        'calendar': Calendar features (hour, day, month, cyclical encodings)
        'lag': Lag features
        'rolling': Rolling statistics features
        'all': All feature columns (calendar + lag + rolling)
    
    Examples
    --------
    >>> cols = get_feature_columns(lag_hours=[1, 24], rolling_windows=[24])
    >>> cols['calendar']
    ['hour_of_day', 'day_of_week', 'is_weekend', 'month', 'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos']
    >>> cols['lag']
    ['lag_1h', 'lag_24h']
    >>> cols['rolling']
    ['rolling_mean_24h', 'rolling_std_24h']
    """
    if lag_hours is None:
        lag_hours = [1, 2, 3, 24, 48, 168]
    if rolling_windows is None:
        rolling_windows = [3, 24, 168]
    
    calendar = [
        "hour_of_day",
        "day_of_week",
        "is_weekend",
        "month",
        "hour_sin",
        "hour_cos",
        "dow_sin",
        "dow_cos",
    ]
    
    lag = [f"lag_{h}h" for h in sorted(lag_hours)]
    
    rolling = []
    for w in sorted(rolling_windows):
        rolling.append(f"rolling_mean_{w}h")
        rolling.append(f"rolling_std_{w}h")
    
    all_features = calendar + lag + rolling
    
    return {
        "calendar": calendar,
        "lag": lag,
        "rolling": rolling,
        "all": all_features,
    }


def count_missing_features(
    df: pd.DataFrame,
    feature_cols: list[str],
) -> dict[str, int]:
    """
    Count missing values in feature columns.
    
    Parameters
    ----------
    df : pd.DataFrame
        Feature dataframe
    feature_cols : list of str
        Feature column names to check
    
    Returns
    -------
    dict[str, int]
        Mapping of column name to count of missing (NaN) values.
    
    Examples
    --------
    >>> df = pd.DataFrame({'lag_1h': [np.nan, 1.0, 2.0], 'lag_24h': [np.nan] * 3})
    >>> count_missing_features(df, ['lag_1h', 'lag_24h'])
    {'lag_1h': 1, 'lag_24h': 3}
    """
    missing = {}
    for col in feature_cols:
        if col in df.columns:
            missing[col] = int(df[col].isna().sum())
        else:
            missing[col] = len(df)  # Column doesn't exist = all missing
    return missing
