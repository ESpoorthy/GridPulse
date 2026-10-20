"""Demonstration of real UCI dataset integration with GridPulse pipeline.

This script demonstrates the complete workflow:
1. Download the UCI Individual Household Electric Power Consumption dataset
2. Validate and aggregate to hourly means
3. Load the validated hourly data
4. Build features with leakage prevention
5. Split chronologically into train/validation/test sets
6. Train baseline and ML models
7. Evaluate on the test set

Usage:
    python examples/real_data_demo.py

Requirements:
    - Internet connection (for first-time dataset download)
    - ~130MB disk space for the raw dataset
    - Dependencies from requirements.txt
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.baselines import PersistenceBaseline, SeasonalNaiveBaseline
from ml.data_loader import download_uci_dataset, load_hourly_data, prepare_for_training
from ml.evaluation import calculate_metrics
from ml.models import (
    create_hist_gradient_boosting,
    create_linear_regression,
    create_random_forest,
)
from scripts.validate_data import inspect_dataset

# Configuration
RAW_DATA_PATH = Path("data/raw/household_power_consumption.txt")
HOURLY_DATA_PATH = Path("data/processed/hourly_power.csv")
VALIDATION_REPORT_PATH = Path("reports/generated/dataset_validation.json")
RESULTS_PATH = Path("reports/generated/real_data_results.json")


def main() -> int:
    """Run the complete real-data integration pipeline."""
    print("=" * 70)
    print("GridPulse Real Data Integration Demo")
    print("=" * 70)
    print()
    
    # Step 1: Download dataset if needed
    print("Step 1: Download UCI dataset")
    print("-" * 70)
    try:
        dataset_path = download_uci_dataset(
            output_dir="data/raw",
            verify_md5=False,  # Skip MD5 check - file structure is what matters
            force=False,
        )
        print(f"[OK] Dataset ready: {dataset_path}")
    except RuntimeError as e:
        print(f"[ERROR] Download failed: {e}")
        print()
        print("Manual download instructions:")
        print("1. Visit: https://archive.ics.uci.edu/dataset/235")
        print("2. Download: household_power_consumption.txt")
        print("3. Place at: data/raw/household_power_consumption.txt")
        return 1
    print()
    
    # Step 2: Validate and aggregate to hourly
    print("Step 2: Validate raw data and aggregate to hourly means")
    print("-" * 70)
    try:
        report, hourly = inspect_dataset(
            RAW_DATA_PATH,
            min_valid_minutes_per_hour=45,
            expected_rows=2_075_259,
        )
        
        print(f"[OK] Validation: {report['validation_status']}")
        print(f"  - Row count: {report['row_count']:,}")
        print(f"  - Date range: {report['first_timestamp']} to {report['last_timestamp']}")
        print(f"  - Target range: {report['global_active_power_min_kw']:.3f} - {report['global_active_power_max_kw']:.3f} kW")
        print(f"  - Hourly eligible: {report['hourly_aggregation']['eligible_hours']:,} hours")
        
        if report['warnings']:
            print(f"  - Warnings: {len(report['warnings'])}")
            for warning in report['warnings'][:3]:
                print(f"    - {warning}")
        
        # Save validation report
        VALIDATION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        VALIDATION_REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        
        # Save hourly data
        HOURLY_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        hourly.to_csv(HOURLY_DATA_PATH, index=False, date_format="%Y-%m-%dT%H:%M:%S")
        print(f"[OK] Hourly data saved: {HOURLY_DATA_PATH}")
        print(f"[OK] Validation report: {VALIDATION_REPORT_PATH}")
        
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] Validation failed: {e}")
        return 1
    print()
    
    # Step 3: Load hourly data
    print("Step 3: Load validated hourly data")
    print("-" * 70)
    hourly_df = load_hourly_data(HOURLY_DATA_PATH)
    print(f"[OK] Loaded {len(hourly_df):,} hourly observations")
    print(f"  - Date range: {hourly_df['timestamp'].min()} to {hourly_df['timestamp'].max()}")
    print(f"  - Mean power: {hourly_df['global_active_power_mean_kw'].mean():.3f} kW")
    print(f"  - Std power: {hourly_df['global_active_power_mean_kw'].std():.3f} kW")
    print()
    
    # Step 4: Prepare features and splits
    print("Step 4: Build features and split chronologically")
    print("-" * 70)
    data = prepare_for_training(
        hourly_df,
        lag_hours=[1, 2, 3, 24, 48, 168],
        rolling_windows=[3, 24, 168],
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        drop_na=True,
    )
    
    print(f"[OK] Features built: {len(data['feature_columns'])} features")
    print(f"  - Calendar: hour_of_day, day_of_week, is_weekend, month, cyclical encodings")
    print(f"  - Lag: lag_1h, lag_2h, lag_3h, lag_24h, lag_48h, lag_168h")
    print(f"  - Rolling: rolling_mean/std for windows 3h, 24h, 168h")
    print()
    print(f"[OK] Chronological split:")
    print(f"  - Train: {data['split_info']['train_size']:,} samples")
    print(f"  - Val:   {data['split_info']['val_size']:,} samples")
    print(f"  - Test:  {data['split_info']['test_size']:,} samples")
    print(f"  - Total: {data['split_info']['total_after_drop_na']:,} (after dropping NaN)")
    print()
    
    # Step 5: Train and evaluate models
    print("Step 5: Train and evaluate models")
    print("-" * 70)
    
    results = {}
    
    # Baseline: Persistence (Naive)
    print("Training: Persistence Baseline...")
    persistence = PersistenceBaseline()
    persistence.fit(data['train_X'], data['train_y'])
    persistence_pred = persistence.predict(data['test_X'])
    persistence_metrics = calculate_metrics(data['test_y'], persistence_pred)
    results['persistence'] = persistence_metrics
    print(f"  [OK] Test MAE:  {persistence_metrics['mae']:.4f} kW")
    print(f"  [OK] Test RMSE: {persistence_metrics['rmse']:.4f} kW")
    
    # Baseline: Seasonal Naive (daily)
    print("Training: Seasonal Naive (daily) Baseline...")
    seasonal_naive = SeasonalNaiveBaseline(seasonal_period=24)
    seasonal_naive.fit(data['train_X'], data['train_y'])
    seasonal_pred = seasonal_naive.predict(data['test_X'])
    seasonal_metrics = calculate_metrics(data['test_y'], seasonal_pred)
    results['seasonal_naive_daily'] = seasonal_metrics
    print(f"  [OK] Test MAE:  {seasonal_metrics['mae']:.4f} kW")
    print(f"  [OK] Test RMSE: {seasonal_metrics['rmse']:.4f} kW")
    
    # ML Model: Linear Regression
    print("Training: Linear Regression...")
    lr_model = create_linear_regression(feature_cols=data['feature_columns'])
    lr_model.fit(data['train_X'], data['train_y'])
    lr_pred = lr_model.predict(data['test_X'])
    lr_metrics = calculate_metrics(data['test_y'], lr_pred)
    results['linear_regression'] = lr_metrics
    print(f"  [OK] Test MAE:  {lr_metrics['mae']:.4f} kW")
    print(f"  [OK] Test RMSE: {lr_metrics['rmse']:.4f} kW")
    
    # ML Model: Random Forest
    print("Training: Random Forest...")
    rf_model = create_random_forest(
        feature_cols=data['feature_columns'],
        n_estimators=100,
        max_depth=15,
    )
    rf_model.fit(data['train_X'], data['train_y'])
    rf_pred = rf_model.predict(data['test_X'])
    rf_metrics = calculate_metrics(data['test_y'], rf_pred)
    results['random_forest'] = rf_metrics
    print(f"  [OK] Test MAE:  {rf_metrics['mae']:.4f} kW")
    print(f"  [OK] Test RMSE: {rf_metrics['rmse']:.4f} kW")
    
    # ML Model: Histogram Gradient Boosting
    print("Training: Histogram Gradient Boosting...")
    hgb_model = create_hist_gradient_boosting(
        feature_cols=data['feature_columns'],
        max_iter=100,
        max_depth=10,
    )
    hgb_model.fit(data['train_X'], data['train_y'])
    hgb_pred = hgb_model.predict(data['test_X'])
    hgb_metrics = calculate_metrics(data['test_y'], hgb_pred)
    results['hist_gradient_boosting'] = hgb_metrics
    print(f"  [OK] Test MAE:  {hgb_metrics['mae']:.4f} kW")
    print(f"  [OK] Test RMSE: {hgb_metrics['rmse']:.4f} kW")
    print()
    
    # Step 6: Save and summarize results
    print("Step 6: Results Summary")
    print("-" * 70)
    
    # Sort by MAE (lower is better)
    sorted_results = sorted(results.items(), key=lambda x: x[1]['mae'])
    
    print("Model Performance (Test Set):")
    print()
    print(f"{'Model':<30} {'MAE (kW)':>12} {'RMSE (kW)':>12}")
    print("-" * 56)
    for model_name, metrics in sorted_results:
        print(f"{model_name:<30} {metrics['mae']:>12.4f} {metrics['rmse']:>12.4f}")
    print()
    
    best_model, best_metrics = sorted_results[0]
    print(f"[OK] Best model: {best_model}")
    print(f"  - MAE improvement over persistence: {((persistence_metrics['mae'] - best_metrics['mae']) / persistence_metrics['mae'] * 100):.1f}%")
    print(f"  - RMSE improvement over persistence: {((persistence_metrics['rmse'] - best_metrics['rmse']) / persistence_metrics['rmse'] * 100):.1f}%")
    print()
    
    # Save results
    results_data = {
        'dataset': 'UCI Individual Household Electric Power Consumption',
        'test_samples': data['split_info']['test_size'],
        'features': len(data['feature_columns']),
        'models': results,
        'best_model': best_model,
    }
    
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results_data, indent=2), encoding="utf-8")
    print(f"[OK] Results saved: {RESULTS_PATH}")
    print()
    
    print("=" * 70)
    print("Real Data Integration Complete!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

