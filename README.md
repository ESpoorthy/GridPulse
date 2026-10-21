# GridPulse

**Energy, Decoded.** GridPulse analyzes historical household electricity readings, compares classical one-step forecasting models, identifies unusual power observations, and presents dataset quality in a five-screen dashboard.

## What works today

- Chunked validation and minute-to-hour aggregation for the UCI Individual Household Electric Power Consumption dataset.
- Persistence and seasonal-naive baselines plus Linear Regression, Random Forest, and HistGradientBoostingRegressor.
- Chronological train/validation/test partitions. Candidates are selected by recursive 24-hour validation MAE over fixed origins every 72 hours; final one-step comparisons use the held-out test partition after refitting on train plus validation.
- Saved selected-model artifact, 24-step recursive forecast endpoint, and separate held-out recursive 24-hour evaluation with errors by horizon group.
- FastAPI endpoints for overview, forecast, anomalies, model metrics, and dataset health.
- Next.js dashboard with synthetic data available only through an explicit `?demo=1` opt-in.

The source data is one household in Sceaux, France, measured from 2006 to 2010. It is not live telemetry or grid-wide demand. The target is hourly mean active power in **kW**. See [dataset notes](docs/DATASET.md) and [implementation status](docs/IMPLEMENTATION_STATUS.md).

On the held-out period, HistGradientBoosting achieved 0.3180 kW one-step test MAE (0.4625 RMSE) and 0.4427 kW recursive 24-hour test MAE (0.5831 RMSE) across 66 forecast origins. These scores describe distinct evaluation strategies; see [full experiment results](docs/ML_RESULTS.md).

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r backend/requirements.txt
python scripts/train_models.py
```

The experiment downloads the official UCI archive (pinned SHA-256 checked), validates it, writes ignored local hourly data and quality reports, evaluates the candidates, and saves `artifacts/selected_model.joblib`. Raw data, generated reports, and model files are excluded from Git. To validate a manually obtained source file instead:

```bash
python scripts/validate_data.py --input data/raw/household_power_consumption.txt
```

Start the API from any working directory:

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Set `NEXT_PUBLIC_API_URL` for the frontend and `GRIDPULSE_CORS_ORIGINS` for the API when they are not running on localhost. API artifact paths can be overridden with `GRIDPULSE_HOURLY_DATA`, `GRIDPULSE_VALIDATION_REPORT`, `GRIDPULSE_MODEL_RESULTS`, and `GRIDPULSE_MODEL_ARTIFACT`.

To run synthetic UI fixtures intentionally, append `?demo=1` to a dashboard URL. The UI labels that mode as synthetic. Without the API and generated artifacts, real-data pages show an unavailable state.

## Verification

```bash
python -m pytest -q
python -m compileall -q backend ml scripts examples
cd frontend
npm ci
npm run lint
npx tsc --noEmit
npm run build
```

## Documentation

- [Product requirements](PRD.md)
- [ML plan](ML_PLAN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Dataset and validation](docs/DATASET.md)
- [Measured ML results](docs/ML_RESULTS.md)
- [Development and troubleshooting](docs/DEVELOPMENT.md)
- [Deployment configuration](docs/DEPLOYMENT.md)
- [Verified implementation status](docs/IMPLEMENTATION_STATUS.md)

Deployment has not been performed. Measured experiment results and run metadata are published in [ML results](docs/ML_RESULTS.md).
