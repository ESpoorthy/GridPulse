"""Tests for ML model wrappers."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.models import (
    SklearnForecaster,
    create_hist_gradient_boosting,
    create_linear_regression,
    create_random_forest,
)


class TestSklearnForecaster:
    """Test sklearn model wrapper."""
    
    def test_fit_and_predict_basic(self):
        """Should fit and predict with sklearn model."""
        from sklearn.linear_model import LinearRegression
        
        X = pd.DataFrame({"feat1": [1, 2, 3, 4, 5], "feat2": [2, 4, 6, 8, 10]})
        y = pd.Series([10, 20, 30, 40, 50])
        
        model = SklearnForecaster(LinearRegression(), ["feat1", "feat2"], "TestLR")
        model.fit(X, y)
        predictions = model.predict(X)
        
        # Perfect linear relationship, should predict exactly
        np.testing.assert_array_almost_equal(predictions, y, decimal=10)
    
    def test_selects_only_specified_features(self):
        """Should only use specified features, ignore others."""
        from sklearn.linear_model import LinearRegression
        
        X = pd.DataFrame({
            "feat1": [1, 2, 3, 4, 5],
            "feat2": [2, 4, 6, 8, 10],
            "feat3": [100, 200, 300, 400, 500],  # Not used
        })
        y = pd.Series([10, 20, 30, 40, 50])
        
        # Only use feat1, feat2
        model = SklearnForecaster(LinearRegression(), ["feat1", "feat2"], "TestLR")
        model.fit(X, y)
        
        # Should work even with feat3 in prediction data
        predictions = model.predict(X)
        assert len(predictions) == 5
    
    def test_tracks_fitted_state(self):
        """Should track whether model has been fitted."""
        from sklearn.linear_model import LinearRegression
        
        X = pd.DataFrame({"feat1": [1, 2, 3]})
        y = pd.Series([10, 20, 30])
        
        model = SklearnForecaster(LinearRegression(), ["feat1"], "TestLR")
        
        # Not fitted initially
        assert not model.is_fitted_
        
        model.fit(X, y)
        
        # Fitted after fit()
        assert model.is_fitted_
    
    def test_rejects_prediction_before_fit(self):
        """Should raise error if predict called before fit."""
        from sklearn.linear_model import LinearRegression
        
        X = pd.DataFrame({"feat1": [1, 2, 3]})
        
        model = SklearnForecaster(LinearRegression(), ["feat1"], "TestLR")
        
        with pytest.raises(ValueError, match="must be fitted before predict"):
            model.predict(X)
    
    def test_rejects_missing_features_in_fit(self):
        """Should raise error if required features missing during fit."""
        from sklearn.linear_model import LinearRegression
        
        X = pd.DataFrame({"wrong_feat": [1, 2, 3]})
        y = pd.Series([10, 20, 30])
        
        model = SklearnForecaster(LinearRegression(), ["feat1"], "TestLR")
        
        with pytest.raises(ValueError, match="Missing required features"):
            model.fit(X, y)
    
    def test_rejects_missing_features_in_predict(self):
        """Should raise error if required features missing during predict."""
        from sklearn.linear_model import LinearRegression
        
        X_train = pd.DataFrame({"feat1": [1, 2, 3]})
        y_train = pd.Series([10, 20, 30])
        X_test = pd.DataFrame({"wrong_feat": [4, 5]})
        
        model = SklearnForecaster(LinearRegression(), ["feat1"], "TestLR")
        model.fit(X_train, y_train)
        
        with pytest.raises(ValueError, match="Missing required features"):
            model.predict(X_test)
    
    def test_rejects_nan_in_features_during_fit(self):
        """Should raise error if features contain NaN during fit."""
        from sklearn.linear_model import LinearRegression
        
        X = pd.DataFrame({"feat1": [1.0, np.nan, 3.0]})
        y = pd.Series([10, 20, 30])
        
        model = SklearnForecaster(LinearRegression(), ["feat1"], "TestLR")
        
        with pytest.raises(ValueError, match="Feature matrix contains NaN"):
            model.fit(X, y)
    
    def test_rejects_nan_in_target_during_fit(self):
        """Should raise error if target contains NaN during fit."""
        from sklearn.linear_model import LinearRegression
        
        X = pd.DataFrame({"feat1": [1, 2, 3]})
        y = pd.Series([10, np.nan, 30])
        
        model = SklearnForecaster(LinearRegression(), ["feat1"], "TestLR")
        
        with pytest.raises(ValueError, match="Target contains NaN"):
            model.fit(X, y)
    
    def test_rejects_nan_in_features_during_predict(self):
        """Should raise error if features contain NaN during predict."""
        from sklearn.linear_model import LinearRegression
        
        X_train = pd.DataFrame({"feat1": [1, 2, 3]})
        y_train = pd.Series([10, 20, 30])
        X_test = pd.DataFrame({"feat1": [4.0, np.nan]})
        
        model = SklearnForecaster(LinearRegression(), ["feat1"], "TestLR")
        model.fit(X_train, y_train)
        
        with pytest.raises(ValueError, match="Feature matrix contains NaN"):
            model.predict(X_test)


class TestModelCreators:
    """Test model creation functions."""
    
    def test_create_linear_regression(self):
        """Should create Linear Regression forecaster."""
        model = create_linear_regression(["feat1", "feat2"])
        
        assert model.name == "LinearRegression"
        assert model.feature_cols == ["feat1", "feat2"]
        assert not model.is_fitted_
    
    def test_create_random_forest(self):
        """Should create Random Forest forecaster."""
        model = create_random_forest(["feat1"], n_estimators=50)
        
        assert model.name == "RandomForest"
        assert model.feature_cols == ["feat1"]
        assert not model.is_fitted_
    
    def test_create_hist_gradient_boosting(self):
        """Should create HistGradientBoosting forecaster."""
        model = create_hist_gradient_boosting(["feat1", "feat2"], max_iter=50)
        
        assert model.name == "HistGradientBoosting"
        assert model.feature_cols == ["feat1", "feat2"]
        assert not model.is_fitted_
    
    def test_random_forest_reproducible(self):
        """Random Forest with same seed should give same results."""
        X = pd.DataFrame({"feat1": np.random.rand(100)})
        y = pd.Series(np.random.rand(100))
        
        model1 = create_random_forest(["feat1"], n_estimators=10, random_state=42)
        model2 = create_random_forest(["feat1"], n_estimators=10, random_state=42)
        
        model1.fit(X, y)
        model2.fit(X, y)
        
        pred1 = model1.predict(X)
        pred2 = model2.predict(X)
        
        # Allow tiny floating-point differences
        np.testing.assert_array_almost_equal(pred1, pred2, decimal=10)
    
    def test_hist_gradient_boosting_reproducible(self):
        """HistGradientBoosting with same seed should give same results."""
        X = pd.DataFrame({"feat1": np.random.rand(100)})
        y = pd.Series(np.random.rand(100))
        
        model1 = create_hist_gradient_boosting(["feat1"], max_iter=10, random_state=42)
        model2 = create_hist_gradient_boosting(["feat1"], max_iter=10, random_state=42)
        
        model1.fit(X, y)
        model2.fit(X, y)
        
        pred1 = model1.predict(X)
        pred2 = model2.predict(X)
        
        np.testing.assert_array_almost_equal(pred1, pred2, decimal=10)


class TestModelFitting:
    """Test that models can actually fit and predict."""
    
    def test_linear_regression_fits_and_predicts(self):
        """Linear Regression should fit and predict."""
        X = pd.DataFrame({"feat1": [1, 2, 3, 4, 5]})
        y = pd.Series([2, 4, 6, 8, 10])
        
        model = create_linear_regression(["feat1"])
        model.fit(X, y)
        predictions = model.predict(X)
        
        # Perfect linear fit
        np.testing.assert_array_almost_equal(predictions, y, decimal=10)
    
    def test_random_forest_fits_and_predicts(self):
        """Random Forest should fit and predict."""
        X = pd.DataFrame({"feat1": [1, 2, 3, 4, 5]})
        y = pd.Series([2, 4, 6, 8, 10])
        
        model = create_random_forest(["feat1"], n_estimators=10, random_state=42)
        model.fit(X, y)
        predictions = model.predict(X)
        
        # Should predict reasonably close
        assert len(predictions) == 5
        assert np.all(predictions > 0)
    
    def test_hist_gradient_boosting_fits_and_predicts(self):
        """HistGradientBoosting should fit and predict."""
        X = pd.DataFrame({"feat1": [1, 2, 3, 4, 5]})
        y = pd.Series([2, 4, 6, 8, 10])
        
        model = create_hist_gradient_boosting(["feat1"], max_iter=10, random_state=42)
        model.fit(X, y)
        predictions = model.predict(X)
        
        # Should predict reasonably close
        assert len(predictions) == 5
        assert np.all(predictions > 0)
