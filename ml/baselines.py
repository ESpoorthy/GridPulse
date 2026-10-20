"""Baseline forecasting models for time-series evaluation.

Baseline models provide simple, interpretable benchmarks against which to compare
more complex ML models. A baseline that is hard to beat often indicates the problem
is already well-solved by simple methods.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class PersistenceBaseline:
    """
    Persistence (naive) baseline: predict the last observed value.
    
    This baseline assumes "tomorrow will be like today" and uses lag_1h feature.
    It's the simplest possible forecasting method and often surprisingly effective
    for time series with strong temporal continuity.
    
    Parameters
    ----------
    None
    
    Attributes
    ----------
    None (stateless model)
    
    Examples
    --------
    >>> import pandas as pd
    >>> import numpy as np
    >>> X = pd.DataFrame({'lag_1h': [10.0, 20.0, 30.0]})
    >>> model = PersistenceBaseline()
    >>> model.fit(X, None)  # No-op
    >>> model.predict(X)
    array([10., 20., 30.])
    """
    
    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> PersistenceBaseline:
        """
        Fit persistence baseline (no-op, model is stateless).
        
        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix (not used).
        y : pd.Series, optional
            Target values (not used).
        
        Returns
        -------
        self
        """
        # Stateless model - no fitting required
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict using persistence: return lag_1h values.
        
        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix, must contain 'lag_1h' column.
        
        Returns
        -------
        np.ndarray
            Predictions (copy of lag_1h values).
        
        Raises
        ------
        ValueError
            If 'lag_1h' column not found.
        """
        if "lag_1h" not in X.columns:
            raise ValueError("PersistenceBaseline requires 'lag_1h' feature")
        
        return X["lag_1h"].to_numpy()


class SeasonalNaiveBaseline:
    """
    Seasonal naive baseline: predict the value from N hours ago.
    
    This baseline exploits seasonality by using the observation from the same
    time in a previous cycle (e.g., 24 hours ago for daily patterns, 168 hours
    for weekly patterns).
    
    Parameters
    ----------
    seasonal_period : int, default 24
        Number of hours in the seasonal period (24 for daily, 168 for weekly).
    
    Attributes
    ----------
    seasonal_period : int
        Seasonal period used for predictions.
    
    Examples
    --------
    >>> X = pd.DataFrame({'lag_24h': [10.0, 20.0, 30.0]})
    >>> model = SeasonalNaiveBaseline(seasonal_period=24)
    >>> model.fit(X, None)  # No-op
    >>> model.predict(X)
    array([10., 20., 30.])
    """
    
    def __init__(self, seasonal_period: int = 24):
        """
        Initialize seasonal naive baseline.
        
        Parameters
        ----------
        seasonal_period : int, default 24
            Seasonal period in hours (24 for daily, 168 for weekly).
        """
        if seasonal_period < 1:
            raise ValueError(f"seasonal_period must be >= 1, got {seasonal_period}")
        self.seasonal_period = seasonal_period
    
    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> SeasonalNaiveBaseline:
        """
        Fit seasonal naive baseline (no-op, model is stateless).
        
        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix (not used).
        y : pd.Series, optional
            Target values (not used).
        
        Returns
        -------
        self
        """
        # Stateless model - no fitting required
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict using seasonal naive: return lag_{period}h values.
        
        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix, must contain f'lag_{period}h' column.
        
        Returns
        -------
        np.ndarray
            Predictions (copy of lag_{period}h values).
        
        Raises
        ------
        ValueError
            If required lag column not found.
        """
        lag_col = f"lag_{self.seasonal_period}h"
        if lag_col not in X.columns:
            raise ValueError(
                f"SeasonalNaiveBaseline requires '{lag_col}' feature"
            )
        
        return X[lag_col].to_numpy()
