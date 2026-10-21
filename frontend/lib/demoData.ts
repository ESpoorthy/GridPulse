/**
 * Demo data for GridPulse frontend development.
 * 
 * ⚠️ THIS IS SYNTHETIC DEMO DATA FOR UI DEVELOPMENT ONLY
 * 
 * All values are clearly labeled with isDemo: true and will be replaced
 * by real API responses once the FastAPI backend is implemented.
 * 
 * Data characteristics match the UCI dataset profile:
 * - Power range: 0.2 - 11 kW (typical household range)
 * - Patterns: daily and weekly seasonality
 * - Realistic anomaly scenarios
 */

import {
  OverviewData,
  RecentConsumptionPoint,
  ForecastData,
  AnomalyData,
  AnomalyEvent,
  ModelComparisonData,
  ModelMetrics,
  DataHealthData,
  ModelDetails,
  FeatureImportance,
} from './types';

// ============================================================================
// Helper Functions
// ============================================================================

function generateTimestamp(hoursAgo: number): string {
  if (typeof window === 'undefined') {
    // Server-side: use a fixed base time for consistency
    const baseDate = new Date('2024-10-20T12:00:00Z');
    baseDate.setHours(baseDate.getHours() - hoursAgo);
    return baseDate.toISOString();
  }
  const date = new Date();
  date.setHours(date.getHours() - hoursAgo);
  return date.toISOString();
}

function generateHourlyPattern(hour: number): number {
  // Simulate daily pattern: low at night, peak in evening
  const basePattern = 0.5 + 0.3 * Math.sin((hour - 6) * Math.PI / 12);
  // Use deterministic "noise" based on hour for SSR consistency
  const noise = ((hour * 37) % 20 - 10) / 200; // Deterministic pseudo-random
  return Math.max(0.2, Math.min(5.0, basePattern * 3 + noise));
}

// ============================================================================
// Overview Data
// ============================================================================

export function getDemoOverviewData(): OverviewData {
  return {
    currentPower: 2.4,
    dailyAverage: 1.8,
    weeklyTrend: 'down',
    weeklyChange: -3.2,
    dailyObservedHours: 24,
    dailyExpectedHours: 24,
    dailyCoveragePercentage: 100,
    anomalyCount: 4,
    lastUpdated: generateTimestamp(0),
    dataSource: 'Demo Data (Synthetic)',
    isDemo: true,
  };
}

export function getDemoRecentConsumption(): RecentConsumptionPoint[] {
  const points: RecentConsumptionPoint[] = [];
  const now = typeof window === 'undefined' 
    ? new Date('2024-10-20T12:00:00Z') 
    : new Date();
  
  for (let i = 168; i >= 0; i--) {
    const timestamp = new Date(now);
    timestamp.setHours(now.getHours() - i);
    
    points.push({
      timestamp: timestamp.toISOString(),
      power: generateHourlyPattern(timestamp.getHours()),
    });
  }
  
  return points;
}

// ============================================================================
// Forecast Data
// ============================================================================

export function getDemoForecastData(): ForecastData {
  const historical = getDemoRecentConsumption().slice(-48); // Last 48 hours
  
  const baseTime = typeof window === 'undefined'
    ? new Date('2024-10-20T12:00:00Z')
    : new Date();
  
  const forecast = Array.from({ length: 24 }, (_, i) => {
    const timestamp = new Date(baseTime);
    timestamp.setHours(baseTime.getHours() + i + 1);
    const hour = timestamp.getHours();
    const predicted = generateHourlyPattern(hour);
    
    return {
      timestamp: timestamp.toISOString(),
      predicted,
      lower: predicted * 0.85,
      upper: predicted * 1.15,
    };
  });
  
  return {
    modelName: 'Random Forest (Demo)',
    horizon: 24,
    generatedAt: generateTimestamp(0),
    historical: historical.map(p => ({
      timestamp: p.timestamp,
      actual: p.power,
    })),
    forecast,
    confidence: 0.87,
    isDemo: true,
  };
}

// ============================================================================
// Anomaly Data
// ============================================================================

export function getDemoAnomalyData(): AnomalyData {
  const events: AnomalyEvent[] = [
    {
      id: 'anom-001',
      timestamp: generateTimestamp(12),
      observedPower: 6.8,
      expectedPower: 2.1,
      deviation: 224,
      severity: 'high',
      reason: 'Consumption exceeded seasonal baseline by 4.7 kW (224% above expected)',
      confidence: 0.92,
    },
    {
      id: 'anom-002',
      timestamp: generateTimestamp(36),
      observedPower: 4.2,
      expectedPower: 1.8,
      deviation: 133,
      severity: 'medium',
      reason: 'Unusual consumption during typical low-usage hours',
      confidence: 0.78,
    },
    {
      id: 'anom-003',
      timestamp: generateTimestamp(72),
      observedPower: 0.3,
      expectedPower: 2.5,
      deviation: -88,
      severity: 'medium',
      reason: 'Consumption dropped 2.2 kW below expected baseline',
      confidence: 0.85,
    },
    {
      id: 'anom-004',
      timestamp: generateTimestamp(120),
      observedPower: 5.1,
      expectedPower: 3.0,
      deviation: 70,
      severity: 'low',
      reason: 'Moderate deviation from weekly seasonal pattern',
      confidence: 0.65,
    },
  ];
  
  return {
    events,
    totalCount: events.length,
    severityCounts: {
      high: 1,
      medium: 2,
      low: 1,
    },
    detectionMethod: 'Seasonal Residual Threshold (Demo)',
    thresholdInfo: 'Anomalies detected when deviation exceeds 2.5σ from seasonal baseline',
    period: {
      start: generateTimestamp(168),
      end: generateTimestamp(0),
    },
    isDemo: true,
  };
}

// ============================================================================
// Model Comparison Data
// ============================================================================

export function getDemoModelComparisonData(): ModelComparisonData {
  const models: ModelMetrics[] = [
    {
      name: 'Persistence Baseline',
      mae: 0.523,
      rmse: 0.872,
      trainSamples: 28000,
      testSamples: 6000,
      isBaseline: true,
    },
    {
      name: 'Seasonal Naive (Daily)',
      mae: 0.445,
      rmse: 0.721,
      trainSamples: 28000,
      testSamples: 6000,
      isBaseline: true,
    },
    {
      name: 'Linear Regression',
      mae: 0.398,
      rmse: 0.654,
      trainSamples: 28000,
      testSamples: 6000,
      trainingTime: 1.2,
      isBaseline: false,
    },
    {
      name: 'Random Forest',
      mae: 0.312,
      rmse: 0.521,
      trainSamples: 28000,
      testSamples: 6000,
      trainingTime: 8.5,
      isBaseline: false,
    },
    {
      name: 'Hist Gradient Boosting',
      mae: 0.285,
      rmse: 0.478,
      trainSamples: 28000,
      testSamples: 6000,
      trainingTime: 12.3,
      isBaseline: false,
    },
  ];
  
  return {
    models,
    bestModel: 'Hist Gradient Boosting',
    evaluationPeriod: {
      start: '2010-01-01T00:00:00Z',
      end: '2010-11-26T23:00:00Z',
    },
    splitRatio: '70/15/15',
    forecastHorizon: 1,
    selectionMetric: 'synthetic one-step validation MAE',
    isDemo: true,
  };
}

export function getDemoModelDetails(modelName: string): ModelDetails {
  const comparisonData = getDemoModelComparisonData();
  const metrics = comparisonData.models.find(m => m.name === modelName);
  
  if (!metrics) {
    throw new Error(`Model ${modelName} not found`);
  }
  
  const featureImportance: FeatureImportance[] | undefined = modelName.includes('Forest') || modelName.includes('Gradient')
    ? [
        { featureName: 'lag_24h', importance: 0.32 },
        { featureName: 'lag_168h', importance: 0.24 },
        { featureName: 'rolling_mean_24h', importance: 0.18 },
        { featureName: 'hour_of_day', importance: 0.12 },
        { featureName: 'day_of_week', importance: 0.08 },
        { featureName: 'lag_1h', importance: 0.06 },
      ]
    : undefined;
  
  const hyperparameters = modelName === 'Random Forest'
    ? {
        n_estimators: 100,
        max_depth: 15,
        min_samples_split: 2,
        random_state: 42,
      }
    : modelName === 'Hist Gradient Boosting'
    ? {
        max_iter: 100,
        max_depth: 10,
        learning_rate: 0.1,
        random_state: 42,
      }
    : undefined;
  
  const descriptions: Record<string, string> = {
    'Persistence Baseline': 'Naive forecast that predicts the most recent observed value (lag_1h) will continue.',
    'Seasonal Naive (Daily)': 'Predicts the value from exactly 24 hours ago (lag_24h), capturing daily seasonality.',
    'Linear Regression': 'Linear model using calendar, lag, and rolling features with sklearn LinearRegression.',
    'Random Forest': 'Ensemble of 100 decision trees with max depth 15, trained on all engineered features.',
    'Hist Gradient Boosting': 'Histogram-based gradient boosting with 100 iterations, optimal for tabular data.',
  };
  
  return {
    name: modelName,
    type: metrics.isBaseline ? 'Baseline' : 'ML Model',
    description: descriptions[modelName] || 'Model description not available.',
    metrics,
    featureImportance,
    hyperparameters,
  };
}

// ============================================================================
// Data Health Data
// ============================================================================

export function getDemoDataHealthData(): DataHealthData {
  const hourlyDistribution = Array.from({ length: 24 }, (_, hour) => ({
    hour,
    avgPower: generateHourlyPattern(hour),
    sampleCount: 1200 + ((hour * 17) % 200), // Deterministic variation
  }));
  
  return {
    datasetName: 'Demo Household Power Consumption',
    sourceFile: 'synthetic_demo_data.csv',
    quality: {
      totalRows: 47520,
      validRows: 45890,
      missingRows: 1630,
      missingPercentage: 3.4,
      duplicateRowsExcluded: 0,
      timestampParseFailures: 0,
      missingMinuteTimestamps: 1630,
      excludedHourlyIntervals: 0,
      dateRange: {
        start: '2006-12-16T17:00:00Z',
        end: '2010-11-26T21:00:00Z',
      },
      coverage: {
        totalHours: 47520,
        eligibleHours: 45890,
        coveragePercentage: 96.6,
      },
      warnings: [
        'Demo data: Not from actual UCI dataset',
        'Synthetic patterns for UI development only',
        'Replace with real validation results',
      ],
      validationStatus: 'passed_with_warnings',
    },
    statistics: {
      min: 0.2,
      max: 10.8,
      mean: 1.92,
      median: 1.68,
      std: 1.15,
    },
    hourlyDistribution,
    isDemo: true,
  };
}

// ============================================================================
// Demo Data Flag Notice
// ============================================================================

export const DEMO_DATA_NOTICE = `⚠️ Demo Data: All displayed data is synthetic and for UI development only. 
Real data will be provided by the FastAPI backend once implemented.`;
