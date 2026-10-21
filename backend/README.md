# GridPulse API

FastAPI serves the generated results from the repository's UCI household power experiment. It does not provide live meter data.

## Run locally

From the repository root:

```bash
python -m pip install -r requirements.txt
python -m pip install -r backend/requirements.txt
python scripts/train_models.py
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

The training step downloads and validates the official dataset and writes ignored artifacts under `data/`, `artifacts/`, and `reports/generated/`. Configure `GRIDPULSE_RESULTS_PATH`, `GRIDPULSE_DATA_PATH`, `GRIDPULSE_MODEL_PATH`, or `GRIDPULSE_CORS_ORIGINS` when needed. Defaults are repository-root-relative.

Interactive API docs are at `/api/docs`. Routes include health, overview, a recursive 24-hour forecast, anomalies, model metrics, and dataset health. Missing artifacts produce a clear 503 response.

Run backend tests from the repository root with `python -m pytest backend/tests`. See [development](../docs/DEVELOPMENT.md), [architecture](../docs/ARCHITECTURE.md), and [ML results](../docs/ML_RESULTS.md).
