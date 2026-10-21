"""Tests for real dataset integration and loading."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from ml.data_loader import (
    download_uci_dataset,
    load_hourly_data,
    prepare_for_training,
)


class TestLoadHourlyData:
    """Test loading validated hourly data from CSV."""
    
    def test_loads_valid_csv(self, tmp_path):
        """Should successfully load a valid hourly CSV."""
        csv_path = tmp_path / "hourly.csv"
        
        # Create synthetic hourly data
        hourly_data = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=100, freq="h"),
            "global_active_power_mean_kw": np.random.rand(100) + 1.0,
            "valid_minutes": [60] * 100,
        })
        hourly_data.to_csv(csv_path, index=False)
        
        # Load and verify
        result = load_hourly_data(csv_path)
        
        assert len(result) == 100
        assert "timestamp" in result.columns
        assert "global_active_power_mean_kw" in result.columns
        assert pd.api.types.is_datetime64_any_dtype(result["timestamp"])
    
    def test_raises_if_file_not_found(self, tmp_path):
        """Should raise FileNotFoundError if CSV doesn't exist."""
        nonexistent = tmp_path / "does_not_exist.csv"
        
        with pytest.raises(FileNotFoundError, match="Hourly data file not found"):
            load_hourly_data(nonexistent)
    
    def test_raises_if_timestamp_column_missing(self, tmp_path):
        """Should raise error if timestamp column is missing."""
        csv_path = tmp_path / "bad_hourly.csv"
        
        bad_data = pd.DataFrame({
            "power": [1.0, 2.0, 3.0],
        })
        bad_data.to_csv(csv_path, index=False)
        
        # pandas raises ValueError when parse_dates references missing column
        with pytest.raises(ValueError):
            load_hourly_data(csv_path)
    
    def test_raises_if_target_column_missing(self, tmp_path):
        """Should raise ValueError if target column is missing."""
        csv_path = tmp_path / "bad_hourly.csv"
        
        bad_data = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=10, freq="h"),
        })
        bad_data.to_csv(csv_path, index=False)
        
        with pytest.raises(ValueError, match="Target column.*not found"):
            load_hourly_data(csv_path)
    
    def test_parses_timestamp_strings(self, tmp_path):
        """Should parse timestamp strings to datetime64."""
        csv_path = tmp_path / "hourly.csv"
        
        # Write with string timestamps
        with open(csv_path, 'w') as f:
            f.write("timestamp,global_active_power_mean_kw\n")
            f.write("2007-01-01T00:00:00,1.5\n")
            f.write("2007-01-01T01:00:00,2.0\n")
        
        result = load_hourly_data(csv_path)
        
        assert len(result) == 2
        assert pd.api.types.is_datetime64_any_dtype(result["timestamp"])
        assert result["timestamp"].iloc[0] == pd.Timestamp("2007-01-01 00:00:00")


class TestPrepareForTraining:
    """Test full pipeline from hourly data to train/val/test splits."""
    
    def test_full_pipeline_with_synthetic_data(self):
        """Should produce valid train/val/test splits from hourly data."""
        # Create synthetic hourly data with enough history for features
        hourly_df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=1000, freq="h"),
            "global_active_power_mean_kw": np.random.rand(1000) + 1.0,
        })
        
        result = prepare_for_training(
            hourly_df,
            lag_hours=[1, 24],
            rolling_windows=[24],
        )
        
        # Verify all expected keys are present
        assert "features" in result
        assert "train_X" in result
        assert "train_y" in result
        assert "val_X" in result
        assert "val_y" in result
        assert "test_X" in result
        assert "test_y" in result
        assert "feature_columns" in result
        assert "split_info" in result
        
        # Verify data shapes are consistent
        assert len(result["train_X"]) == len(result["train_y"])
        assert len(result["val_X"]) == len(result["val_y"])
        assert len(result["test_X"]) == len(result["test_y"])
        
        # Verify feature columns are reasonable
        feature_cols = result["feature_columns"]
        assert "hour_of_day" in feature_cols
        assert "lag_1h" in feature_cols
        assert "lag_24h" in feature_cols
        assert "rolling_mean_24h" in feature_cols
    
    def test_chronological_split_ordering(self):
        """Train should precede val should precede test in time."""
        hourly_df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=1000, freq="h"),
            "global_active_power_mean_kw": np.arange(1000, dtype=float),  # Increasing values
        })
        
        result = prepare_for_training(
            hourly_df,
            lag_hours=[1],
            rolling_windows=[3],
        )
        
        # Since target is strictly increasing, chronological order means
        # max(train) < min(val) < max(val) < min(test)
        assert result["train_y"].max() < result["val_y"].min()
        assert result["val_y"].max() < result["test_y"].min()
    
    def test_default_split_ratios(self):
        """Should use 70/15/15 split by default."""
        hourly_df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=1000, freq="h"),
            "global_active_power_mean_kw": np.random.rand(1000) + 1.0,
        })
        
        result = prepare_for_training(
            hourly_df,
            lag_hours=[1],
            rolling_windows=[3],
        )
        
        total = (
            result["split_info"]["train_size"]
            + result["split_info"]["val_size"]
            + result["split_info"]["test_size"]
        )
        
        train_pct = result["split_info"]["train_size"] / total
        val_pct = result["split_info"]["val_size"] / total
        test_pct = result["split_info"]["test_size"] / total
        
        # Allow 1% tolerance for rounding
        assert 0.69 <= train_pct <= 0.71
        assert 0.14 <= val_pct <= 0.16
        assert 0.14 <= test_pct <= 0.16
    
    def test_custom_split_ratios(self):
        """Should respect custom split ratios."""
        hourly_df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=1000, freq="h"),
            "global_active_power_mean_kw": np.random.rand(1000) + 1.0,
        })
        
        result = prepare_for_training(
            hourly_df,
            lag_hours=[1],
            rolling_windows=[3],
            train_ratio=0.60,
            val_ratio=0.20,
            test_ratio=0.20,
        )
        
        total = (
            result["split_info"]["train_size"]
            + result["split_info"]["val_size"]
            + result["split_info"]["test_size"]
        )
        
        train_pct = result["split_info"]["train_size"] / total
        val_pct = result["split_info"]["val_size"] / total
        test_pct = result["split_info"]["test_size"] / total
        
        assert 0.59 <= train_pct <= 0.61
        assert 0.19 <= val_pct <= 0.21
        assert 0.19 <= test_pct <= 0.21
    
    def test_drops_nan_by_default(self):
        """Should drop rows with NaN features by default."""
        hourly_df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=200, freq="h"),
            "global_active_power_mean_kw": np.random.rand(200) + 1.0,
        })
        
        result = prepare_for_training(
            hourly_df,
            lag_hours=[1, 168],  # 168-hour lag will create many NaN rows
            rolling_windows=[168],
            drop_na=True,
        )
        
        # After dropping NaN, total should be less than input
        total_after = result["split_info"]["total_after_drop_na"]
        total_before = result["split_info"]["total_before_drop_na"]
        
        assert total_after < total_before
        
        # No NaN values should remain in train/val/test
        assert not result["train_X"].isna().any().any()
        assert not result["val_X"].isna().any().any()
        assert not result["test_X"].isna().any().any()
        assert not result["train_y"].isna().any()
        assert not result["val_y"].isna().any()
        assert not result["test_y"].isna().any()
    
    def test_preserves_nan_when_requested(self):
        """Should keep NaN rows when drop_na=False."""
        hourly_df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=200, freq="h"),
            "global_active_power_mean_kw": np.random.rand(200) + 1.0,
        })
        
        result = prepare_for_training(
            hourly_df,
            lag_hours=[1, 24],
            rolling_windows=[24],
            drop_na=False,
        )
        
        # Total should match input (no rows dropped)
        total_after = result["split_info"]["total_after_drop_na"]
        total_before = result["split_info"]["total_before_drop_na"]
        
        assert total_after == total_before
        
        # Early rows should have NaN in lag/rolling features
        # (First 24 rows will have NaN for lag_24h and rolling_mean_24h)
        assert result["train_X"]["lag_24h"].isna().sum() > 0
    
    def test_feature_columns_exclude_timestamp_and_target(self):
        """Feature columns should not include timestamp or target."""
        hourly_df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=200, freq="h"),
            "global_active_power_mean_kw": np.random.rand(200) + 1.0,
        })
        
        result = prepare_for_training(
            hourly_df,
            lag_hours=[1],
            rolling_windows=[3],
        )
        
        feature_cols = result["feature_columns"]
        
        assert "timestamp" not in feature_cols
        assert "global_active_power_mean_kw" not in feature_cols
        assert len(feature_cols) > 0

    def test_feature_columns_exclude_hourly_coverage_metadata(self):
        hourly_df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=200, freq="h"),
            "global_active_power_mean_kw": np.random.rand(200) + 1.0,
            "valid_minutes": [60] * 200,
        })
        result = prepare_for_training(hourly_df, lag_hours=[1], rolling_windows=[3])
        assert "valid_minutes" not in result["feature_columns"]
    
    def test_split_info_contains_metadata(self):
        """Split info should contain useful metadata."""
        hourly_df = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=500, freq="h"),
            "global_active_power_mean_kw": np.random.rand(500) + 1.0,
        })
        
        result = prepare_for_training(
            hourly_df,
            lag_hours=[1],
            rolling_windows=[3],
        )
        
        split_info = result["split_info"]
        
        assert "train_end_idx" in split_info
        assert "val_end_idx" in split_info
        assert "train_size" in split_info
        assert "val_size" in split_info
        assert "test_size" in split_info
        assert "total_after_drop_na" in split_info
        assert "total_before_drop_na" in split_info
        
        # Sizes should be positive integers
        assert split_info["train_size"] > 0
        assert split_info["val_size"] > 0
        assert split_info["test_size"] > 0


class TestDownloadUCIDataset:
    """Test UCI dataset download functionality."""
    
    @patch('ml.data_loader.hashlib.sha256')
    @patch('ml.data_loader.urlopen')
    @patch('ml.data_loader.zipfile.ZipFile')
    def test_downloads_and_extracts_dataset(self, mock_zipfile, mock_urlopen, mock_sha256, tmp_path):
        """Should download, verify, and extract the dataset."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.headers = {'content-length': '1000'}
        mock_response.read = Mock(side_effect=[b'a' * 100, b''])  # Simulate download
        mock_urlopen.return_value.__enter__ = Mock(return_value=mock_response)
        mock_urlopen.return_value.__exit__ = Mock(return_value=False)
        
        # Mock ZIP extraction
        mock_zip = Mock()
        mock_zip.namelist.return_value = ['household_power_consumption.txt']
        mock_zip.open.return_value = BytesIO(b"Date;Time;Global_active_power\n")
        mock_zipfile.return_value.__enter__ = Mock(return_value=mock_zip)
        mock_zipfile.return_value.__exit__ = Mock(return_value=False)
        
        output_dir = tmp_path / "raw"
        output_dir.mkdir()
        from ml.data_loader import UCI_ZIP_SHA256
        mock_sha256.return_value.hexdigest.return_value = UCI_ZIP_SHA256
        
        result = download_uci_dataset(output_dir, force=True)
        
        # Verify download was called
        assert mock_urlopen.called
        assert result.exists()
        assert result.read_text() == "Date;Time;Global_active_power\n"
        assert mock_sha256.return_value.update.called
    
    def test_skips_download_if_file_exists(self, tmp_path):
        """Should not re-download if file already exists and force=False."""
        output_dir = tmp_path / "raw"
        output_dir.mkdir()
        
        # Create existing file
        existing_file = output_dir / "household_power_consumption.txt"
        existing_file.write_text("existing data")
        
        result = download_uci_dataset(output_dir, force=False)
        
        # Should return existing file without modification
        assert result == existing_file.resolve()
        assert existing_file.read_text() == "existing data"

    @patch('ml.data_loader.hashlib.sha256')
    @patch('ml.data_loader.urlopen')
    def test_rejects_archive_with_unexpected_checksum(self, mock_urlopen, mock_sha256, tmp_path):
        response = Mock(headers={"content-length": "1"})
        response.read = Mock(side_effect=[b"x", b""])
        mock_urlopen.return_value.__enter__ = Mock(return_value=response)
        mock_urlopen.return_value.__exit__ = Mock(return_value=False)
        mock_sha256.return_value.hexdigest.return_value = "0" * 64
        with pytest.raises(RuntimeError, match="SHA-256 checksum mismatch"):
            download_uci_dataset(tmp_path, force=True)
        assert not (tmp_path / "household_power_consumption.zip").exists()
    
    @patch('ml.data_loader.urlopen')
    def test_raises_on_download_failure(self, mock_urlopen, tmp_path):
        """Should raise RuntimeError if download fails."""
        mock_urlopen.side_effect = Exception("Network error")
        
        with pytest.raises(RuntimeError, match="Failed to download UCI dataset"):
            download_uci_dataset(tmp_path)


class TestEndToEndIntegration:
    """Integration tests for the full real-data pipeline."""
    
    def test_full_pipeline_from_csv_to_splits(self, tmp_path):
        """End-to-end test: CSV → load → prepare → train/val/test."""
        # 1. Create synthetic validated hourly CSV
        csv_path = tmp_path / "hourly_power.csv"
        hourly_data = pd.DataFrame({
            "timestamp": pd.date_range("2007-01-01", periods=1000, freq="h"),
            "global_active_power_mean_kw": np.random.rand(1000) * 2 + 1.0,
            "valid_minutes": [60] * 1000,
        })
        hourly_data.to_csv(csv_path, index=False)
        
        # 2. Load hourly data
        loaded = load_hourly_data(csv_path)
        assert len(loaded) == 1000
        
        # 3. Prepare for training
        data = prepare_for_training(
            loaded,
            lag_hours=[1, 24, 168],
            rolling_windows=[24, 168],
        )
        
        # 4. Verify we can use the data for training
        assert len(data["train_X"]) > 0
        assert len(data["val_X"]) > 0
        assert len(data["test_X"]) > 0
        
        # 5. Verify feature columns are reasonable for baselines
        feature_cols = data["feature_columns"]
        assert "lag_1h" in feature_cols  # Required for persistence
        assert "lag_24h" in feature_cols  # Required for seasonal-naive
        assert "lag_168h" in feature_cols  # Required for weekly seasonal-naive
        
        # 6. Verify no NaN in final splits
        assert not data["train_X"].isna().any().any()
        assert not data["val_X"].isna().any().any()
        assert not data["test_X"].isna().any().any()
