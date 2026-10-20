"""Tests for leakage-safe feature engineering.

This test suite verifies:
1. Temporal leakage prevention (rolling features exclude current target)
2. Chronological ordering preservation
3. Cyclical encoding correctness
4. Missing value handling and transparency
5. Feature alignment with timestamps
6. Future-perturbation invariance
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from ml.features import build_features, get_feature_columns, count_missing_features


class TestCalendarFeatures:
    """Test calendar feature extraction."""
    
    def test_hour_of_day_extraction(self):
        """Hour of day should be 0-23."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01 00:00", periods=25, freq="h"),
            "global_active_power_mean_kw": np.ones(25),
        })
        result = build_features(df, lag_hours=[], rolling_windows=[])
        
        assert result["hour_of_day"].iloc[0] == 0
        assert result["hour_of_day"].iloc[12] == 12
        assert result["hour_of_day"].iloc[23] == 23
        assert result["hour_of_day"].iloc[24] == 0  # Wraps to next day
    
    def test_day_of_week_extraction(self):
        """Day of week should be 0-6, Monday=0."""
        # 2007-01-01 was a Monday
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=7, freq="D"),
            "global_active_power_mean_kw": np.ones(7),
        })
        result = build_features(df, lag_hours=[], rolling_windows=[])
        
        # With daily frequency, reindexing fills 23 hours between each day
        # We only check the original days (every 24 hours)
        # Row 0 = 2007-01-01 00:00 Monday
        assert result["day_of_week"].iloc[0] == 0  # Monday
        # Row 24 = 2007-01-02 00:00 Tuesday
        assert result["day_of_week"].iloc[24] == 1  # Tuesday
        # Row 120 = 2007-01-06 00:00 Saturday
        assert result["day_of_week"].iloc[120] == 5  # Saturday
        # Row 144 = 2007-01-07 00:00 Sunday
        assert result["day_of_week"].iloc[144] == 6  # Sunday
    
    def test_weekend_indicator(self):
        """Weekend indicator should be 1 for Sat/Sun, 0 otherwise."""
        # 2007-01-01 was Monday
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=7, freq="D"),
            "global_active_power_mean_kw": np.ones(7),
        })
        result = build_features(df, lag_hours=[], rolling_windows=[])
        
        # With daily frequency, reindexing fills hours between days
        assert result["is_weekend"].iloc[0] == 0  # Monday
        assert result["is_weekend"].iloc[96] == 0  # Friday (4*24)
        assert result["is_weekend"].iloc[120] == 1  # Saturday (5*24)
        assert result["is_weekend"].iloc[144] == 1  # Sunday (6*24)
    
    def test_month_extraction(self):
        """Month should be 1-12."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-15", periods=6, freq="ME"),
            "global_active_power_mean_kw": np.ones(6),
        })
        result = build_features(df, lag_hours=[], rolling_windows=[])
        
        # With month-end frequency, reindexing fills all hours between month ends
        # Check the first timestamp (original input)
        first_month = result["month"].iloc[0]
        assert first_month == 1  # January 15th
    
    def test_cyclical_hour_encoding(self):
        """Hour cyclical encoding should have period 24."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01 00:00", periods=25, freq="h"),
            "global_active_power_mean_kw": np.ones(25),
        })
        result = build_features(df, lag_hours=[], rolling_windows=[])
        
        # Hour 0 and hour 24 should encode to same values (period=24)
        assert result["hour_sin"].iloc[0] == pytest.approx(result["hour_sin"].iloc[24])
        assert result["hour_cos"].iloc[0] == pytest.approx(result["hour_cos"].iloc[24])
        
        # Hour 0: sin(0) = 0, cos(0) = 1
        assert result["hour_sin"].iloc[0] == pytest.approx(0.0, abs=1e-10)
        assert result["hour_cos"].iloc[0] == pytest.approx(1.0)
        
        # Hour 6: sin(π/2) = 1, cos(π/2) = 0
        assert result["hour_sin"].iloc[6] == pytest.approx(1.0)
        assert result["hour_cos"].iloc[6] == pytest.approx(0.0, abs=1e-10)
        
        # Hour 12: sin(π) = 0, cos(π) = -1
        assert result["hour_sin"].iloc[12] == pytest.approx(0.0, abs=1e-10)
        assert result["hour_cos"].iloc[12] == pytest.approx(-1.0)
    
    def test_cyclical_dow_encoding(self):
        """Day of week cyclical encoding should have period 7."""
        # 2007-01-01 is Monday, 2007-01-08 is also Monday
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=8, freq="D"),
            "global_active_power_mean_kw": np.ones(8),
        })
        result = build_features(df, lag_hours=[], rolling_windows=[])
        
        # Monday day 0 and day 7 should encode to same values
        assert result["dow_sin"].iloc[0] == pytest.approx(result["dow_sin"].iloc[7])
        assert result["dow_cos"].iloc[0] == pytest.approx(result["dow_cos"].iloc[7])
        
        # Monday (dow=0): sin(0) = 0, cos(0) = 1
        assert result["dow_sin"].iloc[0] == pytest.approx(0.0, abs=1e-10)
        assert result["dow_cos"].iloc[0] == pytest.approx(1.0)


class TestLagFeatures:
    """Test lag feature creation and alignment."""
    
    def test_lag_1h_basic(self):
        """Lag 1h should reference previous hour's target."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=5, freq="h"),
            "global_active_power_mean_kw": [1.0, 2.0, 3.0, 4.0, 5.0],
        })
        result = build_features(df, lag_hours=[1], rolling_windows=[])
        
        assert pd.isna(result["lag_1h"].iloc[0])  # No history
        assert result["lag_1h"].iloc[1] == 1.0
        assert result["lag_1h"].iloc[2] == 2.0
        assert result["lag_1h"].iloc[3] == 3.0
        assert result["lag_1h"].iloc[4] == 4.0
    
    def test_lag_24h_basic(self):
        """Lag 24h should reference value from 24 hours ago."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=26, freq="h"),
            "global_active_power_mean_kw": np.arange(26, dtype=float),
        })
        result = build_features(df, lag_hours=[24], rolling_windows=[])
        
        # First 24 hours have no 24h history
        assert pd.isna(result["lag_24h"].iloc[0])
        assert pd.isna(result["lag_24h"].iloc[23])
        
        # Hour 24 should have lag from hour 0
        assert result["lag_24h"].iloc[24] == 0.0
        assert result["lag_24h"].iloc[25] == 1.0
    
    def test_multiple_lags(self):
        """Multiple lag features should coexist correctly."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=10, freq="h"),
            "global_active_power_mean_kw": np.arange(10, dtype=float),
        })
        result = build_features(df, lag_hours=[1, 2, 3], rolling_windows=[])
        
        # Check row 5
        assert result["lag_1h"].iloc[5] == 4.0
        assert result["lag_2h"].iloc[5] == 3.0
        assert result["lag_3h"].iloc[5] == 2.0
    
    def test_lag_with_missing_target(self):
        """Missing target values should propagate to lags."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=5, freq="h"),
            "global_active_power_mean_kw": [1.0, np.nan, 3.0, 4.0, 5.0],
        })
        result = build_features(df, lag_hours=[1], rolling_windows=[])
        
        assert pd.isna(result["lag_1h"].iloc[0])  # No history
        assert result["lag_1h"].iloc[1] == 1.0
        assert pd.isna(result["lag_1h"].iloc[2])  # Previous was NaN
        assert result["lag_1h"].iloc[3] == 3.0
        assert result["lag_1h"].iloc[4] == 4.0


class TestRollingFeatures:
    """Test rolling statistics and leakage prevention."""
    
    def test_rolling_mean_excludes_current_hour(self):
        """
        Critical leakage test: rolling mean at time T must NOT include target at T.
        
        At each timestamp, the rolling feature should be computed from the window
        ending at (T - 1 hour), not including the current hour's target.
        
        With min_periods=window, rolling_mean_Nh requires N hours of history.
        """
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=5, freq="h"),
            "global_active_power_mean_kw": [10.0, 20.0, 30.0, 40.0, 50.0],
        })
        result = build_features(df, lag_hours=[], rolling_windows=[3])
        
        # Hour 0-2: insufficient history (need 3 hours) → NaN
        assert pd.isna(result["rolling_mean_3h"].iloc[0])
        assert pd.isna(result["rolling_mean_3h"].iloc[1])
        assert pd.isna(result["rolling_mean_3h"].iloc[2])
        
        # Hour 3: mean of hours 0-2 (full 3-hour window, excluding hour 3's 40.0)
        assert result["rolling_mean_3h"].iloc[3] == pytest.approx(20.0)
        
        # Hour 4: mean of hours 1-3 (excluding hour 4's 50.0)
        expected = (20.0 + 30.0 + 40.0) / 3
        assert result["rolling_mean_3h"].iloc[4] == pytest.approx(expected)
    
    def test_rolling_std_excludes_current_hour(self):
        """Rolling std must also exclude current hour."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=5, freq="h"),
            "global_active_power_mean_kw": [10.0, 20.0, 30.0, 40.0, 50.0],
        })
        result = build_features(df, lag_hours=[], rolling_windows=[3])
        
        # Hour 0-2: insufficient history (need 3 hours) → NaN
        assert pd.isna(result["rolling_std_3h"].iloc[0])
        assert pd.isna(result["rolling_std_3h"].iloc[1])
        assert pd.isna(result["rolling_std_3h"].iloc[2])
        
        # Hour 3: std of [10.0, 20.0, 30.0]
        expected_std = np.std([10.0, 20.0, 30.0], ddof=1)
        assert result["rolling_std_3h"].iloc[3] == pytest.approx(expected_std)
    
    def test_multiple_rolling_windows(self):
        """Multiple rolling windows should coexist."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=50, freq="h"),
            "global_active_power_mean_kw": np.arange(50, dtype=float),
        })
        result = build_features(df, lag_hours=[], rolling_windows=[3, 24])
        
        assert "rolling_mean_3h" in result.columns
        assert "rolling_std_3h" in result.columns
        assert "rolling_mean_24h" in result.columns
        assert "rolling_std_24h" in result.columns
        
        # At hour 30, rolling_mean_3h should average hours 27-29
        expected_3h = np.mean([27.0, 28.0, 29.0])
        assert result["rolling_mean_3h"].iloc[30] == pytest.approx(expected_3h)
        
        # At hour 30, rolling_mean_24h should average hours 6-29
        expected_24h = np.mean(np.arange(6, 30, dtype=float))
        assert result["rolling_mean_24h"].iloc[30] == pytest.approx(expected_24h)
    
    def test_rolling_with_missing_values(self):
        """Rolling features should handle missing target values."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=5, freq="h"),
            "global_active_power_mean_kw": [10.0, np.nan, 30.0, 40.0, 50.0],
        })
        result = build_features(df, lag_hours=[], rolling_windows=[3])
        
        # Hour 0-2: insufficient history → NaN
        assert pd.isna(result["rolling_mean_3h"].iloc[0])
        assert pd.isna(result["rolling_mean_3h"].iloc[1])
        assert pd.isna(result["rolling_mean_3h"].iloc[2])
        
        # Hour 3: window [10.0, NaN, 30.0]
        # With min_periods=3, need 3 non-NaN values but only have 2 → NaN
        assert pd.isna(result["rolling_mean_3h"].iloc[3])
        
        # Hour 4: window [NaN, 30.0, 40.0]
        # With min_periods=3, need 3 non-NaN values but only have 2 → NaN
        assert pd.isna(result["rolling_mean_3h"].iloc[4])


class TestLeakagePrevention:
    """Critical tests for temporal leakage prevention."""
    
    def test_future_perturbation_invariance(self):
        """
        Changing observations after timestamp T must not affect features at T.
        
        This is the gold standard leakage test: if we modify future data,
        features used to predict at time T should remain unchanged.
        """
        # Create base data
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=100, freq="h"),
            "global_active_power_mean_kw": np.random.RandomState(42).rand(100) + 1.0,
        })
        
        # Build features
        result1 = build_features(df, lag_hours=[1, 24], rolling_windows=[24])
        
        # Modify data AFTER hour 50 (future from perspective of hour 50)
        df_modified = df.copy()
        df_modified.loc[51:, "global_active_power_mean_kw"] = 999.0
        
        result2 = build_features(df_modified, lag_hours=[1, 24], rolling_windows=[24])
        
        # Features at hour 50 should be IDENTICAL in both cases
        feature_cols = get_feature_columns(lag_hours=[1, 24], rolling_windows=[24])["all"]
        
        for col in feature_cols:
            val1 = result1.loc[50, col]
            val2 = result2.loc[50, col]
            
            if pd.isna(val1) and pd.isna(val2):
                continue  # Both NaN is fine
            
            assert val1 == pytest.approx(val2), (
                f"Feature '{col}' at hour 50 changed after modifying future data. "
                f"Original: {val1}, Modified: {val2}. This indicates temporal leakage!"
            )
    
    def test_rolling_never_uses_current_target(self):
        """
        Explicit test: when predicting target at time T, rolling features
        must not include the target value at T.
        
        Use a sentinel value to detect if current target leaks into features.
        """
        # Create data with a sentinel value at hour 50
        target_values = np.ones(100)
        target_values[50] = 999.0  # Sentinel
        
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=100, freq="h"),
            "global_active_power_mean_kw": target_values,
        })
        
        result = build_features(df, lag_hours=[], rolling_windows=[3, 24])
        
        # At hour 50, rolling features should NOT include 999.0
        # rolling_mean_3h should be mean of hours 47-49 (all 1.0)
        assert result["rolling_mean_3h"].iloc[50] == pytest.approx(1.0)
        
        # rolling_mean_24h should be mean of hours 26-49 (all 1.0)
        assert result["rolling_mean_24h"].iloc[50] == pytest.approx(1.0)
        
        # At hour 51, rolling_mean_3h should include the sentinel from hour 50
        # Mean of hours 48-50: [1.0, 1.0, 999.0]
        expected = (1.0 + 1.0 + 999.0) / 3
        assert result["rolling_mean_3h"].iloc[51] == pytest.approx(expected)


class TestChronologicalOrdering:
    """Test that chronological order is preserved."""
    
    def test_preserves_chronological_order(self):
        """Output should maintain chronological order of input."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=100, freq="h"),
            "global_active_power_mean_kw": np.random.rand(100),
        })
        
        result = build_features(df)
        
        # Timestamps should be monotonically increasing
        assert result["timestamp"].is_monotonic_increasing
    
    def test_sorts_unordered_input(self):
        """Function should sort input if not chronologically ordered."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=10, freq="h"),
            "global_active_power_mean_kw": np.arange(10, dtype=float),
        })
        
        # Shuffle the dataframe
        df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
        assert not df_shuffled["timestamp"].is_monotonic_increasing
        
        result = build_features(df_shuffled, lag_hours=[1], rolling_windows=[])
        
        # Output should be sorted
        assert result["timestamp"].is_monotonic_increasing
        
        # Lag features should be correct after sorting
        assert result["lag_1h"].iloc[5] == 4.0


class TestMissingValueHandling:
    """Test missing value transparency and documentation."""
    
    def test_missing_values_not_silently_dropped(self):
        """Function should NOT drop rows with NaN features."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=10, freq="h"),
            "global_active_power_mean_kw": np.arange(10, dtype=float),
        })
        
        result = build_features(df, lag_hours=[1, 24], rolling_windows=[3])
        
        # Output should have same number of rows as input
        assert len(result) == len(df)
    
    def test_count_missing_features_utility(self):
        """count_missing_features should report NaN counts correctly."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=30, freq="h"),
            "global_active_power_mean_kw": np.arange(30, dtype=float),
        })
        
        result = build_features(df, lag_hours=[1, 24], rolling_windows=[24])
        feature_cols = get_feature_columns(lag_hours=[1, 24], rolling_windows=[24])["all"]
        
        missing = count_missing_features(result, feature_cols)
        
        # Calendar features should never be missing
        assert missing["hour_of_day"] == 0
        assert missing["hour_sin"] == 0
        
        # lag_1h: first row is NaN
        assert missing["lag_1h"] == 1
        
        # lag_24h: first 24 rows are NaN
        assert missing["lag_24h"] == 24
        
        # rolling_mean_24h: first 24 rows are NaN (need full window with min_periods=window)
        assert missing["rolling_mean_24h"] == 24


class TestInputValidation:
    """Test input validation and error messages."""
    
    def test_rejects_empty_dataframe(self):
        """Should raise ValueError for empty input."""
        df = pd.DataFrame({"timestamp": [], "global_active_power_mean_kw": []})
        
        with pytest.raises(ValueError, match="empty"):
            build_features(df)
    
    def test_rejects_missing_timestamp_column(self):
        """Should raise ValueError if timestamp column missing."""
        df = pd.DataFrame({"time": pd.date_range("2007-01-01", periods=5, freq="h")})
        
        with pytest.raises(ValueError, match="Timestamp column.*not found"):
            build_features(df)
    
    def test_rejects_missing_target_column(self):
        """Should raise ValueError if target column missing."""
        df = pd.DataFrame({"timestamp": pd.date_range("2007-01-01", periods=5, freq="h")})
        
        with pytest.raises(ValueError, match="Target column.*not found"):
            build_features(df)
    
    def test_rejects_non_datetime_timestamp(self):
        """Should raise ValueError if timestamp is not datetime64."""
        df = pd.DataFrame({
            "timestamp": ["2007-01-01", "2007-01-02"],
            "global_active_power_mean_kw": [1.0, 2.0],
        })
        
        with pytest.raises(ValueError, match="datetime64 dtype"):
            build_features(df)
    
    def test_rejects_duplicate_timestamps(self):
        """Should raise ValueError if duplicate timestamps present."""
        df = pd.DataFrame({
            "timestamp": pd.to_datetime([
                "2007-01-01 00:00",
                "2007-01-01 01:00",
                "2007-01-01 01:00",  # Duplicate
                "2007-01-01 02:00",
            ]),
            "global_active_power_mean_kw": [10.0, 20.0, 25.0, 30.0],
        })
        
        with pytest.raises(ValueError, match="duplicate timestamp"):
            build_features(df)
    
    def test_rejects_invalid_lag_hours(self):
        """Should raise ValueError for lag < 1."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=5, freq="h"),
            "global_active_power_mean_kw": np.ones(5),
        })
        
        with pytest.raises(ValueError, match="Lag must be >= 1"):
            build_features(df, lag_hours=[0])
        
        with pytest.raises(ValueError, match="Lag must be >= 1"):
            build_features(df, lag_hours=[-1])
    
    def test_rejects_invalid_rolling_window(self):
        """Should raise ValueError for window < 1."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=5, freq="h"),
            "global_active_power_mean_kw": np.ones(5),
        })
        
        with pytest.raises(ValueError, match="Rolling window must be >= 1"):
            build_features(df, rolling_windows=[0])


class TestHourlyReindexing:
    """Test hourly reindexing for time-based lag correctness."""
    
    def test_fills_missing_hours_with_nan(self):
        """Missing hours in input should be filled with NaN in output."""
        df = pd.DataFrame({
            "timestamp": pd.to_datetime([
                "2007-01-01 00:00",
                "2007-01-01 01:00",
                "2007-01-01 02:00",
                # Gap: 03:00 missing
                "2007-01-01 04:00",
                "2007-01-01 05:00",
            ]),
            "global_active_power_mean_kw": [10.0, 20.0, 30.0, 40.0, 50.0],
        })
        
        result = build_features(df, lag_hours=[1], rolling_windows=[])
        
        # Output should have 6 rows (00:00 through 05:00)
        assert len(result) == 6
        
        # Check that 03:00 was filled
        ts_03 = pd.Timestamp("2007-01-01 03:00")
        assert ts_03 in result["timestamp"].values
        
        # Target at 03:00 should be NaN (gap)
        row_03 = result[result["timestamp"] == ts_03].iloc[0]
        assert pd.isna(row_03["global_active_power_mean_kw"])
    
    def test_lag_references_correct_time_with_gap(self):
        """
        Critical: lag_1h after a gap should reference the correct hour, not previous position.
        """
        df = pd.DataFrame({
            "timestamp": pd.to_datetime([
                "2007-01-01 00:00",
                "2007-01-01 01:00",
                "2007-01-01 02:00",
                # Gap: 03:00 missing
                "2007-01-01 04:00",
                "2007-01-01 05:00",
            ]),
            "global_active_power_mean_kw": [10.0, 20.0, 30.0, 40.0, 50.0],
        })
        
        result = build_features(df, lag_hours=[1], rolling_windows=[])
        
        # At 04:00, lag_1h should reference 03:00 (which is NaN due to gap)
        # NOT 02:00 (which would be position-based)
        row_04 = result[result["timestamp"] == pd.Timestamp("2007-01-01 04:00")].iloc[0]
        assert pd.isna(row_04["lag_1h"]), (
            "lag_1h at 04:00 should be NaN (references missing 03:00), "
            f"but got {row_04['lag_1h']}"
        )
        
        # At 05:00, lag_1h should be 40.0 (from 04:00)
        row_05 = result[result["timestamp"] == pd.Timestamp("2007-01-01 05:00")].iloc[0]
        assert row_05["lag_1h"] == 40.0
    
    def test_rolling_features_handle_gaps(self):
        """Rolling features should handle gaps correctly via reindexing."""
        df = pd.DataFrame({
            "timestamp": pd.to_datetime([
                "2007-01-01 00:00",
                "2007-01-01 01:00",
                # Gap: 02:00 missing
                "2007-01-01 03:00",
                "2007-01-01 04:00",
            ]),
            "global_active_power_mean_kw": [10.0, 20.0, 30.0, 40.0],
        })
        
        result = build_features(df, lag_hours=[], rolling_windows=[3])
        
        # Output should have 5 rows (00:00 through 04:00)
        assert len(result) == 5
        
        # At 03:00, rolling_mean_3h uses hours [00:00, 01:00, 02:00]
        # 02:00 is NaN (filled gap), so window is [10.0, 20.0, NaN]
        # With min_periods=3, need 3 non-NaN values but only have 2 → NaN
        row_03 = result[result["timestamp"] == pd.Timestamp("2007-01-01 03:00")].iloc[0]
        assert pd.isna(row_03["rolling_mean_3h"])
        
        # At 04:00, rolling_mean_3h uses hours [01:00, 02:00, 03:00]
        # Window is [20.0, NaN, 30.0], still only 2 non-NaN → NaN
        row_04 = result[result["timestamp"] == pd.Timestamp("2007-01-01 04:00")].iloc[0]
        assert pd.isna(row_04["rolling_mean_3h"])
    
    def test_preserves_timezone_in_reindexing(self):
        """Reindexing should preserve timezone information."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=5, freq="h", tz="UTC"),
            "global_active_power_mean_kw": np.arange(5, dtype=float),
        })
        
        result = build_features(df, lag_hours=[1], rolling_windows=[])
        
        # Timezone should be preserved
        assert result["timestamp"].dt.tz is not None
        assert str(result["timestamp"].dt.tz) == "UTC"


class TestRollingWindowBehavior:
    """Test rolling window with min_periods=window."""
    
    def test_rolling_mean_requires_full_window(self):
        """Rolling mean should be NaN until full window available."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=30, freq="h"),
            "global_active_power_mean_kw": np.arange(30, dtype=float),
        })
        
        result = build_features(df, lag_hours=[], rolling_windows=[3, 24])
        
        # rolling_mean_3h: first 3 hours should be NaN (need 3 hours + shift)
        assert result["rolling_mean_3h"].iloc[0:3].isna().all()
        
        # rolling_mean_24h: first 24 hours should be NaN
        assert result["rolling_mean_24h"].iloc[0:24].isna().all()
        
        # After sufficient history, should have values
        assert not pd.isna(result["rolling_mean_3h"].iloc[3])
        assert not pd.isna(result["rolling_mean_24h"].iloc[24])
    
    def test_rolling_std_requires_full_window(self):
        """Rolling std should be NaN until full window available."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=30, freq="h"),
            "global_active_power_mean_kw": np.arange(30, dtype=float),
        })
        
        result = build_features(df, lag_hours=[], rolling_windows=[3, 24])
        
        # rolling_std_3h: first 3 hours should be NaN
        assert result["rolling_std_3h"].iloc[0:3].isna().all()
        
        # rolling_std_24h: first 24 hours should be NaN
        assert result["rolling_std_24h"].iloc[0:24].isna().all()
        
        # After sufficient history, should have values
        assert not pd.isna(result["rolling_std_3h"].iloc[3])
        assert not pd.isna(result["rolling_std_24h"].iloc[24])
    
    def test_rolling_nan_counts_with_min_periods_window(self):
        """Verify expected NaN counts with min_periods=window."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=200, freq="h"),
            "global_active_power_mean_kw": np.arange(200, dtype=float),
        })
        
        result = build_features(df)
        cols = get_feature_columns()
        missing = count_missing_features(result, cols["rolling"])
        
        # With min_periods=window and shift(1):
        # rolling_mean_3h: first 3 rows are NaN
        assert missing["rolling_mean_3h"] == 3
        # rolling_mean_24h: first 24 rows are NaN
        assert missing["rolling_mean_24h"] == 24
        # rolling_mean_168h: first 168 rows are NaN
        assert missing["rolling_mean_168h"] == 168
        
        # Same for std
        assert missing["rolling_std_3h"] == 3
        assert missing["rolling_std_24h"] == 24
        assert missing["rolling_std_168h"] == 168


class TestInputValidation:
    """Test input validation and error messages."""
    
    def test_rejects_empty_dataframe(self):
        """Should raise ValueError for empty input."""
        df = pd.DataFrame({"timestamp": [], "global_active_power_mean_kw": []})
        
        with pytest.raises(ValueError, match="empty"):
            build_features(df)
    
    def test_rejects_missing_timestamp_column(self):
        """Should raise ValueError if timestamp column missing."""
        df = pd.DataFrame({"time": pd.date_range("2007-01-01", periods=5, freq="h")})
        
        with pytest.raises(ValueError, match="Timestamp column.*not found"):
            build_features(df)
    
    def test_rejects_missing_target_column(self):
        """Should raise ValueError if target column missing."""
        df = pd.DataFrame({"timestamp": pd.date_range("2007-01-01", periods=5, freq="h")})
        
        with pytest.raises(ValueError, match="Target column.*not found"):
            build_features(df)
    
    def test_rejects_non_datetime_timestamp(self):
        """Should raise ValueError if timestamp is not datetime64."""
        df = pd.DataFrame({
            "timestamp": ["2007-01-01", "2007-01-02"],
            "global_active_power_mean_kw": [1.0, 2.0],
        })
        
        with pytest.raises(ValueError, match="datetime64 dtype"):
            build_features(df)
    
    def test_rejects_invalid_lag_hours(self):
        """Should raise ValueError for lag < 1."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=5, freq="h"),
            "global_active_power_mean_kw": np.ones(5),
        })
        
        with pytest.raises(ValueError, match="Lag must be >= 1"):
            build_features(df, lag_hours=[0])
        
        with pytest.raises(ValueError, match="Lag must be >= 1"):
            build_features(df, lag_hours=[-1])
    
    def test_rejects_invalid_rolling_window(self):
        """Should raise ValueError for window < 1."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=5, freq="h"),
            "global_active_power_mean_kw": np.ones(5),
        })
        
        with pytest.raises(ValueError, match="Rolling window must be >= 1"):
            build_features(df, rolling_windows=[0])


class TestFeatureColumnUtility:
    """Test get_feature_columns utility function."""
    
    def test_returns_all_categories(self):
        """Should return calendar, lag, rolling, and all."""
        cols = get_feature_columns(lag_hours=[1, 24], rolling_windows=[3])
        
        assert "calendar" in cols
        assert "lag" in cols
        assert "rolling" in cols
        assert "all" in cols
    
    def test_calendar_columns_correct(self):
        """Calendar columns should be complete."""
        cols = get_feature_columns()
        expected = [
            "hour_of_day", "day_of_week", "is_weekend", "month",
            "hour_sin", "hour_cos", "dow_sin", "dow_cos"
        ]
        assert cols["calendar"] == expected
    
    def test_lag_columns_match_config(self):
        """Lag columns should match input configuration."""
        cols = get_feature_columns(lag_hours=[1, 2, 24, 168])
        assert cols["lag"] == ["lag_1h", "lag_2h", "lag_24h", "lag_168h"]
    
    def test_rolling_columns_match_config(self):
        """Rolling columns should include mean and std for each window."""
        cols = get_feature_columns(rolling_windows=[3, 24])
        expected = [
            "rolling_mean_3h", "rolling_std_3h",
            "rolling_mean_24h", "rolling_std_24h"
        ]
        assert cols["rolling"] == expected
    
    def test_all_columns_combines_categories(self):
        """All columns should be calendar + lag + rolling."""
        cols = get_feature_columns(lag_hours=[1], rolling_windows=[3])
        
        expected_all = (
            cols["calendar"] + cols["lag"] + cols["rolling"]
        )
        assert cols["all"] == expected_all
