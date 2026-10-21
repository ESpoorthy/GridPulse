# Development

## Setup

Use Python 3.12 or later and Node.js 22. Install Python dependencies with `python -m pip install -r requirements.txt -r backend/requirements.txt`; install frontend dependencies with `cd frontend && npm ci`.

## Data and artifacts

`python scripts/train_models.py` is the reproducible end-to-end local workflow. It downloads the UCI source when absent, verifies the archive checksum, validates timestamps and readings, aggregates hourly power using a 45-valid-minute threshold, evaluates the models, and writes local outputs under `data/`, `reports/generated/`, and `artifacts/`. These outputs are ignored by Git.

The downloader pins the current SHA-256 digest of the UCI archive. A checksum mismatch stops processing and removes the partial archive; never disable verification to work around a mismatch. The UCI endpoint's current archive digest replaced a stale MD5 in the earlier implementation.

The validator keeps the first source row per duplicate timestamp and excludes later duplicate rows from hourly aggregation. It reports how many duplicate rows were excluded. Missing target readings are never imputed. Eligible hourly means have between 45 and 60 valid minute readings.

Candidates are selected by recursive 24-hour validation MAE at fixed origins every 72 hours. Each candidate then receives one-step held-out test metrics after refitting on train plus validation; the selected candidate also receives a separate recursive 24-hour held-out evaluation. Horizon groups and skipped windows are recorded. Anomaly thresholds use the 95th, 99th, and 99.5th percentiles of absolute 24-hour seasonal-naive residuals in the validation partition.

## Run services

Start the API from the repository root with `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`. Start the frontend with `cd frontend && npm run dev`; set `NEXT_PUBLIC_API_URL` when the API is elsewhere. Real pages require generated data, validation, and model outputs. Add `?demo=1` to opt into synthetic preview fixtures.

## Checks

Run `python -m pytest -q`, `python -m compileall -q backend ml scripts examples`, then in `frontend/` run `npm ci`, `npm run lint`, `npx tsc --noEmit`, and `npm run build`.
