"""Backward-compatible entry point for the reproducible experiment command."""
from __future__ import annotations

import json

from scripts.train_models import run


if __name__ == "__main__":
    result = run()
    print(json.dumps({
        "best_model_selected_on_validation": result["best_model"],
        "one_step_test_metrics": result["models"][result["best_model"]]["test"],
        "forecast_artifact": "artifacts/selected_model.joblib",
    }, indent=2))
