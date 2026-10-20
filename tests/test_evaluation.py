"""Tests for chronological evaluation and metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.evaluation import DataSplit, calculate_metrics, chronological_split


class TestChronologicalSplit:
    """Test chronological train/val/test splitting."""
    
    def test_basic_split_with_defaults(self):
        """Default 70/15/15 split should work correctly."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=100, freq="h"),
            "target": np.arange(100, dtype=float),
            "feat1": np.arange(100, dtype=float),
        })
        
        split = chronological_split(df, "target", ["feat1"])
        
        # Check sizes
        assert len(split.train_X) == 70
        assert len(split.val_X) == 15
        assert len(split.test_X) == 15
        
        # Check shapes match
        assert len(split.train_y) == len(split.train_X)
        assert len(split.val_y) == len(split.val_X)
        assert len(split.test_y) == len(split.test_X)
    
    def test_chronological_ordering(self):
        """Train data must precede validation, which must precede test."""
        df = pd.DataFrame({
            "target": np.arange(100, dtype=float),
            "feat1": np.arange(100, dtype=float),
        })
        
        split = chronological_split(df, "target", ["feat1"], 0.6, 0.2)
        
        # Train: 0-59, Val: 60-79, Test: 80-99
        assert split.train_y.iloc[0] == 0
        assert split.train_y.iloc[-1] == 59
        assert split.val_y.iloc[0] == 60
        assert split.val_y.iloc[-1] == 79
        assert split.test_y.iloc[0] == 80
        assert split.test_y.iloc[-1] == 99
    
    def test_no_temporal_leakage(self):
        """No future data should appear in training set."""
        df = pd.DataFrame({
            "target": np.arange(100, dtype=float),
            "feat1": np.arange(100, dtype=float),
        })
        
        split = chronological_split(df, "target", ["feat1"])
        
        # Maximum training target should be less than minimum validation target
        assert split.train_y.max() < split.val_y.min()
        # Maximum validation target should be less than minimum test target
        assert split.val_y.max() < split.test_y.min()
    
    def test_custom_split_ratios(self):
        """Should respect custom split ratios."""
        df = pd.DataFrame({
            "target": np.arange(100, dtype=float),
            "feat1": np.arange(100, dtype=float),
        })
        
        split = chronological_split(df, "target", ["feat1"], 0.6, 0.2)
        
        assert len(split.train_X) == 60
        assert len(split.val_X) == 20
        assert len(split.test_X) == 20
    
    def test_drops_nan_by_default(self):
        """Should drop rows with NaN by default."""
        df = pd.DataFrame({
            "target": [1.0, np.nan, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "feat1": [1.0, 2.0, np.nan, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        })
        
        split = chronological_split(df, "target", ["feat1"])
        
        # Should have 8 rows after dropping 2 NaN rows
        total = len(split.train_X) + len(split.val_X) + len(split.test_X)
        assert total == 8
        
        # No NaN in any split
        assert not split.train_X["feat1"].isna().any()
        assert not split.train_y.isna().any()
        assert not split.val_X["feat1"].isna().any()
        assert not split.val_y.isna().any()
    
    def test_keeps_nan_when_drop_na_false(self):
        """Should keep NaN when drop_na=False."""
        df = pd.DataFrame({
            "target": [1.0, np.nan, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "feat1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        })
        
        split = chronological_split(df, "target", ["feat1"], drop_na=False)
        
        # Should have all 10 rows
        total = len(split.train_X) + len(split.val_X) + len(split.test_X)
        assert total == 10
        
        # Training set should contain the NaN
        assert split.train_y.isna().any()
    
    def test_selects_only_requested_features(self):
        """Should only include requested feature columns."""
        df = pd.DataFrame({
            "target": np.arange(100, dtype=float),
            "feat1": np.arange(100, dtype=float),
            "feat2": np.arange(100, dtype=float),
            "feat3": np.arange(100, dtype=float),
        })
        
        split = chronological_split(df, "target", ["feat1", "feat3"])
        
        assert list(split.train_X.columns) == ["feat1", "feat3"]
        assert "feat2" not in split.train_X.columns
    
    def test_rejects_invalid_fractions(self):
        """Should raise error for invalid split fractions."""
        df = pd.DataFrame({
            "target": np.arange(100, dtype=float),
            "feat1": np.arange(100, dtype=float),
        })
        
        # train_frac >= 1
        with pytest.raises(ValueError, match="train_frac must be in"):
            chronological_split(df, "target", ["feat1"], train_frac=1.0)
        
        # train_frac <= 0
        with pytest.raises(ValueError, match="train_frac must be in"):
            chronological_split(df, "target", ["feat1"], train_frac=0.0)
        
        # Sum >= 1
        with pytest.raises(ValueError, match="train_frac \\+ val_frac must be < 1"):
            chronological_split(df, "target", ["feat1"], train_frac=0.8, val_frac=0.3)
    
    def test_rejects_missing_columns(self):
        """Should raise error if target or features missing."""
        df = pd.DataFrame({
            "target": np.arange(100, dtype=float),
            "feat1": np.arange(100, dtype=float),
        })
        
        # Missing target
        with pytest.raises(ValueError, match="Target column.*not found"):
            chronological_split(df, "missing_target", ["feat1"])
        
        # Missing features
        with pytest.raises(ValueError, match="Feature columns not found"):
            chronological_split(df, "target", ["feat1", "missing_feat"])
    
    def test_rejects_insufficient_data(self):
        """Should raise error if insufficient data for split."""
        df = pd.DataFrame({
            "target": [1.0, 2.0],
            "feat1": [1.0, 2.0],
        })
        
        # Too few rows for 70/15/15 split
        with pytest.raises(ValueError, match="Insufficient data"):
            chronological_split(df, "target", ["feat1"])
    
    def test_split_indices_correct(self):
        """Split indices should correctly mark boundaries."""
        df = pd.DataFrame({
            "target": np.arange(100, dtype=float),
            "feat1": np.arange(100, dtype=float),
        })
        
        split = chronological_split(df, "target", ["feat1"])
        
        # train_end_idx should be first validation index
        assert split.train_end_idx == 70
        # val_end_idx should be first test index
        assert split.val_end_idx == 85


class TestCalculateMetrics:
    """Test metric calculations."""
    
    def test_perfect_predictions(self):
        """Perfect predictions should have zero error."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        metrics = calculate_metrics(y_true, y_pred)
        
        assert metrics["mae"] == pytest.approx(0.0)
        assert metrics["rmse"] == pytest.approx(0.0)
    
    def test_known_mae_calculation(self):
        """MAE should match manual calculation."""
        y_true = np.array([10.0, 20.0, 30.0])
        y_pred = np.array([12.0, 19.0, 28.0])
        
        metrics = calculate_metrics(y_true, y_pred)
        
        # Errors: [2, 1, 2], MAE = (2+1+2)/3 = 1.67
        expected_mae = (2.0 + 1.0 + 2.0) / 3
        assert metrics["mae"] == pytest.approx(expected_mae)
    
    def test_known_rmse_calculation(self):
        """RMSE should match manual calculation."""
        y_true = np.array([10.0, 20.0, 30.0])
        y_pred = np.array([12.0, 19.0, 28.0])
        
        metrics = calculate_metrics(y_true, y_pred)
        
        # Errors: [2, 1, 2], RMSE = sqrt((4+1+4)/3) = sqrt(3) = 1.732
        expected_rmse = np.sqrt((4.0 + 1.0 + 4.0) / 3)
        assert metrics["rmse"] == pytest.approx(expected_rmse)
    
    def test_accepts_pandas_series(self):
        """Should accept pandas Series as input."""
        y_true = pd.Series([1.0, 2.0, 3.0])
        y_pred = pd.Series([1.1, 2.1, 2.9])
        
        metrics = calculate_metrics(y_true, y_pred)
        
        assert "mae" in metrics
        assert "rmse" in metrics
    
    def test_handles_nan_pairs(self):
        """Should skip NaN pairs in calculation."""
        y_true = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        y_pred = np.array([1.1, np.nan, 3.0, 4.1, 5.1])
        
        metrics = calculate_metrics(y_true, y_pred)
        
        # Should compute on [1.0, 4.0, 5.0] vs [1.1, 4.1, 5.1]
        # Errors: [0.1, 0.1, 0.1], MAE = 0.1
        assert metrics["mae"] == pytest.approx(0.1)
    
    def test_rejects_shape_mismatch(self):
        """Should raise error if arrays have different shapes."""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0])
        
        with pytest.raises(ValueError, match="Shape mismatch"):
            calculate_metrics(y_true, y_pred)
    
    def test_rejects_empty_arrays(self):
        """Should raise error for empty input."""
        y_true = np.array([])
        y_pred = np.array([])
        
        with pytest.raises(ValueError, match="empty arrays"):
            calculate_metrics(y_true, y_pred)
    
    def test_rejects_all_nan(self):
        """Should raise error if all values are NaN."""
        y_true = np.array([np.nan, np.nan])
        y_pred = np.array([np.nan, np.nan])
        
        with pytest.raises(ValueError, match="No valid.*non-NaN"):
            calculate_metrics(y_true, y_pred)
    
    def test_rmse_penalizes_large_errors(self):
        """RMSE should be larger than MAE when errors vary."""
        # One large error, rest small
        y_true = np.array([10.0, 20.0, 30.0, 40.0])
        y_pred = np.array([10.1, 20.1, 30.1, 50.0])  # Last error is 10
        
        metrics = calculate_metrics(y_true, y_pred)
        
        # MAE = (0.1 + 0.1 + 0.1 + 10) / 4 = 2.575
        # RMSE = sqrt((0.01 + 0.01 + 0.01 + 100) / 4) = 5.0
        assert metrics["rmse"] > metrics["mae"]
        assert metrics["rmse"] == pytest.approx(5.0, rel=0.01)
