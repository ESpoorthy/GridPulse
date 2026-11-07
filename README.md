# GridPulse — Energy, Decoded.

<p align="center">
  <strong>From raw electricity readings to explainable energy intelligence.</strong><br />
  A reproducible machine-learning pipeline, a FastAPI analytics service, and a five-view Next.js dashboard for historical household power analysis.
</p>

<p align="center">
  <a href="https://github.com/ESpoorthy/GridPulse/actions/workflows/python-tests.yml"><img src="https://github.com/ESpoorthy/GridPulse/actions/workflows/python-tests.yml/badge.svg?branch=main" alt="GridPulse quality checks" /></a>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white" alt="Next.js 16" />
  <img src="https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikitlearn&logoColor=white" alt="scikit-learn" />
  <img src="https://img.shields.io/badge/License-see%20LICENSE-blue.svg" alt="License" />
</p>

---

## Overview

**GridPulse** is an end-to-end energy analytics project that turns minute-level electricity measurements into validated hourly power data, recursive 24-hour forecasts, and explainable anomaly signals.

The project brings together three connected layers:

- **Machine learning:** data auditing, feature engineering, chronological model evaluation, candidate selection, and recursive forecasting.
- **Analytics API:** a FastAPI service that reads the generated experiment outputs and exposes consistent, typed endpoints.
- **Interactive dashboard:** a Next.js and React interface for exploring consumption patterns, forecasts, anomalies, model comparisons, and data quality.

GridPulse is designed to make the entire workflow inspectable and reproducible—not just to display a prediction.

> **Project scope:** the current experiment uses one historical household dataset from Sceaux, France (2006–2010). It is not live meter telemetry, campus monitoring, or a grid-wide demand forecasting system. A hosted public demo has not yet been deployed; follow the local setup below to run the application.

## What you can explore

| Dashboard view | What it shows |
|---|---|
| **Overview** | Latest available observations, recent consumption behaviour, and summary indicators derived from the processed series. |
| **Forecasting** | A recursive 24-hour hourly active-power forecast from the selected trained model. |
| **Anomaly investigation** | Observations with unusually large seasonal residuals, using thresholds calibrated on validation data. |
| **Model comparison** | Candidate-model evaluation results and the metrics used to select the final estimator. |
| **Data health** | Timestamp, duplicate, missing-reading, hourly-coverage, and excluded-period diagnostics. |

Synthetic interface fixtures are deliberately opt-in. Add `?demo=1` to a dashboard URL to view clearly labelled demo data. Normal application views use the API and do not silently replace unavailable real results with synthetic values.

## Key capabilities

### Data engineering and quality

- Downloads the official UCI dataset and verifies the pinned archive checksum.
- Validates the source in chunks rather than requiring the full raw file to be loaded into memory.
- Audits timestamp parsing, duplicate timestamps, missing readings, and hourly coverage.
- Aggregates minute-level active-power readings into hourly means.
- Marks an hour eligible only when it contains at least **45 valid minute readings**; missing target values are not imputed.
- Keeps raw data, processed data, reports, and trained model artifacts out of Git.

### Model development and evaluation

GridPulse compares five forecasting candidates:

1. Persistence baseline
2. Daily seasonal-naive baseline
3. Linear Regression
4. Random Forest Regressor
5. HistGradientBoosting Regressor

Evaluation uses chronological train, validation, and test partitions. Model selection is based on **recursive 24-hour validation MAE** at fixed forecast origins. The selected estimator is then refitted on train plus validation data before held-out evaluation.

Feature engineering includes timestamp-aligned lag features, shifted rolling statistics, and calendar encodings. The recursive forecast feeds each prediction into the next forecast step, matching the multi-step inference setting more closely than a collection of independent one-step predictions.

### Forecasting and anomaly signals

- Generates 24 consecutive future hourly forecasts using the persisted selected model.
- Compares observed power with a daily seasonal baseline to identify unusual residuals.
- Calibrates anomaly thresholds from validation residual quantiles; the held-out test set does not tune the thresholds.
- Omits prediction intervals because calibrated interval coverage has not been implemented.

An anomaly flag is a statistical signal for investigation—not a confirmed equipment fault, cause, or labelled anomaly classification.

## Measured results

The selected model is **HistGradientBoosting**. The table separates the two evaluation settings because they answer different questions.

| Evaluation | MAE | RMSE | Evaluation size |
|---|---:|---:|---:|
| One-step-ahead held-out test | **0.3180 kW** | **0.4625 kW** | 4,745 hourly test rows |
| Recursive 24-hour held-out test | **0.4427 kW** | **0.5831 kW** | 66 forecast origins / 1,584 target hours |

For model selection, HistGradientBoosting achieved a recursive 24-hour **validation MAE of 0.4814 kW**. The held-out test results are reported separately and were not used to choose the model.

### Dataset audit snapshot

| Measure | Verified result |
|---|---:|
| Source rows | 2,075,259 |
| Duplicate timestamps | 0 |
| Timestamp parse failures | 0 |
| Eligible hourly bins | 34,151 of 34,589 |
| Eligible hourly coverage | 98.73% |
| Hours excluded by the coverage rule | 438 |

The prediction target is **hourly mean active power**, so model MAE and RMSE are expressed in **kW**. These are not energy measurements in kWh.

See [the full experiment report](docs/ML_RESULTS.md) for candidate comparisons, split boundaries, horizon-group errors, calibration values, and reproduction details.

## Dataset

GridPulse uses the [UCI Individual Household Electric Power Consumption dataset](https://archive.ics.uci.edu/dataset/235/individualhouseholdelectricpowerconsumption).

- **Source:** one household in Sceaux, France.
- **Collection period:** December 2006 to November 2010.
- **Granularity:** minute-level measurements, aggregated by GridPulse to hourly values.
- **Target:** hourly mean `Global_active_power` in kW.
- **Coverage rule:** at least 45 valid minute readings are required for an eligible hour.

The dataset does not contain labelled anomaly ground truth. Consequently, anomaly precision, recall, and false-positive rates are not claimed. The results should not be interpreted as evidence of performance on other households, commercial buildings, campuses, or utility-scale grids.

More details: [Dataset and validation notes](docs/DATASET.md).

## Architecture

~~~mermaid
flowchart TD
    A["UCI minute-level household data"] --> B["Data validation and quality audit"]
    B --> C["Hourly power series"]
    B --> D["Dataset validation report"]
    C --> E["Feature engineering"]
    E --> F["Chronological train / validation / test"]
    F --> G["Five candidate forecasting models"]
    G --> H["Recursive 24-hour validation selection"]
    H --> I["Selected model and experiment metadata"]
    C --> J["FastAPI analytics service"]
    D --> J
    I --> J
    J --> K["Next.js dashboard"]
    K --> L["Overview"]
    K --> M["Forecast"]
    K --> N["Anomaly investigation"]
    K --> O["Model comparison"]
    K --> P["Data health"]
~~~

Training is an offline/reproducible workflow; model fitting does not happen inside API requests. The API serves the generated hourly data, validation report, experiment metadata, and selected model artifact.

### API reference

Start the backend locally and open the interactive API documentation at [http://localhost:8000/api/docs](http://localhost:8000/api/docs).

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Checks API and generated artifact availability. |
| `GET` | `/api/v1/overview` | Returns current summary indicators and recent observations. |
| `GET` | `/api/v1/forecast` | Returns the recursive 24-hour forecast. |
| `GET` | `/api/v1/anomalies` | Returns seasonal-residual anomaly signals. |
| `GET` | `/api/v1/model-metrics` | Returns candidate and selected-model metrics. |
| `GET` | `/api/v1/dataset-health` | Returns data-quality and coverage information. |

The API returns an unavailable/error response when required generated artifacts are missing; it does not fabricate production metrics.

## Technology stack

| Layer | Technologies |
|---|---|
| Data processing | Python, Pandas, NumPy |
| Machine learning | scikit-learn, Joblib |
| Backend | FastAPI, Pydantic, Uvicorn |
| Frontend | Next.js, React, TypeScript |
| Visualisation | Recharts |
| Quality and automation | pytest, ESLint, TypeScript, GitHub Actions |

## Run locally

### Prerequisites

- Python **3.12**
- Node.js **22** or a compatible later release
- npm
- Git

### 1. Clone the repository

~~~bash
git clone https://github.com/ESpoorthy/GridPulse.git
cd GridPulse
~~~

### 2. Create a Python environment and install dependencies

macOS / Linux:

~~~bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r backend/requirements.txt
~~~

Windows PowerShell:

~~~powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r backend/requirements.txt
~~~

### 3. Download, validate, and train

From the repository root:

~~~bash
python scripts/train_models.py
~~~

This command downloads the official UCI archive, verifies its pinned SHA-256 checksum, validates and aggregates the readings, compares the candidate models, evaluates the selected model, and writes the generated data and inference artifacts locally.

Expected generated locations include:

- `data/raw/` and `data/processed/`
- `reports/generated/`
- `artifacts/selected_model.joblib`

These are generated local artifacts and are intentionally ignored by Git. Run the training command before starting the API on a fresh machine.

### 4. Start the API

From the repository root, in terminal one:

~~~bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
~~~

API documentation: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

### 5. Configure and start the dashboard

In terminal two:

~~~bash
cp frontend/.env.example frontend/.env.local
cd frontend
npm ci
npm run dev
~~~

The example environment file points the frontend to `http://localhost:8000`. Change `NEXT_PUBLIC_API_URL` if your API runs at a different origin.

Open the dashboard at [http://localhost:3000](http://localhost:3000).

For a non-local setup, configure `GRIDPULSE_CORS_ORIGINS` on the API and `NEXT_PUBLIC_API_URL` on the frontend. Generated model and data paths can be overridden with `GRIDPULSE_HOURLY_DATA`, `GRIDPULSE_VALIDATION_REPORT`, `GRIDPULSE_MODEL_RESULTS`, and `GRIDPULSE_MODEL_ARTIFACT`.

## Verification

Run the backend and ML tests from the repository root:

~~~bash
python -m pytest -q
python -m compileall -q backend ml scripts examples tests
git diff --check
~~~

Run frontend checks from `frontend/`:

~~~bash
npm ci
npm run lint
npx tsc --noEmit
npm run build
~~~

GitHub Actions runs the Python test suite and frontend install, lint, type-check, and production-build jobs on pushes and pull requests.

## Repository structure

~~~text
GridPulse/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI routes and artifact-backed responses
│   │   └── schemas.py          # API response schemas
│   └── tests/                  # Backend API tests
├── frontend/
│   ├── app/                    # Five dashboard views
│   ├── components/             # Reusable dashboard components
│   └── lib/                    # API client, types, and explicit demo fixtures
├── ml/
│   ├── anomaly_detection.py    # Validation-calibrated anomaly signals
│   ├── baselines.py            # Persistence and seasonal-naive baselines
│   ├── data_loader.py          # Loading and hourly data preparation
│   ├── evaluation.py           # Forecast evaluation metrics
│   ├── features.py             # Time-series feature engineering
│   ├── forecasting.py          # Recursive forecasting and horizon evaluation
│   └── models.py               # Candidate model definitions
├── scripts/
│   ├── train_models.py         # Reproducible experiment pipeline
│   └── validate_data.py       # Data audit and hourly aggregation
├── tests/                      # ML and data pipeline tests
├── docs/                       # Architecture, dataset, results, deployment
├── Project_Report.pdf          # Project report
├── PRD.md                      # Product requirements
├── ML_PLAN.md                  # Modelling plan
└── README.md
~~~

## Project documentation

| Document | Description |
|---|---|
| [Project report](Project_Report.pdf) | Downloadable project report. |
| [Product requirements](PRD.md) | Project goals, scope, and requirements. |
| [ML plan](ML_PLAN.md) | Modelling and evaluation plan. |
| [Architecture](docs/ARCHITECTURE.md) | Component boundaries and data flow. |
| [Dataset notes](docs/DATASET.md) | Source data, aggregation, and quality rules. |
| [ML results](docs/ML_RESULTS.md) | Full metrics, methodology, and calibration details. |
| [Implementation status](docs/IMPLEMENTATION_STATUS.md) | Verified capabilities and known limitations. |
| [Development guide](docs/DEVELOPMENT.md) | Local development and troubleshooting. |
| [Deployment guide](docs/DEPLOYMENT.md) | Hosting prerequisites and deployment configuration. |

## Limitations and responsible interpretation

- The experiment is based on one household and historical data from 2006–2010; external generalisation has not been established.
- The application does not ingest live smart-meter or utility telemetry.
- Anomaly thresholds are calibrated statistically, but there are no labelled anomaly outcomes to calculate detection accuracy.
- Forecast prediction intervals are not displayed because interval coverage has not been calibrated.
- Deployment and hosted-environment behaviour have not yet been verified.

These boundaries are intentional: GridPulse reports what has been measured and avoids presenting unvalidated capabilities as production guarantees.

## License

See the [LICENSE](LICENSE) file for the terms of use.

---

<p align="center">
  <strong>GridPulse</strong><br />
  <em>Turning historical energy data into measurable, explainable insight.</em>
</p>
