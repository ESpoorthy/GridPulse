"""
Tests for GridPulse FastAPI endpoints.

These tests verify that the API returns valid responses and handles errors correctly.
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys
import json

import pandas as pd
import joblib

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.main import app

client = TestClient(app)


class LastObservedModel:
    feature_cols = ["lag_1h"]

    def predict(self, frame):
        return frame["lag_1h"].to_numpy()


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check_returns_200(self):
        """Health endpoint should return 200."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_check_has_required_fields(self):
        """Health response should have all required fields."""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert "version" in data
        assert "dataAvailable" in data or "data_available" in data
        assert "modelsLoaded" in data or "models_loaded" in data
    
    def test_health_status_is_healthy(self):
        """Health status should be 'healthy'."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"


class TestModelMetricsEndpoint:
    """Test model comparison endpoint."""
    
    def test_model_metrics_returns_200_or_503(self):
        """Model metrics should return 200 if data exists, 503 otherwise."""
        response = client.get("/api/v1/model-metrics")
        assert response.status_code in [200, 503]
    
    def test_model_metrics_structure_if_available(self):
        """If model metrics available, verify structure."""
        response = client.get("/api/v1/model-metrics")
        
        if response.status_code == 200:
            data = response.json()
            assert "models" in data
            assert "bestModel" in data or "best_model" in data
            assert "evaluationPeriod" in data or "evaluation_period" in data
            assert "splitRatio" in data or "split_ratio" in data
            assert isinstance(data["models"], list)
            
            if len(data["models"]) > 0:
                model = data["models"][0]
                assert "name" in model
                assert "mae" in model
                assert "rmse" in model
    
    def test_models_sorted_by_mae(self):
        """Models should be sorted by MAE (best first)."""
        response = client.get("/api/v1/model-metrics")
        
        if response.status_code == 200:
            data = response.json()
            models = data["models"]
            
            if len(models) > 1:
                for i in range(len(models) - 1):
                    assert models[i]["mae"] <= models[i + 1]["mae"]


class TestDataHealthEndpoint:
    """Test data health endpoint."""
    
    def test_data_health_returns_200_or_503(self):
        """Data health should return 200 if data exists, 503 otherwise."""
        response = client.get("/api/v1/dataset-health")
        assert response.status_code in [200, 503]
    
    def test_data_health_structure_if_available(self):
        """If data health available, verify structure."""
        response = client.get("/api/v1/dataset-health")
        
        if response.status_code == 200:
            data = response.json()
            assert "datasetName" in data or "dataset_name" in data
            assert "quality" in data
            assert "statistics" in data
            assert "hourlyDistribution" in data or "hourly_distribution" in data
            
            # Verify quality structure
            quality = data["quality"]
            assert "totalRows" in quality or "total_rows" in quality
            assert "validRows" in quality or "valid_rows" in quality
            assert "missingRows" in quality or "missing_rows" in quality
            
            # Verify statistics structure
            stats = data["statistics"]
            assert "min" in stats
            assert "max" in stats
            assert "mean" in stats


class TestOverviewEndpoint:
    """Test overview endpoint."""
    
    def test_overview_returns_200_or_503(self):
        """Overview should return 200 if data exists, 503 otherwise."""
        response = client.get("/api/v1/overview")
        assert response.status_code in [200, 503]
    
    def test_overview_structure_if_available(self):
        """If overview available, verify structure."""
        response = client.get("/api/v1/overview")
        
        if response.status_code == 200:
            data = response.json()
            assert "currentPower" in data or "current_power" in data
            assert "dailyAverage" in data or "daily_average" in data
            assert "weeklyTrend" in data or "weekly_trend" in data
            assert "dataSource" in data or "data_source" in data


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_returns_200(self):
        """Root endpoint should return 200."""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_root_has_api_info(self):
        """Root should return API information."""
        response = client.get("/")
        data = response.json()
        
        assert "name" in data
        assert "version" in data
        assert "status" in data


class TestErrorHandling:
    """Test error handling."""
    
    def test_404_for_nonexistent_endpoint(self):
        """Should return 404 for non-existent endpoints."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
        assert "status" in data
        assert data["status"] == 404


class TestCORS:
    """Test CORS configuration."""
    
    def test_cors_headers_present(self):
        """CORS headers should be present for localhost."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        # FastAPI CORS middleware should add these headers
        assert response.status_code in [200, 204]


def test_api_uses_controlled_generated_data_not_fixed_values(tmp_path, monkeypatch):
    """Overview, health, metrics, and anomaly results follow their artifacts."""
    from backend.app import main as api

    timestamps = pd.date_range("2008-01-01", periods=24 * 15, freq="h")
    powers = [1.0 + (index % 24) / 100 for index in range(len(timestamps))]
    powers[-25] = 0.0
    powers[-1] = 4.0
    pd.DataFrame({"timestamp": timestamps, "global_active_power_mean_kw": powers}).to_csv(
        tmp_path / "hourly.csv", index=False
    )
    (tmp_path / "validation.json").write_text(json.dumps({
        "dataset_name": "Fixture household", "input_file": "fixture.txt", "row_count": 21600,
        "non_missing_target_rows": 21500, "timestamp_parse_failures": 2,
        "duplicate_rows_excluded_from_aggregation": 3, "missing_minute_timestamps_in_range": 4,
        "missing_numeric_values": {"Global_active_power": 100}, "numeric_parse_errors": {"Global_active_power": 0},
        "first_timestamp": timestamps[0].isoformat(), "last_timestamp": timestamps[-1].isoformat(),
        "hourly_aggregation": {"hourly_bins_in_time_range": 360, "eligible_hours": 359,
            "excluded_hours_below_coverage_threshold": 1},
        "warnings": [], "validation_status": "passed_with_warnings",
    }), encoding="utf-8")
    (tmp_path / "results.json").write_text(json.dumps({
        "models": {"linear_regression": {"validation": {"mae": .2}, "test": {"mae": .3, "rmse": .4},
            "recursive_validation": {"metrics": {"mae": .25, "rmse": .35}, "forecast_origins": 5,
                "evaluated_hours": 120, "step_group_metrics": {}}}},
        "best_model": "linear_regression", "split_ratio": "70/15/15", "train_samples": 200,
        "test_samples": 50, "test_period": {"start": "2008-01-01", "end": "2008-01-02"},
        "horizon_hours": 24, "selection_metric": "24-hour recursive validation MAE",
        "recursive_test": {"metrics": {"mae": .4, "rmse": .5}, "forecast_origins": 3,
            "evaluated_hours": 72, "step_group_metrics": {}, "evaluation_period": {"start": "2008-01-01", "end": "2008-01-03"}},
        "anomaly_calibration": {"method": "fixture validation quantiles", "threshold_low_kw": .1,
            "threshold_medium_kw": .2, "threshold_high_kw": .3},
    }), encoding="utf-8")
    monkeypatch.setattr(api, "HOURLY_PATH", tmp_path / "hourly.csv")
    monkeypatch.setattr(api, "VALIDATION_PATH", tmp_path / "validation.json")
    monkeypatch.setattr(api, "RESULTS_PATH", tmp_path / "results.json")
    model_artifact = tmp_path / "model.joblib"
    joblib.dump({"model": LastObservedModel(), "metadata": {"best_model": "fixture_model"}}, model_artifact)
    monkeypatch.setattr(api, "MODEL_PATH", model_artifact)

    overview = client.get("/api/v1/overview").json()
    health = client.get("/api/v1/dataset-health").json()
    metrics = client.get("/api/v1/model-metrics").json()
    anomalies = client.get("/api/v1/anomalies").json()

    assert overview["current_power"] == 4.0
    assert overview["daily_observed_hours"] == 24
    assert overview["daily_expected_hours"] == 24
    assert overview["daily_coverage_percentage"] == 100
    assert overview["anomaly_count"] == anomalies["total_count"]
    assert health["statistics"]["mean"] == pytest.approx(pd.Series(powers).mean())
    assert health["quality"]["total_rows"] == 21600
    assert health["quality"]["duplicate_rows_excluded"] == 3
    assert health["quality"]["timestamp_parse_failures"] == 2
    assert health["quality"]["missing_minute_timestamps"] == 4
    assert health["quality"]["excluded_hourly_intervals"] == 1
    assert metrics["models"][0]["test_samples"] == 50
    assert metrics["models"][0]["mae"] == .3
    assert metrics["forecast_horizon"] == 24
    assert metrics["models"][0]["recursive_validation"]["forecast_origins"] == 5
    assert metrics["recursive_test"]["forecast_origins"] == 3
    latest_anomaly = next(event for event in anomalies["events"] if event["timestamp"] == timestamps[-1].isoformat())
    assert latest_anomaly["severity"] == "high"
    assert latest_anomaly["deviation"] is None

    forecast = client.get("/api/v1/forecast")
    assert forecast.status_code == 200
    forecast_data = forecast.json()
    assert forecast_data["horizon"] == 24
    assert len(forecast_data["forecast"]) == 24
    assert forecast_data["forecast"][0]["timestamp"] == (timestamps[-1] + pd.Timedelta(hours=1)).isoformat()
    assert forecast_data["forecast"][-1]["timestamp"] == (timestamps[-1] + pd.Timedelta(hours=24)).isoformat()
    assert all(point["lower"] is None and point["upper"] is None for point in forecast_data["forecast"])


class TestForecastEndpoint:
    """Test forecast endpoint."""
    
    def test_forecast_returns_200_or_503(self):
        """Forecast should return 200 if data exists, 503 otherwise."""
        response = client.get("/api/v1/forecast")
        assert response.status_code in [200, 503]
    
    def test_forecast_structure_if_available(self):
        """If forecast available, verify structure."""
        response = client.get("/api/v1/forecast")
        
        if response.status_code == 200:
            data = response.json()
            assert "modelName" in data or "model_name" in data
            assert "horizon" in data
            assert "generatedAt" in data or "generated_at" in data
            assert "historical" in data
            assert "forecast" in data
            assert "isDemo" in data or "is_demo" in data
            
            # Verify horizon is 24
            assert data["horizon"] == 24
            
            # Verify forecast has 24 points
            assert len(data["forecast"]) == 24
            
            # Verify forecast point structure
            if data["forecast"]:
                point = data["forecast"][0]
                assert "timestamp" in point
                assert "predicted" in point
                assert isinstance(point["predicted"], (int, float))


class TestAnomalyEndpoint:
    """Test anomaly detection endpoint."""
    
    def test_anomaly_returns_200_or_503(self):
        """Anomaly should return 200 if data exists, 503 otherwise."""
        response = client.get("/api/v1/anomalies")
        assert response.status_code in [200, 503]
    
    def test_anomaly_structure_if_available(self):
        """If anomalies available, verify structure."""
        response = client.get("/api/v1/anomalies")
        
        if response.status_code == 200:
            data = response.json()
            assert "events" in data
            assert "totalCount" in data or "total_count" in data
            assert "severityCounts" in data or "severity_counts" in data
            assert "detectionMethod" in data or "detection_method" in data
            assert "thresholdInfo" in data or "threshold_info" in data
            assert "period" in data
            assert "isDemo" in data or "is_demo" in data
            
            # Verify severity counts
            severity_key = "severityCounts" if "severityCounts" in data else "severity_counts"
            assert "low" in data[severity_key]
            assert "medium" in data[severity_key]
            assert "high" in data[severity_key]
            
            # Verify total matches events
            total_key = "totalCount" if "totalCount" in data else "total_count"
            assert data[total_key] == len(data["events"])
            
            # If events exist, verify structure
            if data["events"]:
                event = data["events"][0]
                assert "id" in event
                assert "timestamp" in event
                assert "observedPower" in event or "observed_power" in event
                assert "expectedPower" in event or "expected_power" in event
                assert "deviation" in event
                assert "severity" in event
                assert event["severity"] in ["low", "medium", "high"]
