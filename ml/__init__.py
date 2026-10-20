"""GridPulse machine learning pipeline.

This package implements the core ML components for energy forecasting:
- Feature engineering (calendar, lag, rolling features)
- Baseline models (persistence, seasonal naive)
- ML models (Linear Regression, Random Forest, HistGradientBoosting)
- Chronological evaluation framework
- Recursive 24-hour forecasting
- Residual-based anomaly detection
"""

__version__ = "0.1.0"
