/**
 * API client for GridPulse backend.
 * 
 * Fetches real data from FastAPI. Synthetic fixtures are selected explicitly
 * by the page only when the URL contains ?demo=1.
 */

import {
  ModelComparisonData,
  DataHealthData,
  OverviewData,
  ForecastData,
  AnomalyData,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// API response types (snake_case from backend)
interface ApiAnomalyEvent {
  id: string;
  timestamp: string;
  observed_power?: number;
  expected_power?: number;
  deviation?: number | null;
  severity: 'low' | 'medium' | 'high';
  reason: string;
  confidence?: number;
}

interface ApiAnomalyData {
  events: ApiAnomalyEvent[];
  total_count: number;
  severity_counts: {
    low: number;
    medium: number;
    high: number;
  };
  detection_method: string;
  threshold_info: string;
  period: {
    start: string;
    end: string;
  };
  is_demo: boolean;
}

interface ApiModelMetrics {
  name: string;
  mae: number;
  rmse: number;
  train_samples: number;
  test_samples: number;
  training_time?: number;
  is_baseline: boolean;
  recursive_validation?: {
    mae: number;
    rmse: number;
    forecast_origins: number;
    evaluated_hours: number;
    evaluation_period: { start: string; end: string };
    step_group_metrics: Record<string, { mae: number; rmse: number }>;
  } | null;
}

interface ApiModelComparisonData {
  models: ApiModelMetrics[];
  best_model: string;
  evaluation_period: {
    start: string;
    end: string;
  };
  split_ratio: string;
  is_demo: boolean;
  forecast_horizon: number;
  selection_metric: string;
  recursive_test?: ModelComparisonData['recursiveTest'];
}

interface ApiDataHealthData {
  dataset_name: string;
  source_file: string;
  quality: {
    total_rows: number;
    valid_rows: number;
    missing_rows: number;
    missing_percentage: number;
    duplicate_rows_excluded: number;
    timestamp_parse_failures: number;
    missing_minute_timestamps: number;
    excluded_hourly_intervals: number;
    date_range: {
      start: string;
      end: string;
    };
    coverage: {
      total_hours: number;
      eligible_hours: number;
      coverage_percentage: number;
    };
    warnings: string[];
    validation_status: 'passed' | 'passed_with_warnings' | 'failed';
  };
  statistics: {
    min: number;
    max: number;
    mean: number;
    median: number;
    std: number;
  };
  hourly_distribution: Array<{
    hour: number;
    avg_power: number;
    sample_count: number;
  }>;
  is_demo: boolean;
}

interface ApiOverviewData {
  current_power: number;
  daily_average: number;
  weekly_trend: 'up' | 'down' | 'stable';
  weekly_change: number;
  daily_observed_hours: number;
  daily_expected_hours: number;
  daily_coverage_percentage: number;
  anomaly_count: number;
  last_updated: string;
  data_source: string;
  recent_consumption?: Array<{
    timestamp: string;
    power: number;
  }>;
  is_demo: boolean;
}

interface ApiForecastData {
  model_name: string;
  horizon: number;
  generated_at: string;
  historical: Array<{
    timestamp: string;
    actual: number;
  }>;
  forecast: Array<{
    timestamp: string;
    predicted: number;
    lower?: number;
    upper?: number;
  }>;
  confidence?: number;
  is_demo: boolean;
}

/**
 * Generic fetch wrapper with error handling.
 */
async function apiFetch<T>(endpoint: string): Promise<T | null> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Don't cache during development
      cache: 'no-store',
    });
    
    if (!response.ok) {
      console.error(`API error: ${response.status} ${response.statusText}`);
      return null;
    }
    
    return await response.json();
  } catch (error) {
    console.error(`Failed to fetch ${endpoint}:`, error);
    return null;
  }
}

/**
 * Check if backend is available.
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      cache: 'no-store',
    });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Fetch model comparison data.
 */
export async function fetchModelMetrics(): Promise<ModelComparisonData | null> {
  const data = await apiFetch<ApiModelComparisonData>('/api/v1/model-metrics');
  
  if (!data) return null;
  
  // Transform snake_case API response to camelCase frontend types
  return {
    models: (data.models || []).map((model) => ({
      name: model.name,
      mae: model.mae ?? 0,
      rmse: model.rmse ?? 0,
      trainSamples: model.train_samples ?? 0,
      testSamples: model.test_samples ?? 0,
      trainingTime: model.training_time,
      isBaseline: model.is_baseline ?? false,
      recursiveValidation: model.recursive_validation ? {
        mae: model.recursive_validation.mae,
        rmse: model.recursive_validation.rmse,
        forecastOrigins: model.recursive_validation.forecast_origins,
        evaluatedHours: model.recursive_validation.evaluated_hours,
        evaluationPeriod: model.recursive_validation.evaluation_period,
        stepGroupMetrics: model.recursive_validation.step_group_metrics,
      } : null,
    })),
    bestModel: data.best_model ?? '',
    evaluationPeriod: {
      start: data.evaluation_period?.start ?? '',
      end: data.evaluation_period?.end ?? '',
    },
    splitRatio: data.split_ratio ?? '',
    forecastHorizon: data.forecast_horizon ?? 1,
    selectionMetric: data.selection_metric ?? 'one-step validation MAE',
    recursiveTest: data.recursive_test ?? null,
    isDemo: data.is_demo ?? false,
  };
}

/**
 * Fetch data health metrics.
 */
export async function fetchDataHealth(): Promise<DataHealthData | null> {
  const data = await apiFetch<ApiDataHealthData>('/api/v1/dataset-health');
  
  if (!data) return null;
  
  // Transform snake_case API response to camelCase frontend types
  return {
    datasetName: data.dataset_name ?? 'Unknown',
    sourceFile: data.source_file ?? '',
    quality: {
      totalRows: data.quality?.total_rows ?? 0,
      validRows: data.quality?.valid_rows ?? 0,
      missingRows: data.quality?.missing_rows ?? 0,
      missingPercentage: data.quality?.missing_percentage ?? 0,
      duplicateRowsExcluded: data.quality?.duplicate_rows_excluded ?? 0,
      timestampParseFailures: data.quality?.timestamp_parse_failures ?? 0,
      missingMinuteTimestamps: data.quality?.missing_minute_timestamps ?? 0,
      excludedHourlyIntervals: data.quality?.excluded_hourly_intervals ?? 0,
      dateRange: {
        start: data.quality?.date_range?.start ?? '',
        end: data.quality?.date_range?.end ?? '',
      },
      coverage: {
        totalHours: data.quality?.coverage?.total_hours ?? 0,
        eligibleHours: data.quality?.coverage?.eligible_hours ?? 0,
        coveragePercentage: data.quality?.coverage?.coverage_percentage ?? 0,
      },
      warnings: data.quality?.warnings || [],
      validationStatus: data.quality?.validation_status ?? 'failed',
    },
    statistics: {
      min: data.statistics?.min ?? 0,
      max: data.statistics?.max ?? 0,
      mean: data.statistics?.mean ?? 0,
      median: data.statistics?.median ?? 0,
      std: data.statistics?.std ?? 0,
    },
    hourlyDistribution: (data.hourly_distribution || []).map((item) => ({
      hour: item.hour ?? 0,
      avgPower: item.avg_power ?? 0,
      sampleCount: item.sample_count ?? 0,
    })),
    isDemo: data.is_demo ?? false,
  };
}

/**
 * Fetch overview/dashboard data.
 */
export async function fetchOverview(): Promise<OverviewData | null> {
  const data = await apiFetch<ApiOverviewData>('/api/v1/overview');
  
  if (!data) return null;
  
  // Transform snake_case API response to camelCase frontend types
  return {
    currentPower: data.current_power ?? 0,
    dailyAverage: data.daily_average ?? 0,
    weeklyTrend: data.weekly_trend ?? 'stable',
    weeklyChange: data.weekly_change ?? 0,
    dailyObservedHours: data.daily_observed_hours ?? 0,
    dailyExpectedHours: data.daily_expected_hours ?? 0,
    dailyCoveragePercentage: data.daily_coverage_percentage ?? 0,
    anomalyCount: data.anomaly_count ?? 0,
    lastUpdated: data.last_updated ?? new Date().toISOString(),
    dataSource: data.data_source ?? 'Unknown',
    recentConsumption: data.recent_consumption?.map((point) => ({
      timestamp: point.timestamp,
      power: point.power ?? 0,
    })),
    isDemo: data.is_demo ?? false,
  };
}

/**
 * Fetch 24-hour forecast.
 */
export async function fetchForecast(): Promise<ForecastData | null> {
  const data = await apiFetch<ApiForecastData>('/api/v1/forecast');
  
  if (!data) return null;
  
  // Transform snake_case API response to camelCase frontend types
  return {
    modelName: data.model_name ?? 'Unknown',
    horizon: data.horizon ?? 24,
    generatedAt: data.generated_at ?? new Date().toISOString(),
    historical: (data.historical || []).map((point) => ({
      timestamp: point.timestamp,
      actual: point.actual ?? 0,
    })),
    forecast: (data.forecast || []).map((point) => ({
      timestamp: point.timestamp,
      predicted: point.predicted ?? 0,
      lower: point.lower,
      upper: point.upper,
    })),
    confidence: data.confidence,
    isDemo: data.is_demo ?? false,
  };
}

/**
 * Fetch detected anomalies.
 */
export async function fetchAnomalies(): Promise<AnomalyData | null> {
  const data = await apiFetch<ApiAnomalyData>('/api/v1/anomalies');
  
  if (!data) return null;
  
  // Transform snake_case API response to camelCase frontend types
  return {
    events: (data.events || []).map((event) => ({
      id: event.id,
      timestamp: event.timestamp,
      observedPower: event.observed_power ?? 0,
      expectedPower: event.expected_power ?? 0,
      deviation: event.deviation ?? null,
      severity: event.severity,
      reason: event.reason,
      confidence: event.confidence,
    })),
    totalCount: data.total_count ?? 0,
    severityCounts: {
      low: data.severity_counts?.low ?? 0,
      medium: data.severity_counts?.medium ?? 0,
      high: data.severity_counts?.high ?? 0,
    },
    detectionMethod: data.detection_method ?? 'Unknown',
    thresholdInfo: data.threshold_info ?? '',
    period: {
      start: data.period?.start ?? '',
      end: data.period?.end ?? '',
    },
    isDemo: data.is_demo ?? false,
  };
}
