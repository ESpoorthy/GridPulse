"""Chronological train/val/test splitting and evaluation metrics.

This module implements time-series evaluation with strict chronological ordering
to prevent temporal leakage. Train data always precedes validation, which precedes test.
"""
from __future__ import annotations

from typing import NamedTuple

import numpy as np
import pandas as pd


class DataSplit(NamedTuple):
    """Chronological data split with train, validation, and test sets."""
    
    train_X: pd.DataFrame
    train_y: pd.Series
    val_X: pd.DataFrame
    val_y: pd.Series
    test_X: pd.DataFrame
    test_y: pd.Series
    train_end_idx: int
    val_end_idx: int


def chronological_split(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: list[str],
    train_frac: float = 0.7,
    val_frac: float = 0.15,
    drop_na: bool = True,
) -> DataSplit:
    """
    Split time-series data chronologically into train, validation, and test sets.
    
    The split preserves temporal order: all training data comes before validation,
    which comes before test. This prevents temporal leakage where future information
    influences past predictions.
    
    Parameters
    ----------
    df : pd.DataFrame
        Time-series dataframe with features and target. Must be sorted chronologically.
    target_col : str
        Name of the target column.
    feature_cols : list of str
        Names of feature columns to use for training.
    train_frac : float, default 0.7
        Fraction of data for training (0 < train_frac < 1).
    val_frac : float, default 0.15
        Fraction of data for validation (0 < val_frac < 1).
        Test fraction is implicitly 1 - train_frac - val_frac.
    drop_na : bool, default True
        If True, drop rows with NaN in features or target before splitting.
        If False, keep NaN rows (caller must handle).
    
    Returns
    -------
    DataSplit
        Named tuple with train/val/test X and y, plus split indices.
    
    Raises
    ------
    ValueError
        If fractions don't sum to < 1, columns missing, or insufficient data.
    
    Notes
    -----
    - Dropping NaN is done before splitting to ensure consistent split boundaries
    - Split indices refer to the cleaned dataframe (after dropping NaN)
    - Minimum of 1 row per split required
    
    Examples
    --------
    >>> df = pd.DataFrame({
    ...     'timestamp': pd.date_range('2007-01-01', periods=100, freq='h'),
    ...     'target': np.arange(100),
    ...     'feat1': np.arange(100),
    ... })
    >>> split = chronological_split(df, 'target', ['feat1'], 0.7, 0.15)
    >>> len(split.train_X), len(split.val_X), len(split.test_X)
    (70, 15, 15)
    """
    # Validation
    if train_frac <= 0 or train_frac >= 1:
        raise ValueError(f"train_frac must be in (0, 1), got {train_frac}")
    if val_frac <= 0 or val_frac >= 1:
        raise ValueError(f"val_frac must be in (0, 1), got {val_frac}")
    if train_frac + val_frac >= 1:
        raise ValueError(
            f"train_frac + val_frac must be < 1, got {train_frac + val_frac}"
        )
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe")
    
    missing_features = [c for c in feature_cols if c not in df.columns]
    if missing_features:
        raise ValueError(
            f"Feature columns not found: {missing_features}"
        )
    
    # Prepare data
    data = df.copy()
    
    # Drop rows with NaN if requested
    if drop_na:
        relevant_cols = [target_col] + feature_cols
        data = data.dropna(subset=relevant_cols).reset_index(drop=True)
    
    if len(data) == 0:
        raise ValueError("No valid rows after dropping NaN")
    
    # Calculate split indices
    n = len(data)
    train_end = int(n * train_frac)
    val_end = int(n * (train_frac + val_frac))
    
    # Ensure at least 1 row per split
    if train_end < 1 or val_end <= train_end or n <= val_end:
        raise ValueError(
            f"Insufficient data for split: n={n}, train_end={train_end}, "
            f"val_end={val_end}. Need at least {int(1/(1-train_frac-val_frac)) + 2} rows."
        )
    
    # Split chronologically
    train_X = data.loc[:train_end-1, feature_cols]
    train_y = data.loc[:train_end-1, target_col]
    
    val_X = data.loc[train_end:val_end-1, feature_cols]
    val_y = data.loc[train_end:val_end-1, target_col]
    
    test_X = data.loc[val_end:, feature_cols]
    test_y = data.loc[val_end:, target_col]
    
    return DataSplit(
        train_X=train_X,
        train_y=train_y,
        val_X=val_X,
        val_y=val_y,
        test_X=test_X,
        test_y=test_y,
        train_end_idx=train_end,
        val_end_idx=val_end,
    )


def calculate_metrics(
    y_true: np.ndarray | pd.Series,
    y_pred: np.ndarray | pd.Series,
) -> dict[str, float]:
    """
    Calculate regression metrics: MAE and RMSE.
    
    Parameters
    ----------
    y_true : array-like
        True target values.
    y_pred : array-like
        Predicted values.
    
    Returns
    -------
    dict[str, float]
        Dictionary with 'mae' and 'rmse' keys.
    
    Raises
    ------
    ValueError
        If inputs have different lengths or contain only NaN.
    
    Examples
    --------
    >>> y_true = np.array([1.0, 2.0, 3.0])
    >>> y_pred = np.array([1.1, 2.1, 2.9])
    >>> metrics = calculate_metrics(y_true, y_pred)
    >>> metrics['mae']  # doctest: +SKIP
    0.1
    """
    # Convert to numpy arrays
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    
    # Validation
    if y_true.shape != y_pred.shape:
        raise ValueError(
            f"Shape mismatch: y_true has shape {y_true.shape}, "
            f"y_pred has shape {y_pred.shape}"
        )
    
    if len(y_true) == 0:
        raise ValueError("Cannot compute metrics on empty arrays")
    
    # Remove NaN pairs (both must be NaN to skip)
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true_clean = y_true[mask]
    y_pred_clean = y_pred[mask]
    
    if len(y_true_clean) == 0:
        raise ValueError("No valid (non-NaN) pairs to compute metrics")
    
    # Calculate metrics
    errors = y_true_clean - y_pred_clean
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    
    return {
        "mae": mae,
        "rmse": rmse,
    }
