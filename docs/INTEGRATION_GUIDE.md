# GridPulse Integration Guide

## Overview

This guide explains how to run the complete GridPulse system with the FastAPI backend and Next.js frontend integrated together.

## System Architecture

```
┌─────────────────┐      HTTP/REST      ┌──────────────────┐
│   Next.js       │ ◄─────────────────► │   FastAPI        │
│   Frontend      │   localhost:3000     │   Backend        │
│   (TypeScript)  │   → localhost:8000   │   (Python)       │
└─────────────────┘                      └──────────────────┘
                                                   │
                                                   ▼
                                         ┌──────────────────┐
                                         │   ML Pipeline    │
                                         │   - Features     │
                                         │   - Models       │
                                         │   - Evaluation   │
                                         └──────────────────┘
```

## Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

## Installation

### 1. Backend Setup

```bash
# From project root
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -m pytest tests/ -v
# Expected: 14 tests passing
```

### 2. Frontend Setup

```bash
# From project root
cd frontend

# Install Node dependencies
npm install

# Create environment file
cp .env.local.example .env.local

# Verify installation
npm run build
# Expected: Successful build with 8 routes prerendered
```

## Running the Application

### Terminal 1: Start Backend API

```bash
cd backend
uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify backend:**
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- Model metrics: http://localhost:8000/api/v1/model-metrics

### Terminal 2: Start Frontend

```bash
cd frontend
npm run dev
```

**Expected output:**
```
▲ Next.js 14.2.18
- Local:        http://localhost:3000
- ready started server on 0.0.0.0:3000
```

**Access the application:**
- Main dashboard: http://localhost:3000
- Model Lab: http://localhost:3000/models
- Data Health: http://localhost:3000/data-health
- Forecasting: http://localhost:3000/forecasting
- Anomalies: http://localhost:3000/anomalies

## Testing End-to-End Integration

### 1. Check Backend is Serving Real Data

Open http://localhost:8000/api/v1/model-metrics in your browser or use curl:

```bash
curl http://localhost:8000/api/v1/model-metrics
```

**Expected response:** JSON with real experiment results including:
- `bestModel`: "Histogram Gradient Boosting"
- `models`: Array with MAE/RMSE for all models
- `isDemo`: false

### 2. Check Frontend is Consuming Backend Data

1. Open http://localhost:3000/models in your browser
2. Open browser DevTools (F12) → Network tab
3. Refresh the page
4. Look for request to `localhost:8000/api/v1/model-metrics`
5. Verify:
   - Request status: 200 OK
   - Response contains real data (`isDemo: false`)
   - Page displays "Histogram Gradient Boosting" as best model
   - MAE shows 0.321 kW (real result)

### 3. Test Fallback Behavior

1. Stop the backend (Ctrl+C in Terminal 1)
2. Refresh http://localhost:3000/models
3. Verify:
   - Page still loads (uses demo data fallback)
   - Yellow demo banner appears
   - No error shown to user
4. Restart backend to restore real data

## API Endpoints

### Health Check
```
GET /health
Response: {"status": "ok"}
```

### Model Metrics
```
GET /api/v1/model-metrics
Response: ModelComparisonData with real experiment results
```

### Dataset Health
```
GET /api/v1/dataset-health
Response: DataHealthData with dataset quality metrics
```

### Overview/Dashboard
```
GET /api/v1/overview
Response: OverviewData with current power, trends, anomalies
```

## Project Structure

```
GridPulse/
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── main.py              # API endpoints
│   │   └── schemas.py           # Pydantic models
│   ├── tests/
│   │   └── test_api.py          # API tests (14 passing)
│   └── requirements.txt
│
├── frontend/                    # Next.js frontend
│   ├── app/                     # Pages (5 screens)
│   │   ├── page.tsx             # Overview dashboard
│   │   ├── models/page.tsx      # Model comparison
│   │   ├── data-health/page.tsx # Dataset quality
│   │   ├── forecasting/page.tsx # 24-hour forecast
│   │   └── anomalies/page.tsx   # Anomaly detection
│   ├── components/ui/           # Reusable components
│   ├── lib/
│   │   ├── api.ts               # API client
│   │   ├── types.ts             # TypeScript interfaces
│   │   ├── demoData.ts          # Demo data fallback
│   │   └── utils.ts             # Utilities
│   ├── .env.local               # Environment config
│   └── package.json
│
├── ml/                          # ML pipeline (used by backend)
│   ├── features.py              # Feature engineering
│   ├── baselines.py             # Baseline models
│   ├── models.py                # ML models
│   ├── evaluation.py            # Evaluation framework
│   └── data_loader.py           # Dataset loading
│
├── reports/generated/           # ML experiment results
│   └── real_data_results.json   # Real experiment output
│
└── docs/
    ├── REAL_DATA_RESULTS.md     # Experiment documentation
    └── INTEGRATION_GUIDE.md     # This file
```

## Real Data vs Demo Data

The application intelligently handles both real and demo data:

### Real Data Mode (Backend Running)
- Backend serves actual ML experiment results
- Frontend fetches from http://localhost:8000
- `isDemo: false` in API responses
- Shows actual performance metrics (e.g., 0.321 kW MAE)

### Demo Data Mode (Backend Unavailable)
- Frontend falls back to synthetic demo data
- Yellow banner indicates demo mode
- User can still explore the UI
- No errors or broken pages

## Configuration

### Backend Configuration

Edit `backend/app/main.py` to modify:
- CORS origins (currently allows localhost:3000)
- Data paths (reads from `reports/generated/real_data_results.json`)
- API base path (currently `/api/v1`)

### Frontend Configuration

Edit `frontend/.env.local`:
```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

To deploy to production, update this to your deployed backend URL.

## Troubleshooting

### Backend won't start
**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

### Frontend can't connect to backend
**Error:** Network request fails in browser console

**Check:**
1. Backend is running on port 8000
2. No CORS errors in console
3. `.env.local` has correct `NEXT_PUBLIC_API_URL`

**Solution:**
```bash
# Verify backend is responding
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

### Frontend shows demo data instead of real data
**Possible causes:**
1. Backend not running
2. Wrong API URL in `.env.local`
3. Backend returning errors

**Debug:**
1. Check browser DevTools → Network tab
2. Look for failed requests to localhost:8000
3. Check backend terminal for errors
4. Verify `reports/generated/real_data_results.json` exists

### Page shows loading forever
**Possible causes:**
1. API endpoint timeout
2. Backend process hung

**Solution:**
```bash
# Restart backend
# Terminal 1: Ctrl+C, then
cd backend
uvicorn app.main:app --reload
```

## Development Workflow

### Making Changes to Backend

1. Edit files in `backend/app/`
2. Backend auto-reloads (if using `--reload`)
3. Test changes:
```bash
cd backend
python -m pytest tests/ -v
```
4. Verify in browser

### Making Changes to Frontend

1. Edit files in `frontend/app/` or `frontend/components/`
2. Frontend auto-reloads via Fast Refresh
3. Changes appear instantly in browser
4. Run linter:
```bash
cd frontend
npm run lint
```

### Adding New API Endpoints

1. Add endpoint to `backend/app/main.py`
2. Add Pydantic schema to `backend/app/schemas.py`
3. Add tests to `backend/tests/test_api.py`
4. Add TypeScript interface to `frontend/lib/types.ts`
5. Add API function to `frontend/lib/api.ts`
6. Use in frontend component

## Next Steps

### Implement Forecasting Endpoint
The forecasting page currently shows demo data. To implement real forecasting:

1. Add 24-hour recursive prediction logic to ML pipeline
2. Create `/api/v1/forecast` endpoint in backend
3. Update `frontend/app/forecasting/page.tsx` to consume it

### Implement Anomaly Detection Endpoint
The anomalies page currently shows demo data. To implement real detection:

1. Implement threshold-based or statistical anomaly detection in ML pipeline
2. Create `/api/v1/anomalies` endpoint in backend
3. Update `frontend/app/anomalies/page.tsx` to consume it

### Deploy to Production

**Backend:**
- Use Render, Railway, or similar
- Set production CORS origins
- Use proper environment variables for secrets

**Frontend:**
- Deploy to Vercel or Netlify
- Set `NEXT_PUBLIC_API_URL` to production backend URL
- Enable production builds

## Testing

### ML Pipeline Tests
```bash
# From project root
python -m pytest tests/ -v
# Expected: 109 tests passing
```

### Backend API Tests
```bash
cd backend
python -m pytest tests/ -v
# Expected: 14 tests passing
```

### Frontend Build Test
```bash
cd frontend
npm run build
npm run lint
# Expected: No errors, successful build
```

## Performance Metrics

Based on real UCI dataset experiments:

- **Dataset:** 2,075,259 minute records → 31,631 hourly samples
- **Split:** 22,141 train / 4,745 val / 4,745 test
- **Best Model:** Histogram Gradient Boosting
  - MAE: 0.3210 kW
  - RMSE: 0.4641 kW
  - 16.4% improvement over baseline
- **Baseline:** Persistence (lag_1h)
  - MAE: 0.3840 kW
  - RMSE: 0.5822 kW

See `docs/REAL_DATA_RESULTS.md` for full details.

## Support

For issues or questions:
1. Check this guide first
2. Review error messages in terminal and browser console
3. Verify all prerequisites are installed
4. Check that ports 3000 and 8000 are not in use by other applications
