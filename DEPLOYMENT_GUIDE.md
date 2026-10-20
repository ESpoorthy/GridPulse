# GridPulse Deployment Guide

## Overview

This guide explains how to deploy GridPulse to production. The application consists of:
- **Backend:** FastAPI (Python 3.9+)
- **Frontend:** Next.js 16 (Node.js 18+)

## Pre-Deployment Checklist

### ✅ Completed
- [x] ML pipeline complete (109 tests passing)
- [x] Backend API complete (18 tests passing)
- [x] Frontend complete (production build successful)
- [x] All 5 screens integrated with API
- [x] Forecast endpoint implemented
- [x] Anomaly detection endpoint implemented
- [x] Demo data fallback working
- [x] Loading and error states implemented
- [x] CORS configured
- [x] Environment variables documented

### ⚠️ Before Deploying
- [ ] Run real UCI experiment to generate data files
- [ ] Decide on persistent storage for processed data
- [ ] Set production CORS origins
- [ ] Configure production API URL
- [ ] Set up environment secrets
- [ ] Choose deployment platform
- [ ] Configure custom domain (optional)

## Local Development

### Start Backend
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Runs at:** http://localhost:8000  
**API docs:** http://localhost:8000/api/docs

### Start Frontend
```bash
cd frontend
npm run dev
```

**Runs at:** http://localhost:3000

### Environment Variables

**Backend:**
No environment variables required for local development. Data is read from:
- `reports/generated/real_data_results.json`
- `reports/generated/dataset_validation.json`
- `data/processed/hourly_power.csv`

**Frontend:**
Create `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Deployment Options

### Option 1: Render + Vercel (Recommended)

#### Backend on Render

1. **Create Render account** at https://render.com

2. **Create new Web Service:**
   - Connect your GitHub repository
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment: Python 3.11

3. **Upload Data Files:**
   Since data files are git-ignored, you'll need to:
   - Run `python examples/real_data_demo.py` locally
   - Upload generated files to Render's persistent disk or object storage
   - Or: re-run data processing on Render (requires 20MB download)

4. **Set Environment Variables on Render:**
   ```bash
   PYTHON_VERSION=3.11
   # Add production CORS origins
   ```

5. **Update CORS in `backend/app/main.py`:**
   ```python
   allow_origins=[
       "https://your-frontend.vercel.app",
       "http://localhost:3000",  # Keep for local dev
   ]
   ```

#### Frontend on Vercel

1. **Create Vercel account** at https://vercel.com

2. **Import project:**
   - Connect GitHub repository
   - Root Directory: `frontend`
   - Framework Preset: Next.js
   - Build Command: `npm run build`
   - Output Directory: `.next`

3. **Set Environment Variable:**
   ```bash
   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
   ```

4. **Deploy:**
   - Vercel will auto-deploy on git push
   - Frontend will be available at `https://your-project.vercel.app`

### Option 2: Railway (Full Stack)

1. **Create Railway account** at https://railway.app

2. **Create New Project** → Deploy from GitHub

3. **Add Backend Service:**
   - Service Name: `gridpulse-backend`
   - Root Directory: `backend`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Python 3.11

4. **Add Frontend Service:**
   - Service Name: `gridpulse-frontend`
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Start Command: `npm start`
   - Environment: `NEXT_PUBLIC_API_URL=${{gridpulse-backend.RAILWAY_STATIC_URL}}`

5. **Configure Networking:**
   - Make both services publicly accessible
   - Update backend CORS with frontend URL

### Option 3: Docker + Your Platform

#### Backend Dockerfile

Create `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy ML modules (needed by backend)
COPY ml/ ../ml/

# Copy data files (or mount as volume)
COPY reports/ ../reports/
COPY data/processed/ ../data/processed/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile

Create `frontend/Dockerfile`:
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./
RUN npm install

# Copy frontend code
COPY frontend/ .

# Build
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

#### Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./reports:/app/reports
    environment:
      - PYTHONUNBUFFERED=1
  
  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
```

**Run:**
```bash
docker-compose up -d
```

## Data Management

### Option A: Process Data at Build Time
- Include `python examples/real_data_demo.py` in your build script
- Downloads UCI data (20MB) and processes it
- Generates results and validation files
- **Pros:** Fully reproducible
- **Cons:** Slower builds, requires network access

### Option B: Upload Pre-Processed Data
- Run locally: `python examples/real_data_demo.py`
- Upload generated files to deployment platform
- **Files needed:**
  - `reports/generated/real_data_results.json`
  - `reports/generated/dataset_validation.json`
  - `data/processed/hourly_power.csv`
- **Pros:** Fast builds
- **Cons:** Manual step required

### Option C: Cloud Storage
- Store processed data in S3/GCS/Azure Blob
- Backend loads from cloud storage on startup
- Requires adding cloud SDK to requirements
- **Pros:** Scalable, persistent
- **Cons:** Additional cost and complexity

## Security Considerations

### Secrets Management
- Never commit `.env` files
- Use platform secret management (Render, Vercel, Railway all provide this)
- Keep `.gitignore` updated

### CORS Configuration
- Update `backend/app/main.py` with production frontend URL
- Remove `localhost` origins in production
- Example:
  ```python
  allow_origins=[
      "https://gridpulse.vercel.app",
      "https://www.yourdomain.com",
  ]
  ```

### API Rate Limiting (Optional)
Add to `backend/app/main.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/v1/forecast")
@limiter.limit("10/minute")
async def get_forecast():
    ...
```

## Monitoring & Health Checks

### Health Check Endpoint
Already implemented at `/health`

Platform configurations:
- **Render:** Auto-detected
- **Railway:** Configure health check path: `/health`
- **Docker:** Add HEALTHCHECK in Dockerfile:
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"
  ```

### Logging
Both backend and frontend log to stdout. Configure your platform to:
- Collect logs
- Set up log retention
- Create alerts for errors

### Metrics to Monitor
- API response times
- Error rates (4xx, 5xx)
- Frontend page load times
- API endpoint usage

## Post-Deployment Verification

### 1. Backend Health
```bash
curl https://your-backend.onrender.com/health
# Should return: {"status":"healthy","version":"1.0.0",...}
```

### 2. API Endpoints
```bash
curl https://your-backend.onrender.com/api/v1/model-metrics
curl https://your-backend.onrender.com/api/v1/dataset-health
curl https://your-backend.onrender.com/api/v1/forecast
curl https://your-backend.onrender.com/api/v1/anomalies
```

### 3. Frontend Access
- Visit frontend URL
- Check all 5 pages load
- Verify no yellow "demo data" banner (means API connected)
- Check browser console for errors

### 4. Integration Test
- Open Model Lab page
- Verify shows "Histogram Gradient Boosting" as best model
- Verify MAE shows 0.321 kW
- Check that data is marked `isDemo: false`

## Rollback Plan

If deployment fails:

1. **Frontend Issues:**
   - Vercel: Revert to previous deployment from dashboard
   - Railway: Redeploy previous commit

2. **Backend Issues:**
   - Check logs for errors
   - Verify data files are present
   - Check CORS configuration
   - Rollback to previous deployment

3. **Nuclear Option:**
   - Keep local development environment running
   - Frontend can fall back to demo data
   - Fix issues, redeploy when ready

## Custom Domain (Optional)

### Frontend (Vercel)
1. Go to Project Settings → Domains
2. Add your domain (e.g., `gridpulse.com`)
3. Configure DNS records as instructed

### Backend (Render)
1. Go to Service Settings → Custom Domains
2. Add domain (e.g., `api.gridpulse.com`)
3. Configure DNS records

### Update Environment Variables
```bash
# Frontend .env
NEXT_PUBLIC_API_URL=https://api.gridpulse.com

# Backend CORS
allow_origins=["https://gridpulse.com"]
```

## Cost Estimates

### Free Tier (Development/Demo)
- **Render Free:** 750 hours/month (sleeps after inactivity)
- **Vercel Hobby:** Unlimited (personal projects)
- **Total:** $0/month

### Paid Tier (Production)
- **Render Starter:** $7/month (always-on)
- **Vercel Pro:** $20/month (team features)
- **Total:** ~$27/month

### With Custom Domain
- **Domain:** ~$12/year (Namecheap, Google Domains)
- **SSL:** Free (Let's Encrypt via platform)

## Troubleshooting

### "Service Unavailable" (503)
- Data files missing
- Run `python examples/real_data_demo.py` to generate them
- Or upload pre-processed files

### "CORS Error"
- Backend `allow_origins` doesn't include frontend URL
- Update `backend/app/main.py` and redeploy

### "Demo Data" Banner Shows
- Frontend can't reach backend
- Check `NEXT_PUBLIC_API_URL` environment variable
- Verify backend is running and accessible

### Slow Cold Starts
- Free tiers sleep after inactivity
- First request wakes service (10-30 seconds)
- Solution: Upgrade to paid tier or add keep-alive ping

## Support & Documentation

- **API Docs:** https://your-backend.onrender.com/api/docs
- **Frontend:** https://your-frontend.vercel.app
- **Status Page:** Check platform status pages
- **Logs:** Check platform dashboards

## Next Steps After Deployment

1. **Share the URL** with stakeholders
2. **Monitor usage** for first few days
3. **Collect feedback** on UI/UX
4. **Plan v2 features:**
   - Real-time updates
   - User authentication
   - Historical forecast comparison
   - Export functionality (CSV, PDF)
   - Advanced anomaly explanations

## License & Attribution

Remember to attribute the UCI dataset:
> Data source: Hebrail, G. & Berard, A. (2006). Individual Household Electric Power Consumption [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C58K54. Licensed under CC BY 4.0.

Add this to your frontend footer or about page.
