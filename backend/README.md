# GridPulse FastAPI Backend

REST API for serving GridPulse ML pipeline results to the frontend.

## Features

- ✅ **Model Performance Metrics** - Real MAE/RMSE from UCI dataset experiments
- ✅ **Data Quality Health** - Actual validation reports and statistics  
- ✅ **Dashboard Overview** - Basic consumption metrics
- ✅ **CORS Enabled** - Configured for local frontend development
- ✅ **Type-Safe** - Pydantic schemas matching frontend TypeScript contracts
- ✅ **Tested** - 14 tests covering success, validation, and error cases

## Quick Start

### 1. Install Dependencies

```bash
# From backend directory
pip install -r requirements.txt
```

### 2. Ensure Data is Available

The API serves real experiment results. Make sure you've run:

```bash
# From project root
python examples/real_data_demo.py
```

This generates:
- `reports/generated/real_data_results.json` - Model metrics
- `reports/generated/dataset_validation.json` - Data quality info
- `data/processed/hourly_power.csv` - Hourly aggregated data

### 3. Run the Server

```bash
# From backend directory
python -m uvicorn app.main:app --reload --port 8000
```

Or from project root:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Server will start at: `http://localhost:8000`

### 4. View API Documentation

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## API Endpoints

### System

- `GET /` - API root information
- `GET /health` - Health check with data/model availability

### Models

- `GET /api/v1/model-metrics` - Model performance comparison
  - Returns actual MAE/RMSE from test set
  - Includes train/test sample counts
  - Identifies best-performing model

### Data Quality

- `GET /api/v1/dataset-health` - Dataset quality metrics
  - Validation status and warnings
  - Coverage statistics
  - Hourly distribution
  - Power consumption statistics

### Dashboard

- `GET /api/v1/overview` - Dashboard summary
  - Basic consumption metrics
  - Dataset information
  - NOTE: Currently returns aggregate stats; real-time trends pending

## Response Format

All responses follow TypeScript contracts defined in `frontend/lib/types.ts`:

```json
{
  "models": [...],
  "bestModel": "Hist Gradient Boosting",
  "evaluationPeriod": {...},
  "splitRatio": "70/15/15",
  "isDemo": false
}
```

## Testing

```bash
# Run all backend tests
cd backend
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

**All 14 tests passing** ✅

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and routes
│   └── schemas.py       # Pydantic models (match frontend types)
├── tests/
│   └── test_api.py      # API endpoint tests
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Configuration

### CORS

Configured for local development:
- `http://localhost:3000` (Next.js)
- `http://127.0.0.1:3000`

For production, update allowed origins in `app/main.py`.

### Data Paths

Expects these files (relative to project root):
- `reports/generated/real_data_results.json`
- `reports/generated/dataset_validation.json`
- `data/processed/hourly_power.csv`

## Error Responses

```json
{
  "error": "Not Found",
  "detail": "Explanation of what went wrong",
  "status": 404
}
```

Common status codes:
- `200` - Success
- `404` - Endpoint not found
- `503` - Data/models not available (run experiment first)
- `500` - Internal server error

## Development

### Add New Endpoint

1. Define Pydantic schema in `schemas.py`
2. Add route in `main.py`
3. Add tests in `tests/test_api.py`
4. Update this README

### Debug Mode

```bash
uvicorn app.main:app --reload --log-level debug
```

## Dependencies

Core:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation

Testing:
- `pytest` - Test framework
- `httpx` - Async HTTP client for tests

ML (from root requirements.txt):
- `pandas`, `numpy`, `scikit-learn`

## Integration with Frontend

Frontend fetches from these endpoints to replace demo data:

```typescript
// Replace demo data
const response = await fetch('http://localhost:8000/api/v1/model-metrics');
const data: ModelComparisonData = await response.json();
```

See frontend API client in `frontend/lib/api.ts` (to be created).

## Known Limitations

### Current Implementation
- ✅ Model metrics (real data from experiments)
- ✅ Data health (real validation results)
- ✅ Basic overview (aggregate statistics)
- ⏳ Forecasting (not yet implemented)
- ⏳ Anomaly detection (not yet calibrated)
- ⏳ Recent consumption API (requires time-series loading)

### Not Implemented
- **Forecasting endpoint**: Requires decision on 1-hour vs 24-hour horizon
- **Anomaly detection**: Needs threshold calibration from validation set
- **Real-time data ingestion**: Currently serves historical experiment results
- **Authentication**: No auth required for MVP
- **Rate limiting**: Not configured
- **Caching**: Direct file reads on each request

## Production Considerations

Before deploying:
1. Update CORS allowed origins
2. Add authentication if needed
3. Implement caching for static results
4. Add rate limiting
5. Use environment variables for configuration
6. Set up monitoring/logging
7. Run behind reverse proxy (nginx)

## License

MIT License - See project root LICENSE file
