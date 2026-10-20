"""Tests for baseline forecasting models."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.baselines import PersistenceBaseline, SeasonalNaiveBaseline


class TestPersistenceBaseline:
    """Test persistence (naive) baseline model."""
    
    def test_returns_lag_1h_values(self):
        """Persistence should return lag_1h as predictions."""
        X = pd.DataFrame({
            "lag_1h": [10.0, 20.0, 30.0],
            "other_feat": [1.0, 2.0, 3.0],
        })
        
        model = PersistenceBaseline()
        model.fit(X, None)  # No-op
        predictions = model.predict(X)
        
        np.testing.assert_array_equal(predictions, [10.0, 20.0, 30.0])
    
    def test_fit_is_noop(self):
        """Fit should not change model state."""
        X = pd.DataFrame({"lag_1h": [1.0, 2.0]})
        y = pd.Series([10.0, 20.0])
        
        model = PersistenceBaseline()
        result = model.fit(X, y)
        
        # Should return self
        assert result is model
        
        # Should still work after fitting
        predictions = model.predict(X)
        np.testing.assert_array_equal(predictions, [1.0, 2.0])
    
    def test_predict_without_fit(self):
        """Should work without calling fit (stateless)."""
        X = pd.DataFrame({"lag_1h": [5.0, 15.0, 25.0]})
        
        model = PersistenceBaseline()
        predictions = model.predict(X)
        
        np.testing.assert_array_equal(predictions, [5.0, 15.0, 25.0])
    
    def test_requires_lag_1h_feature(self):
        """Should raise error if lag_1h feature missing."""
        X = pd.DataFrame({"other_feat": [1.0, 2.0, 3.0]})
        
        model = PersistenceBaseline()
        with pytest.raises(ValueError, match="requires 'lag_1h' feature"):
            model.predict(X)
    
    def test_preserves_nan_values(self):
        """Should preserve NaN values in lag_1h."""
        X = pd.DataFrame({"lag_1h": [10.0, np.nan, 30.0]})
        
        model = PersistenceBaseline()
        predictions = model.predict(X)
        
        assert predictions[0] == 10.0
        assert np.isnan(predictions[1])
        assert predictions[2] == 30.0


class TestSeasonalNaiveBaseline:
    """Test seasonal naive baseline model."""
    
    def test_daily_seasonality_default(self):
        """Default seasonal period should be 24 hours (daily)."""
        model = SeasonalNaiveBaseline()
        assert model.seasonal_period == 24
    
    def test_returns_lag_24h_for_daily(self):
        """Daily seasonal naive should return lag_24h values."""
        X = pd.DataFrame({
            "lag_24h": [10.0, 20.0, 30.0],
            "lag_1h": [1.0, 2.0, 3.0],
        })
        
        model = SeasonalNaiveBaseline(seasonal_period=24)
        model.fit(X, None)  # No-op
        predictions = model.predict(X)
        
        np.testing.assert_array_equal(predictions, [10.0, 20.0, 30.0])
    
    def test_weekly_seasonality(self):
        """Weekly seasonal naive should return lag_168h values."""
        X = pd.DataFrame({
            "lag_168h": [100.0, 200.0, 300.0],
            "lag_24h": [10.0, 20.0, 30.0],
        })
        
        model = SeasonalNaiveBaseline(seasonal_period=168)
        predictions = model.predict(X)
        
        np.testing.assert_array_equal(predictions, [100.0, 200.0, 300.0])
    
    def test_custom_seasonal_period(self):
        """Should support custom seasonal periods."""
        X = pd.DataFrame({
            "lag_12h": [5.0, 10.0, 15.0],
            "lag_24h": [1.0, 2.0, 3.0],
        })
        
        model = SeasonalNaiveBaseline(seasonal_period=12)
        predictions = model.predict(X)
        
        np.testing.assert_array_equal(predictions, [5.0, 10.0, 15.0])
    
    def test_fit_is_noop(self):
        """Fit should not change model state."""
        X = pd.DataFrame({"lag_24h": [1.0, 2.0]})
        y = pd.Series([10.0, 20.0])
        
        model = SeasonalNaiveBaseline()
        result = model.fit(X, y)
        
        assert result is model
    
    def test_predict_without_fit(self):
        """Should work without calling fit (stateless)."""
        X = pd.DataFrame({"lag_24h": [50.0, 100.0]})
        
        model = SeasonalNaiveBaseline()
        predictions = model.predict(X)
        
        np.testing.assert_array_equal(predictions, [50.0, 100.0])
    
    def test_requires_correct_lag_feature(self):
        """Should raise error if required lag feature missing."""
        X = pd.DataFrame({"lag_1h": [1.0, 2.0]})
        
        model = SeasonalNaiveBaseline(seasonal_period=24)
        with pytest.raises(ValueError, match="requires 'lag_24h' feature"):
            model.predict(X)
    
    def test_rejects_invalid_period(self):
        """Should raise error for invalid seasonal period."""
        with pytest.raises(ValueError, match="seasonal_period must be >= 1"):
            SeasonalNaiveBaseline(seasonal_period=0)
        
        with pytest.raises(ValueError, match="seasonal_period must be >= 1"):
            SeasonalNaiveBaseline(seasonal_period=-1)
    
    def test_preserves_nan_values(self):
        """Should preserve NaN values in lag feature."""
        X = pd.DataFrame({"lag_24h": [10.0, np.nan, 30.0]})
        
        model = SeasonalNaiveBaseline()
        predictions = model.predict(X)
        
        assert predictions[0] == 10.0
        assert np.isnan(predictions[1])
        assert predictions[2] == 30.0
