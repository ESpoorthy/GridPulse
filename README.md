# GridPulse

**ML-powered household energy forecasting, anomaly detection, and explainable consumption analytics.**

GridPulse turns historical electricity readings into a transparent 24-hour demand forecast, unusual-usage signals, and model-performance insights. It is being developed as a B.Tech Machine Learning project with an emphasis on sound evaluation, reproducibility, and an interactive product experience.

> **Project status:** Planning and dataset-validation phase. Model metrics and performance claims will be added only after experiments have run.

## What GridPulse aims to do

- Forecast the next 24 hourly average active-power values.
- Compare classical ML models against simple persistence and seasonal-naive baselines.
- Flag potentially unusual consumption patterns using a documented baseline and validation-calibrated thresholds.
- Explain forecasts and anomaly signals with historical context and feature-importance analysis where appropriate.
- Surface dataset quality, missing readings, time coverage and evaluation metrics in a responsive dashboard.

## Selected dataset

The initial experiment uses the **[UCI Individual Household Electric Power Consumption dataset](https://archive.ics.uci.edu/dataset/235/individualhouseholdelectricpowerconsumption)**.

- 2,075,259 one-minute measurements from one household in Sceaux, France.
- Observation period: December 2006 to November 2010.
- Primary target: `Global_active_power`, aggregated to hourly means (kW).
- Dataset DOI: [10.24432/C58K54](https://doi.org/10.24432/C58K54).
- License: CC BY 4.0; attribution is required.

This is a historical **single-household** dataset, not live data or a utility-grid dataset. It does not include weather data, so the first version will not claim to be weather-aware. Missing readings must be handled explicitly. See [Dataset guide](docs/DATASET.md).

**Attribution:** Hebrail, G. & Berard, A. (2006). *Individual Household Electric Power Consumption* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C58K54.

## Planned ML workflow

1. Validate timestamps, numeric values, missingness, duplicates and time coverage.
2. Aggregate minute readings into hourly values with a minimum data-coverage threshold.
3. Build leakage-safe calendar, lag and rolling-window features.
4. Evaluate persistence and seasonal-naive baselines.
5. Compare Linear Regression, Random Forest and HistGradientBoostingRegressor on chronological evaluation windows.
6. Report MAE and RMSE across multiple 24-hour forecast origins.
7. Calibrate anomaly thresholds from validation-only residuals and analyse false positives/negatives.
8. Serve the real forecast and evaluation outputs through an API and dashboard.

No performance numbers are pre-claimed. A model will only be described as an improvement if held-out evaluation supports that conclusion.

## Documentation

- [Product requirements (PRD)](PRD.md)
- [ML methodology and evaluation plan](ML_PLAN.md)
- [Dataset selection, setup and validation](docs/DATASET.md)
- [Initial architecture and API plan](docs/ARCHITECTURE.md)

## Planned technology stack

| Layer | Planned tools |
|---|---|
| Data processing and ML | Python, Pandas, NumPy, scikit-learn |
| Forecasting candidates | Linear Regression, Random Forest, HistGradientBoostingRegressor |
| Anomaly detection | Statistical/seasonal residual thresholds; Isolation Forest as an experiment if useful |
| API | FastAPI, Pydantic, Uvicorn |
| Frontend | React/Next.js, TypeScript, Tailwind CSS |
| Charts | Recharts or Plotly (final choice follows UI design) |
| Testing | pytest, frontend type-check/build checks |
| Experiment tracking | MLflow, introduced after baseline training is stable |
| Deployment candidate | Vercel frontend + Render API, after end-to-end verification |

This stack is planned, not yet an implemented or deployed system.

## Repository setup

The application code is not implemented yet. The following steps are the intended first setup sequence.

1. Create and activate a Python virtual environment.
2. Install the backend dependencies after `backend/requirements.txt` is added.
3. Download the source data from the [official UCI dataset page](https://archive.ics.uci.edu/dataset/235/individualhouseholdelectricpowerconsumption).
4. Put the extracted `household_power_consumption.txt` file at `data/raw/household_power_consumption.txt`.
5. Run the data-validation and training commands once the scripts are implemented; their exact commands will be documented with the implementation.

Raw data, processed data, model files and experiment runs should remain outside Git. Do not add secrets or private credentials to the repository.

## Scope and limitations

- Historical, single-household analysis; results may not generalise to other properties.
- No live smart-meter ingestion or automatic control in the MVP.
- An anomaly means an unusual observed pattern relative to a defined baseline; it does not prove wasted electricity or equipment failure.
- Forecast performance is not known until the holdout experiments are run.
- Any empirical uncertainty band will be labelled as such and not presented as guaranteed coverage.

## Project roadmap

- [x] Create repository and initial planning documents.
- [x] Select a primary public dataset and document its limitations.
- [ ] Validate source data and implement hourly aggregation.
- [ ] Build baselines and compare ML models with chronological evaluation.
- [ ] Implement validation-calibrated anomaly detection.
- [ ] Finalise UI/UX design and API contract.
- [ ] Implement frontend and backend integration.
- [ ] Add automated tests, measured results and deployment documentation.

## License

Application source code is released under the repository's MIT License. The UCI dataset is a separate third-party resource under CC BY 4.0 and retains its own attribution and licence requirements.
