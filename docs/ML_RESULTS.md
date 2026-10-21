# ML results

## Reproduced experiment

Run on 2026-10-21 using the official [UCI Individual Household Electric Power Consumption dataset](https://archive.ics.uci.edu/dataset/235/individualhouseholdelectricpowerconsumption). The source file contains 2,075,259 rows; all timestamps parsed and no duplicate timestamps were found. The target has 2,049,280 non-missing readings. The recorded period is 2006-12-16 17:24 through 2010-11-26 21:02 (source time, with no UTC offset asserted).

Minute readings were aggregated to hourly mean active power in kW. An hour is eligible with at least 45 valid minute readings. There were 34,589 hours in the full time range, 34,151 eligible hours, and 438 excluded hours (98.73% eligible coverage). Missing target values were not imputed. The validation report records missing numeric readings and a warning; it found no timestamp gaps or duplicates.

Features use timestamp-aligned lags (1, 2, 3, 24, 48, 168 hours), shifted rolling statistics (3, 24, 168 hours), and calendar encodings. `valid_minutes` is excluded as a feature because it is unavailable for future forecast hours. The chronological partitions after feature preparation were:

| Partition | Samples | Period |
|---|---:|---|
| Train | 22,141 | 2006-12-23 18:00 to 2009-09-17 04:00 |
| Validation | 4,745 | 2009-09-17 05:00 to 2010-04-20 11:00 |
| Test | 4,745 | 2010-04-20 12:00 to 2010-11-26 20:00 |

Candidates were persistence, daily seasonal naive, Linear Regression, Random Forest (100 trees, max depth 15, minimum split 2, one worker, seed 42), and HistGradientBoosting (100 iterations, max depth 10, seed 42). Candidates were selected by recursive 24-hour validation MAE at fixed origins every 72 hours. For the separate one-step test comparison, all candidates were refit on train plus validation (26,886 samples) and scored on the same held-out test rows.

| Model | Recursive 24h validation MAE (kW) | Recursive 24h validation RMSE (kW) | One-step test MAE (kW) | One-step test RMSE (kW) |
|---|---:|---:|---:|---:|
| Persistence | 0.9077 | 1.2266 | 0.3840 | 0.5822 |
| Daily seasonal naive | 0.6359 | 0.9199 | 0.5101 | 0.7578 |
| Linear Regression | 0.5183 | 0.6935 | 0.3535 | 0.4976 |
| Random Forest | 0.4861 | 0.6654 | 0.3212 | 0.4659 |
| HistGradientBoosting | **0.4814** | **0.6491** | **0.3180** | **0.4625** |

HistGradientBoosting was selected and saved as model version `gridpulse-classical-v1`. The one-step test metrics describe rolling one-hour-ahead predictions; they are not the 24-hour score.

Recursive validation MAE by forecast step group (kW):

| Model | Hours 1–6 | Hours 7–12 | Hours 13–24 |
|---|---:|---:|---:|
| Persistence | 0.9038 | 1.0208 | 0.8531 |
| Daily seasonal naive | 0.5112 | 0.7853 | 0.6236 |
| Linear Regression | 0.4619 | 0.5677 | 0.5217 |
| Random Forest | 0.3860 | 0.5591 | 0.4997 |
| HistGradientBoosting | **0.3808** | 0.5698 | **0.4876** |

## Held-out recursive 24-hour evaluation

The selected model was evaluated on 66 complete 24-hour forecast paths over the held-out test period, representing 1,584 target hours. Origins were spaced 72 hours apart. Three origins were skipped because the target window was incomplete and five because the preceding contiguous history was too short. At each origin the model received only prior observations; its predictions were fed back for later steps.

| Held-out recursive horizon | MAE (kW) | RMSE (kW) |
|---|---:|---:|
| Hours 1–24 | 0.4427 | 0.5831 |
| Hours 1–6 | 0.4894 | 0.6048 |
| Hours 7–12 | 0.5979 | 0.7492 |
| Hours 13–24 | 0.3417 | 0.4652 |

Evaluation targets cover 2010-04-20 12:00 through 2010-11-26 11:00. The recursive test result is specific to this horizon, stride, dataset, and split; it does not imply performance on other households or live demand.

## Anomaly calibration and intervals

The detector compares observations with the 24-hour seasonal-naive value and freezes thresholds from absolute validation residual quantiles (95th, 99th, and 99.5th percentiles): low 2.0994 kW, medium 2.9938 kW, and high 3.4860 kW. The held-out test set does not tune these values. The dataset has no labeled anomaly ground truth, so precision, recall, and false-positive rates are not claimed. Event flags indicate unusual seasonal residuals, not confirmed causes.

Forecast intervals are omitted because no prediction-interval coverage calibration has been implemented.

## Reproduce

```bash
python scripts/train_models.py
python -m pytest -q
```

The command writes machine-readable experiment and validation results plus the selected inference artifact under ignored `reports/generated/`, `data/`, and `artifacts/` directories. The complete run metadata and per-model metrics are in `reports/generated/real_data_results.json`.
