/**
 * TypeScript type definitions for GridPulse API contracts.
 * 
 * These types define the shape of data exchanged between the frontend and
 * the planned FastAPI backend. They will be used for both:
 * - Demo data (clearly labeled as such)
 * - Future real API integration
 * 
 * All timestamps are ISO 8601 strings, all power values are in kW.
 */

// ============================================================================
// Overview / Dashboard Summary
// ============================================================================

export interface OverviewData {
  currentPower: number; // Current hourly consumption in kW
  dailyAverage: number; // Average daily consumption in kW
  weeklyTrend: 'up' | 'down' | 'stable';
  weeklyChange: number; // Percentage change
  anomalyCount: number; // Count of anomalies in recent period
  lastUpdated: string; // ISO 8601 timestamp
  dataSource: string; // e.g., "UCI Historical Data (2006-2010)"
  recentConsumption?: RecentConsumptionPoint[]; // Optional recent consumption data
  isDemo: boolean; // Flag to indicate demo data
}

export interface RecentConsumptionPoint {
  timestamp: string; // ISO 8601
  power: number; // kW
}

// ============================================================================
// Forecasting
// ============================================================================

export interface ForecastPoint {
  timestamp: string; // ISO 8601
  predicted: number; // Predicted power in kW
  lower?: number; // Lower bound (if available)
  upper?: number; // Upper bound (if available)
}

export interface HistoricalPoint {
  timestamp: string; // ISO 8601
  actual: number; // Actual power in kW
}

export interface ForecastData {
  modelName: string; // e.g., "Random Forest", "Persistence Baseline"
  horizon: number; // Forecast horizon in hours
  generatedAt: string; // ISO 8601 timestamp when forecast was generated
  historical: HistoricalPoint[]; // Recent history for context
  forecast: ForecastPoint[]; // Future predictions
  confidence?: number; // Model confidence (0-1) if available
  isDemo: boolean;
}

// ============================================================================
// Anomaly Detection
// ============================================================================

export interface AnomalyEvent {
  id: string;
  timestamp: string; // ISO 8601
  observedPower: number; // Observed value in kW
  expectedPower: number; // Expected/baseline value in kW
  deviation: number; // Percentage deviation
  severity: 'low' | 'medium' | 'high';
  reason: string; // Human-readable explanation
  confidence?: number; // Detection confidence (0-1)
}

export interface AnomalyData {
  events: AnomalyEvent[];
  totalCount: number;
  severityCounts: {
    low: number;
    medium: number;
    high: number;
  };
  detectionMethod: string; // e.g., "Seasonal Residual Threshold"
  thresholdInfo: string; // Human-readable threshold description
  period: {
    start: string; // ISO 8601
    end: string; // ISO 8601
  };
  isDemo: boolean;
}

// ============================================================================
// Model Performance / Lab
// ============================================================================

export interface ModelMetrics {
  name: string; // Model name
  mae: number; // Mean Absolute Error in kW
  rmse: number; // Root Mean Squared Error in kW
  trainSamples: number;
  testSamples: number;
  trainingTime?: number; // Seconds
  isBaseline: boolean; // True for persistence/seasonal-naive
}

export interface ModelComparisonData {
  models: ModelMetrics[];
  bestModel: string; // Name of best-performing model
  evaluationPeriod: {
    start: string; // ISO 8601
    end: string; // ISO 8601
  };
  splitRatio: string; // e.g., "70/15/15"
  isDemo: boolean;
}

export interface FeatureImportance {
  featureName: string;
  importance: number; // 0-1, relative importance
}

export interface ModelDetails {
  name: string;
  type: string; // e.g., "Random Forest", "Baseline"
  description: string;
  metrics: ModelMetrics;
  featureImportance?: FeatureImportance[]; // Only for tree-based models
  hyperparameters?: Record<string, unknown>;
}

// ============================================================================
// Dataset Health / Data Quality
// ============================================================================

export interface DataQualityMetrics {
  totalRows: number;
  validRows: number;
  missingRows: number;
  missingPercentage: number;
  dateRange: {
    start: string; // ISO 8601
    end: string; // ISO 8601
  };
  coverage: {
    totalHours: number;
    eligibleHours: number;
    coveragePercentage: number;
  };
  warnings: string[]; // List of validation warnings
  validationStatus: 'passed' | 'passed_with_warnings' | 'failed';
}

export interface PowerStatistics {
  min: number; // kW
  max: number; // kW
  mean: number; // kW
  median: number; // kW
  std: number; // kW
}

export interface DataHealthData {
  datasetName: string;
  sourceFile: string;
  quality: DataQualityMetrics;
  statistics: PowerStatistics;
  hourlyDistribution: Array<{
    hour: number; // 0-23
    avgPower: number; // kW
    sampleCount: number;
  }>;
  isDemo: boolean;
}

// ============================================================================
// API Response Wrappers
// ============================================================================

export interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  message?: string;
  timestamp: string; // ISO 8601
}

export interface ApiError {
  error: string;
  detail?: string;
  status: number;
}

// ============================================================================
// UI State Types
// ============================================================================

export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface DataState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}
