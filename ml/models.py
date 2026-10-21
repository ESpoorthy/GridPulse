"""ML model wrappers with consistent forecasting interface.

This module provides sklearn model wrappers that follow a common interface
for time-series forecasting. All models handle feature selection and provide
consistent predict() methods.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression


class SklearnForecaster:
    """
    Wrapper for sklearn models to provide consistent forecasting interface.
    
    This wrapper handles feature selection, validation, and prediction for
    any sklearn-compatible regressor.
    
    Parameters
    ----------
    model : sklearn estimator
        Any sklearn regressor with fit() and predict() methods.
    feature_cols : list of str
        Feature column names to use for training and prediction.
    name : str
        Human-readable model name for logging and reporting.
    
    Attributes
    ----------
    model : sklearn estimator
        The wrapped sklearn model.
    feature_cols : list of str
        Feature columns used by this model.
    name : str
        Model name.
    is_fitted_ : bool
        Whether the model has been fitted.
    
    Examples
    --------
    >>> from sklearn.linear_model import LinearRegression
    >>> import pandas as pd
    >>> import numpy as np
    >>> X = pd.DataFrame({'feat1': [1, 2, 3], 'feat2': [4, 5, 6]})
    >>> y = pd.Series([10, 20, 30])
    >>> model = SklearnForecaster(LinearRegression(), ['feat1', 'feat2'], 'LR')
    >>> model.fit(X, y)
    >>> model.predict(X)  # doctest: +SKIP
    array([10., 20., 30.])
    """
    
    def __init__(
        self,
        model,
        feature_cols: list[str],
        name: str,
    ):
        """Initialize sklearn forecaster wrapper."""
        self.model = model
        self.feature_cols = feature_cols
        self.name = name
        self.is_fitted_ = False
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> SklearnForecaster:
        """
        Fit the sklearn model on selected features.
        
        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix containing at least self.feature_cols.
        y : pd.Series
            Target values.
        
        Returns
        -------
        self
        
        Raises
        ------
        ValueError
            If required features are missing or data contains NaN.
        """
        # Validate features
        missing_features = [c for c in self.feature_cols if c not in X.columns]
        if missing_features:
            raise ValueError(
                f"Missing required features for {self.name}: {missing_features}"
            )
        
        # Select features
        X_selected = X[self.feature_cols]
        
        # Check for NaN
        if X_selected.isna().any().any():
            raise ValueError(
                f"Feature matrix contains NaN values. "
                f"Drop or impute missing values before fitting {self.name}."
            )
        if y.isna().any():
            raise ValueError(
                f"Target contains NaN values. "
                f"Drop missing targets before fitting {self.name}."
            )
        
        # Fit model
        self.model.fit(X_selected, y)
        self.is_fitted_ = True
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Generate predictions using the fitted model.
        
        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix containing at least self.feature_cols.
        
        Returns
        -------
        np.ndarray
            Model predictions.
        
        Raises
        ------
        ValueError
            If model not fitted or required features missing.
        """
        if not self.is_fitted_:
            raise ValueError(f"{self.name} must be fitted before predict()")
        
        # Validate features
        missing_features = [c for c in self.feature_cols if c not in X.columns]
        if missing_features:
            raise ValueError(
                f"Missing required features for {self.name}: {missing_features}"
            )
        
        # Select features
        X_selected = X[self.feature_cols]
        
        # Check for NaN
        if X_selected.isna().any().any():
            raise ValueError(
                f"Feature matrix contains NaN values. "
                f"Handle missing values before predicting with {self.name}."
            )
        
        return self.model.predict(X_selected)


def create_linear_regression(feature_cols: list[str]) -> SklearnForecaster:
    """
    Create a Linear Regression forecaster.
    
    Linear regression provides a transparent baseline that uses all engineered
    features linearly. It's interpretable and fast to train.
    
    Parameters
    ----------
    feature_cols : list of str
        Feature columns to use.
    
    Returns
    -------
    SklearnForecaster
        Wrapped Linear Regression model.
    
    Examples
    --------
    >>> model = create_linear_regression(['feat1', 'feat2'])
    >>> model.name
    'LinearRegression'
    """
    return SklearnForecaster(
        model=LinearRegression(),
        feature_cols=feature_cols,
        name="LinearRegression",
    )


def create_random_forest(
    feature_cols: list[str],
    n_estimators: int = 100,
    max_depth: int | None = None,
    min_samples_split: int = 2,
    random_state: int = 42,
) -> SklearnForecaster:
    """
    Create a Random Forest forecaster.
    
    Random Forest captures non-linear relationships and feature interactions
    through an ensemble of decision trees. It's robust and often performs well
    out-of-the-box.
    
    Parameters
    ----------
    feature_cols : list of str
        Feature columns to use.
    n_estimators : int, default 100
        Number of trees in the forest.
    max_depth : int or None, default None
        Maximum tree depth (None = no limit).
    min_samples_split : int, default 2
        Minimum samples required to split a node.
    random_state : int, default 42
        Random seed for reproducibility.
    
    Returns
    -------
    SklearnForecaster
        Wrapped Random Forest model.
    
    Examples
    --------
    >>> model = create_random_forest(['feat1'], n_estimators=50)
    >>> model.name
    'RandomForest'
    """
    return SklearnForecaster(
        model=RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            random_state=random_state,
            n_jobs=1,  # Keep experiments reproducible and avoid uncontrolled worker pools
        ),
        feature_cols=feature_cols,
        name="RandomForest",
    )


def create_hist_gradient_boosting(
    feature_cols: list[str],
    max_iter: int = 100,
    max_depth: int | None = None,
    learning_rate: float = 0.1,
    random_state: int = 42,
) -> SklearnForecaster:
    """
    Create a Histogram-based Gradient Boosting forecaster.
    
    HistGradientBoosting is faster than traditional gradient boosting and
    handles missing values natively. It builds trees sequentially to minimize
    prediction error.
    
    Parameters
    ----------
    feature_cols : list of str
        Feature columns to use.
    max_iter : int, default 100
        Number of boosting iterations (trees).
    max_depth : int or None, default None
        Maximum tree depth (None = no limit).
    learning_rate : float, default 0.1
        Learning rate / shrinkage factor.
    random_state : int, default 42
        Random seed for reproducibility.
    
    Returns
    -------
    SklearnForecaster
        Wrapped HistGradientBoosting model.
    
    Examples
    --------
    >>> model = create_hist_gradient_boosting(['feat1'], max_iter=50)
    >>> model.name
    'HistGradientBoosting'
    """
    return SklearnForecaster(
        model=HistGradientBoostingRegressor(
            max_iter=max_iter,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state,
        ),
        feature_cols=feature_cols,
        name="HistGradientBoosting",
    )
