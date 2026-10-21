# Deployment

GridPulse has not been deployed. The backend and frontend are separate processes suitable for a Render API and Vercel frontend, but live hosting has not been verified.

No hosting credentials, service accounts, or production environment variables are included in the repository. A deployment operator must configure the chosen providers, set the frontend `NEXT_PUBLIC_API_URL` and backend `GRIDPULSE_CORS_ORIGINS`, and provision the generated hourly CSV, validation report, experiment results, and selected model artifact through an approved artifact-storage or persistent-volume process. The UCI archive also requires outbound access during the first local training run; it is not needed at runtime when the generated artifacts are provisioned.

## Backend

Install both root and backend requirements. Start with `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`. Configure `GRIDPULSE_CORS_ORIGINS` with the exact frontend origin. Health check: `/health`.

Provide the generated hourly CSV, validation JSON, experiment JSON, and selected `joblib` artifact at the paths documented in [Development](DEVELOPMENT.md), or set `GRIDPULSE_HOURLY_DATA`, `GRIDPULSE_VALIDATION_REPORT`, `GRIDPULSE_MODEL_RESULTS`, and `GRIDPULSE_MODEL_ARTIFACT`. These files are generated locally and are not committed; the deployment must provision them through an approved persistent artifact process.

## Frontend

Install from `frontend/package-lock.json`; build with `npm run build`. Set `NEXT_PUBLIC_API_URL` to the backend origin at build time. The deployed API must permit that exact origin through `GRIDPULSE_CORS_ORIGINS`.

## Verify and troubleshoot

Check `/health`, then `/api/v1/dataset-health`, `/api/v1/model-metrics`, `/api/v1/overview`, `/api/v1/anomalies`, and `/api/v1/forecast`. Missing generated data or model files return HTTP 503. The forecast requires a persisted selected-model artifact. Do not claim a deployment until the hosted health check and all frontend screens have been checked with those real artifacts.

For a frontend smoke check, visit each of `/`, `/forecasting`, `/anomalies`, `/models`, and `/data-health`, confirm the API origin is reachable, and check that historical timestamps and power values appear with `kW` units. A missing artifact should show an unavailable state; add `?demo=1` only when intentionally checking synthetic preview mode.

If a deployment fails after release, roll back to the last known-good frontend and backend releases together, then verify that the matching hourly data and model artifacts remain available. Check platform build/runtime logs for missing Python packages, wrong working directories, unset `PORT`, CORS origin mismatch, and missing artifact paths. Do not replace missing real outputs with synthetic values in production.
