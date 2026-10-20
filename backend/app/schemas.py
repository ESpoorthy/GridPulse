"""
Pydantic schemas for GridPulse API responses.

These schemas match the TypeScript interfaces defined in frontend/lib/types.ts
to ensure type safety across the full stack.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Model Performance / Lab
# ============================================================================

class ModelMetrics(BaseModel):
    """Metrics for a single model."""
    name: str
    mae: float = Field(..., description="Mean Absolute Error in kW")
    rmse: float = Field(..., description="Root Mean Squared Error in kW")
    trainSamples: int = Field(..., alias="train_samples")
    testSamples: int = Field(..., alias="test_samples")
    trainingTime: Optional[float] = Field(None, alias="training_time", description="Training time in seconds")
    isBaseline: bool = Field(..., alias="is_baseline")
    
    class Config:
        populate_by_name = True


class ModelComparisonResponse(BaseModel):
    """Response for model comparison endpoint."""
    models: List[ModelMetrics]
    bestModel: str = Field(..., alias="best_model")
    evaluationPeriod: dict = Field(..., alias="evaluation_period")
    splitRatio: str = Field(..., alias="split_ratio")
    isDemo: bool = Field(default=False, alias="is_demo")
    
    class Config:
        populate_by_name = True


# ============================================================================
# Data Health / Quality
# ============================================================================

class DataQualityMetrics(BaseModel):
    """Data quality metrics."""
    totalRows: int = Field(..., alias="total_rows")
    validRows: int = Field(..., alias="valid_rows")
    missingRows: int = Field(..., alias="missing_rows")
    missingPercentage: float = Field(..., alias="missing_percentage")
    dateRange: dict = Field(..., alias="date_range")
    coverage: dict
    warnings: List[str]
    validationStatus: str = Field(..., alias="validation_status")
    
    class Config:
        populate_by_name = True


class PowerStatistics(BaseModel):
    """Power consumption statistics."""
    min: float = Field(..., description="Minimum power in kW")
    max: float = Field(..., description="Maximum power in kW")
    mean: float = Field(..., description="Mean power in kW")
    median: float = Field(..., description="Median power in kW")
    std: float = Field(..., description="Standard deviation in kW")


class HourlyDistribution(BaseModel):
    """Hourly distribution data point."""
    hour: int = Field(..., ge=0, le=23)
    avgPower: float = Field(..., alias="avg_power")
    sampleCount: int = Field(..., alias="sample_count")
    
    class Config:
        populate_by_name = True


class DataHealthResponse(BaseModel):
    """Response for data health endpoint."""
    datasetName: str = Field(..., alias="dataset_name")
    sourceFile: str = Field(..., alias="source_file")
    quality: DataQualityMetrics
    statistics: PowerStatistics
    hourlyDistribution: List[HourlyDistribution] = Field(..., alias="hourly_distribution")
    isDemo: bool = Field(default=False, alias="is_demo")
    
    class Config:
        populate_by_name = True


# ============================================================================
# Overview / Dashboard
# ============================================================================

class OverviewResponse(BaseModel):
    """Response for overview/dashboard endpoint."""
    currentPower: float = Field(..., alias="current_power", description="Current hourly consumption in kW")
    dailyAverage: float = Field(..., alias="daily_average")
    weeklyTrend: Literal['up', 'down', 'stable'] = Field(..., alias="weekly_trend")
    weeklyChange: float = Field(..., alias="weekly_change")
    anomalyCount: int = Field(..., alias="anomaly_count")
    lastUpdated: str = Field(..., alias="last_updated")
    dataSource: str = Field(..., alias="data_source")
    isDemo: bool = Field(default=False, alias="is_demo")
    
    class Config:
        populate_by_name = True


class RecentConsumptionPoint(BaseModel):
    """Single consumption data point."""
    timestamp: str
    power: float = Field(..., description="Power in kW")


# ============================================================================
# Health Check
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="API status")
    version: str = Field(..., description="API version")
    dataAvailable: bool = Field(..., alias="data_available")
    modelsLoaded: bool = Field(..., alias="models_loaded")
    
    class Config:
        populate_by_name = True


# ============================================================================
# Forecasting
# ============================================================================

class ForecastPoint(BaseModel):
    """Single forecast point."""
    timestamp: str
    predicted: float = Field(..., description="Predicted power in kW")
    lower: Optional[float] = Field(None, description="Lower confidence bound in kW")
    upper: Optional[float] = Field(None, description="Upper confidence bound in kW")


class HistoricalPoint(BaseModel):
    """Single historical observation point."""
    timestamp: str
    actual: float = Field(..., description="Actual power in kW")


class ForecastResponse(BaseModel):
    """Response for forecast endpoint."""
    modelName: str = Field(..., alias="model_name")
    horizon: int = Field(..., description="Forecast horizon in hours")
    generatedAt: str = Field(..., alias="generated_at")
    historical: List[HistoricalPoint] = Field(..., description="Recent history for context")
    forecast: List[ForecastPoint] = Field(..., description="Future predictions")
    confidence: Optional[float] = Field(None, description="Model confidence (0-1)")
    isDemo: bool = Field(default=False, alias="is_demo")
    
    class Config:
        populate_by_name = True


# ============================================================================
# Anomaly Detection
# ============================================================================

class AnomalyEvent(BaseModel):
    """Single anomaly event."""
    id: str
    timestamp: str
    observedPower: float = Field(..., alias="observed_power", description="Observed value in kW")
    expectedPower: float = Field(..., alias="expected_power", description="Expected/baseline value in kW")
    deviation: float = Field(..., description="Percentage deviation")
    severity: Literal['low', 'medium', 'high']
    reason: str = Field(..., description="Human-readable explanation")
    confidence: Optional[float] = Field(None, description="Detection confidence (0-1)")
    
    class Config:
        populate_by_name = True


class AnomalyResponse(BaseModel):
    """Response for anomaly detection endpoint."""
    events: List[AnomalyEvent]
    totalCount: int = Field(..., alias="total_count")
    severityCounts: dict = Field(..., alias="severity_counts")
    detectionMethod: str = Field(..., alias="detection_method")
    thresholdInfo: str = Field(..., alias="threshold_info")
    period: dict
    isDemo: bool = Field(default=False, alias="is_demo")
    
    class Config:
        populate_by_name = True


# ============================================================================
# Error Response
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    status: int
