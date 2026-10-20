"""Real dataset integration for GridPulse energy forecasting.

This module provides the integration layer between the UCI dataset validator
(scripts/validate_data.py) and the ML pipeline (features, baselines, models).

Key functions:
- download_uci_dataset: Download from official UCI repository
- load_hourly_data: Load validated hourly aggregates
- prepare_for_training: Full pipeline from raw to train/val/test splits
"""
from __future__ import annotations

import hashlib
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any
from urllib.request import urlopen

import pandas as pd

from ml.evaluation import chronological_split
from ml.features import build_features

# Official UCI dataset metadata
UCI_DATASET_URL = "https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip"
UCI_ZIP_MD5 = "1f112f6e363c07792e635a3c5b0a3622"  # MD5 of the ZIP file
EXPECTED_TXT_FILENAME = "household_power_consumption.txt"


def download_uci_dataset(
    output_dir: str | Path = "data/raw",
    *,
    verify_md5: bool = True,
    force: bool = False,
) -> Path:
    """
    Download the UCI Individual Household Electric Power Consumption dataset.
    
    Downloads from the official UCI Machine Learning Repository and extracts
    the dataset text file to the specified output directory.
    
    Parameters
    ----------
    output_dir : str or Path, default "data/raw"
        Directory where the extracted dataset file will be saved.
    verify_md5 : bool, default True
        If True, verify the downloaded ZIP file's MD5 checksum.
    force : bool, default False
        If True, re-download even if the file already exists.
    
    Returns
    -------
    Path
        Absolute path to the downloaded dataset text file.
    
    Raises
    ------
    RuntimeError
        If download fails, MD5 verification fails, or extraction fails.
    
    Examples
    --------
    >>> dataset_path = download_uci_dataset()
    >>> print(f"Dataset downloaded to: {dataset_path}")
    
    Notes
    -----
    - The dataset is ~20MB compressed, ~130MB uncompressed
    - Official source: https://archive.ics.uci.edu/dataset/235
    - License: CC BY 4.0
    - Expected file: household_power_consumption.txt (2,075,259 rows)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    dataset_file = output_path / EXPECTED_TXT_FILENAME
    
    # Check if already downloaded
    if dataset_file.exists() and not force:
        print(f"Dataset already exists: {dataset_file}")
        print("Use force=True to re-download.")
        return dataset_file.resolve()
    
    print(f"Downloading UCI dataset from: {UCI_DATASET_URL}")
    print("This may take a few minutes (~20MB)...")
    
    # Download ZIP file to temporary location
    zip_path = output_path / "household_power_consumption.zip"
    
    try:
        with urlopen(UCI_DATASET_URL) as response:
            total_size = int(response.headers.get('content-length', 0))
            
            with open(zip_path, 'wb') as f:
                downloaded = 0
                chunk_size = 8192
                
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.1f}% ({downloaded}/{total_size} bytes)", end='')
                        sys.stdout.flush()
        
        print()  # Newline after progress
        print(f"Download complete: {zip_path}")
        
        # Verify MD5 checksum
        if verify_md5:
            print("Verifying MD5 checksum...")
            md5_hash = hashlib.md5()
            with open(zip_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    md5_hash.update(chunk)
            
            actual_md5 = md5_hash.hexdigest()
            if actual_md5 != UCI_ZIP_MD5:
                raise RuntimeError(
                    f"MD5 checksum mismatch!\n"
                    f"Expected: {UCI_ZIP_MD5}\n"
                    f"Got:      {actual_md5}\n"
                    f"The download may be corrupted. Try again with force=True."
                )
            print(f"[OK] MD5 checksum verified")
        
        # Extract the dataset file
        print("Extracting dataset...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List contents to find the target file
            members = zip_ref.namelist()
            txt_members = [m for m in members if m.endswith('.txt')]
            
            if not txt_members:
                raise RuntimeError(
                    f"No .txt file found in ZIP archive. Contents: {members}"
                )
            
            # Extract the first .txt file (should be household_power_consumption.txt)
            target_member = txt_members[0]
            print(f"Extracting: {target_member}")
            
            # Extract to output directory
            zip_ref.extract(target_member, output_path)
            
            # Rename if necessary
            extracted_path = output_path / target_member
            if extracted_path.name != EXPECTED_TXT_FILENAME:
                extracted_path.rename(dataset_file)
            
        print(f"[OK] Dataset extracted to: {dataset_file}")
        
        # Clean up ZIP file
        zip_path.unlink()
        print("[OK] Temporary ZIP file removed")
        
        return dataset_file.resolve()
    
    except Exception as e:
        # Clean up on failure
        if zip_path.exists():
            zip_path.unlink()
        raise RuntimeError(f"Failed to download UCI dataset: {e}") from e


def load_hourly_data(
    csv_path: str | Path = "data/processed/hourly_power.csv",
    *,
    timestamp_col: str = "timestamp",
    target_col: str = "global_active_power_mean_kw",
) -> pd.DataFrame:
    """
    Load validated hourly power data from CSV.
    
    This function loads the output of scripts/validate_data.py, which
    aggregates the raw UCI minute-level data to hourly means.
    
    Parameters
    ----------
    csv_path : str or Path, default "data/processed/hourly_power.csv"
        Path to the hourly aggregated CSV file.
    timestamp_col : str, default "timestamp"
        Name of the timestamp column.
    target_col : str, default "global_active_power_mean_kw"
        Name of the target column (hourly mean power in kW).
    
    Returns
    -------
    pd.DataFrame
        Hourly data with parsed timestamps.
        Columns: timestamp (datetime64), global_active_power_mean_kw (float64), etc.
    
    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist.
    ValueError
        If required columns are missing or timestamp parsing fails.
    
    Examples
    --------
    >>> hourly = load_hourly_data()
    >>> print(f"Loaded {len(hourly)} hourly observations")
    >>> print(f"Date range: {hourly['timestamp'].min()} to {hourly['timestamp'].max()}")
    
    Notes
    -----
    Before calling this function, you must run:
        python scripts/validate_data.py --input data/raw/household_power_consumption.txt
    
    This validates the raw data and produces the hourly aggregates.
    """
    path = Path(csv_path)
    
    if not path.exists():
        raise FileNotFoundError(
            f"Hourly data file not found: {path}\n"
            f"Run the validation script first:\n"
            f"  python scripts/validate_data.py --input data/raw/{EXPECTED_TXT_FILENAME}"
        )
    
    # Load CSV with timestamp parsing
    df = pd.read_csv(path, parse_dates=[timestamp_col])
    
    # Validate required columns
    if timestamp_col not in df.columns:
        raise ValueError(f"Timestamp column '{timestamp_col}' not found in {path}")
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in {path}")
    
    # Ensure timestamp is datetime64
    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
        raise ValueError(
            f"Timestamp column must be datetime64, got {df[timestamp_col].dtype}"
        )
    
    return df


def prepare_for_training(
    hourly_df: pd.DataFrame,
    *,
    timestamp_col: str = "timestamp",
    target_col: str = "global_active_power_mean_kw",
    lag_hours: list[int] | None = None,
    rolling_windows: list[int] | None = None,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    drop_na: bool = True,
) -> dict[str, Any]:
    """
    Full pipeline: hourly data → features → train/val/test splits.
    
    This function orchestrates the complete data preparation pipeline:
    1. Build calendar, lag, and rolling features from hourly data
    2. Split chronologically into train/validation/test sets
    3. Return ready-to-use data for model training and evaluation
    
    Parameters
    ----------
    hourly_df : pd.DataFrame
        Hourly power consumption data with timestamp and target columns.
    timestamp_col : str, default "timestamp"
        Name of timestamp column.
    target_col : str, default "global_active_power_mean_kw"
        Name of target column.
    lag_hours : list of int, optional
        Lag offsets for features. Default: [1, 2, 3, 24, 48, 168]
    rolling_windows : list of int, optional
        Rolling window sizes. Default: [3, 24, 168]
    train_ratio : float, default 0.70
        Proportion of data for training (0.0 to 1.0).
    val_ratio : float, default 0.15
        Proportion of data for validation (0.0 to 1.0).
    test_ratio : float, default 0.15
        Proportion of data for testing (0.0 to 1.0).
    drop_na : bool, default True
        If True, drop rows with NaN in features or target before splitting.
        If False, keep NaN rows (caller must handle them).
    
    Returns
    -------
    dict with keys:
        'features': Full feature dataframe (before split)
        'train_X': Training features
        'train_y': Training targets
        'val_X': Validation features
        'val_y': Validation targets
        'test_X': Test features
        'test_y': Test targets
        'feature_columns': List of feature column names
        'split_info': Dict with split indices and metadata
    
    Raises
    ------
    ValueError
        If input dataframe is invalid or split ratios don't sum to 1.0.
    
    Examples
    --------
    >>> hourly = load_hourly_data()
    >>> data = prepare_for_training(hourly)
    >>> print(f"Train: {len(data['train_X'])} samples")
    >>> print(f"Val:   {len(data['val_X'])} samples")
    >>> print(f"Test:  {len(data['test_X'])} samples")
    >>> print(f"Features: {len(data['feature_columns'])}")
    
    Notes
    -----
    - Features are built with leakage-safe logic (no future information)
    - Split is chronological (train earliest, test latest)
    - Early rows with insufficient history are NaN and dropped if drop_na=True
    - All models should use the same train/val/test split for fair comparison
    """
    # Build features
    features_df = build_features(
        hourly_df,
        timestamp_col=timestamp_col,
        target_col=target_col,
        lag_hours=lag_hours,
        rolling_windows=rolling_windows,
    )
    
    # Get feature column names (exclude timestamp and target)
    feature_cols = [
        col for col in features_df.columns 
        if col not in [timestamp_col, target_col]
    ]
    
    # Split chronologically
    # Note: chronological_split uses train_frac and val_frac
    # test_frac is implicit: 1 - train_frac - val_frac
    split = chronological_split(
        features_df,
        target_col=target_col,
        feature_cols=feature_cols,
        train_frac=train_ratio,
        val_frac=val_ratio,
        drop_na=drop_na,
    )
    
    return {
        'features': features_df,
        'train_X': split.train_X,
        'train_y': split.train_y,
        'val_X': split.val_X,
        'val_y': split.val_y,
        'test_X': split.test_X,
        'test_y': split.test_y,
        'feature_columns': feature_cols,
        'split_info': {
            'train_end_idx': split.train_end_idx,
            'val_end_idx': split.val_end_idx,
            'train_size': len(split.train_X),
            'val_size': len(split.val_X),
            'test_size': len(split.test_X),
            'total_after_drop_na': len(split.train_X) + len(split.val_X) + len(split.test_X),
            'total_before_drop_na': len(features_df),
        },
    }
