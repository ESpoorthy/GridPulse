# Implementation status

**Verified:** 2026-10-21

## Completed and locally verified

- Data validation audits the official UCI source, excludes later duplicate timestamps from aggregation, reports reading and time coverage, and keeps generated data out of Git. The verified full source had 2,075,259 rows, zero duplicate timestamps, 34,151 eligible hourly bins out of 34,589, and 438 hours excluded by the 45-minute rule.
- Training compares persistence, daily seasonal naive, Linear Regression, Random Forest, and HistGradientBoosting with chronological partitions. Selection uses recursive 24-hour validation MAE on the same fixed origins every 72 hours; the selected estimator is refit and saved with its feature columns and experiment metadata.
- The selected-model recursive 24-hour held-out evaluation completed on 66 origins / 1,584 hours. The full metrics, step groups, partitions, skipped-window counts, and validation-only anomaly thresholds are recorded in [ML results](ML_RESULTS.md).
- FastAPI serves dynamic overview, forecast, anomaly, model-comparison, and dataset-health responses from generated artifacts. All six API routes were smoke-tested against the real generated files; the forecast returned 24 consecutive future timestamps with intervals unavailable, as intended.
- The five Next.js dashboard routes fetch API data. Synthetic previews require `?demo=1` and are labeled. The production build, lint, and type-check pass. Browser inspection of all five routes with the real local API artifacts confirmed API-backed values and unavailable forecast intervals. The sidebar's static anomaly count and invented analyst profile were removed after inspection.
- Obsolete status and integration guides were consolidated into the canonical docs. GitHub Actions now contains Python and frontend jobs on pushes and pull requests.

## Verification results

- `python3 -m pytest -q`: 138 passed. One third-party joblib warning remains because the sandbox prevents physical-core detection.
- `python3 -m compileall -q backend ml scripts examples tests`: passed.
- `npm ci`: passed using an isolated npm cache.
- `npm run lint`, `npx tsc --noEmit`, and `npm run build`: passed; all five application routes were statically generated.
- `npm audit --omit=dev`: 0 vulnerabilities. Full `npm audit` reports five high-severity entries for one `braces` stack-exhaustion advisory in the development-only `eslint-config-next` → `@next/eslint-plugin-next` → `fast-glob` → `micromatch` → `braces` chain. The registry has no patched `braces` release; npm's only suggested fix force-downgrades `eslint-config-next` to 14.2.35, a breaking change. Production dependencies are unaffected. Until a compatible upstream fix is available, keep CI permissions read-only, do not expose secrets to PR lint jobs, and update the chain when a patched release is published.
- `git diff --check`: passed. Generated source data, reports, model files, caches, `node_modules`, and `.next` are ignored.

## Remaining external checks and limits

- No deployment was performed; platform credentials and hosted artifact provisioning were not available in this task. See [deployment notes](DEPLOYMENT.md).
- GitHub Actions is configured to run Python tests and frontend install, lint, type-check, and production build on pushes and pull requests. Hosted execution status is tracked in GitHub checks; local results in this document are not presented as remote CI results.
- No deployment or mobile/responsive breakpoint review was performed. Browser inspection used the local production build and the generated UCI artifacts only.
- The UCI source has no labeled anomaly ground truth. Detection flags do not support precision/recall or causal claims. Forecast prediction intervals remain unavailable.
- The dataset is a single historical household series (2006–2010), not current campus or grid telemetry.

Changes are prepared on branch `codex/gridpulse-quality-overhaul`. No deployment was performed.
