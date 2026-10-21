# GridPulse — Machine Learning Plan

**Status:** Implemented and measured on the full UCI source; current results are in [docs/ML_RESULTS.md](docs/ML_RESULTS.md).
**Primary task:** Univariate time-series forecasting, followed by residual-based anomaly detection.

## 1. Dataset and target

Use the UCI Individual Household Electric Power Consumption dataset. The raw file contains one-minute readings for one household from December 2006 to November 2010. The primary target column is `Global_active_power`, measured in kilowatts (kW).

Aggregate valid minute-level readings into hourly means. The prediction target is the **hourly mean active power (kW)**, not a direct measurement of grid demand or a whole-building energy bill. If needed for visual explanation, hourly energy in kWh can be estimated from mean kW over a one-hour interval, with that assumption stated.

## 2. Data preparation

1. Load the semicolon-separated raw file from `data/raw/household_power_consumption.txt`.
2. Parse date and time strictly into a timestamp; report failed parses.
3. Convert the numeric columns to numbers, treating the source missing marker (`?` or blank) as missing.
4. Sort by timestamp and report duplicated timestamps, missing timestamps and measurement missingness.
5. Aggregate `Global_active_power` to hourly mean. Keep an hour only if it has at least 45 valid one-minute power values; make this threshold configurable and report excluded hours.
6. Do not backward-fill target values from the future. Missing target hours stay missing/excluded; feature rows with unavailable required lags are dropped.
7. Validate non-negative power values and flag unexpected ranges for review instead of silently changing data.
8. Save derived data under an ignored local `data/processed/` folder.

## 3. Forecast target and horizon

For each forecast origin, predict the next 24 consecutive hourly mean active-power values. A one-step supervised estimator generates the path recursively, adding each prediction to the history used for future lag features. Candidate models are compared on common validation origins spaced 72 hours apart; the selected model is separately scored on the held-out recursive test windows.

The recursive forecast approach must be documented because error can compound across the horizon. If it performs poorly, compare a direct multi-step strategy as a later experiment rather than quietly changing the evaluation method.

## 4. Feature engineering

Candidate predictors available at a forecast origin:
- Calendar: hour of day, day of week, weekend indicator and month.
- Cyclical encodings for hour-of-day and day-of-week.
- Historical target lags: 1, 2, 3, 24, 48 and 168 hours.
- Historical rolling statistics over 3, 24 and 168 hours, calculated only from observations available before the prediction timestamp.
- The validator's `valid_minutes` quality field is not a predictor because its future values are unknown at forecast time.

**Leakage rule:** rolling features must be shifted so that the target hour is never included. Any imputation/scaling/selection that learns parameters from data must be fitted on training data only. Never use random train/test splitting for this time-series task.

## 5. Candidate models

### Baselines (mandatory)
1. **Persistence:** predict the last observed hourly value.
2. **Seasonal naive:** predict the value from 24 hours earlier.

### Classical ML candidates
3. **Linear Regression:** transparent baseline using engineered calendar and lag features.
4. **RandomForestRegressor:** nonlinear tree ensemble.
5. **HistGradientBoostingRegressor:** gradient-boosted tree baseline.

The measured candidate list remains these baselines and classical models. HistGradientBoosting was selected by recursive 24-hour validation MAE in the 2026-10-21 run. See the results report before quoting current metrics.

## 6. Validation strategy

- Preserve timestamp order.
- Begin with a chronological split of approximately 70% train, 15% validation and 15% final test, adjusted only if data quality or minimum-history requirements demand it.
- Use rolling-origin/time-series validation on the development portion where practical.
- Train candidates on the training partition and select the model using recursive validation windows; do not use the final test partition for selection.
- Evaluate every candidate at the same complete 24-hour validation origins; report aggregate and step-group performance (1–6, 7–12 and 13–24 hours).
- Refit each candidate on train plus validation for the one-step test comparison. Separately evaluate the selected model's recursive 24-hour path on complete test windows.
- Record the time periods, forecast strategy, training configuration and random seed.

## 7. Evaluation metrics

- **MAE (kW):** mean absolute difference between predicted and actual hourly mean active power.
- **RMSE (kW):** penalises larger errors more heavily.
- Optional **sMAPE (%):** include only with a documented zero/near-zero denominator handling rule.
- Compare each ML model with both mandatory baselines. The project should not call a model an improvement unless it beats a relevant baseline on held-out data.

## 8. Anomaly detection

The implemented detector uses absolute 24-hour seasonal-naive validation residual quantiles (95th, 99th and 99.5th percentiles) as frozen low/medium/high thresholds. It applies those thresholds to the latest observed window, reports timestamp, observed/expected power, absolute and relative deviation where defined, and sorts events by severity then timestamp. Expected power at or below zero has no relative percentage. The thresholds do not represent calibrated probabilities.

An anomaly is an **unusual pattern**, not proof of wasted electricity, equipment failure or malicious activity. False positives and false negatives must be discussed.

## 9. Prediction bands and explanations

A future enhancement may show empirical error bands derived from validation residual quantiles. Label these as empirical ranges, not guaranteed probabilistic coverage. Global permutation importance may explain model behaviour; do not present it as causal evidence or as a reliable per-prediction explanation.

## 10. Reproducibility and outputs

The repeatable pipeline commands are:
- validate the raw dataset and generate a data-quality summary;
- build the hourly series and time-aware features;
- train/evaluate candidate models;
- save a machine-readable metrics report and selected local model artifact;
- generate forecasts and anomaly results for the backend.

Run `python scripts/train_models.py` for validation, training, candidate comparison, report generation and selected model persistence. Run `python scripts/validate_data.py --input PATH` to validate a particular local raw file. Generated data, model binaries and reports stay outside version control.

## 11. Research and dataset references

- UCI dataset page: https://archive.ics.uci.edu/dataset/235/individualhouseholdelectricpowerconsumption
- Dataset DOI: https://doi.org/10.24432/C58K54
- License: CC BY 4.0; attribution is required when redistributing adapted material.
