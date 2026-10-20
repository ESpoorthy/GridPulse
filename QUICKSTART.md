# GridPulse - Quick Start Guide

## 🚀 Start the Application (3 Steps)

### 1️⃣ Start Backend (Terminal 1)
```bash
cd backend
uvicorn app.main:app --reload
```
✅ Backend runs at: http://localhost:8000  
✅ API docs at: http://localhost:8000/docs

### 2️⃣ Start Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```
✅ Frontend runs at: http://localhost:3000

### 3️⃣ Open Browser
Navigate to: http://localhost:3000

---

## 📱 Pages Available

| Page | URL | Status |
|------|-----|--------|
| Overview | http://localhost:3000 | ✅ Real API |
| Model Lab | http://localhost:3000/models | ✅ Real API |
| Data Health | http://localhost:3000/data-health | ✅ Real API |
| Forecasting | http://localhost:3000/forecasting | ⏳ Demo only |
| Anomalies | http://localhost:3000/anomalies | ⏳ Demo only |

---

## 🧪 Run Tests

### ML Pipeline Tests
```bash
python -m pytest tests/ -v
```
Expected: **109 tests passing**

### Backend API Tests
```bash
cd backend
python -m pytest tests/ -v
```
Expected: **14 tests passing**

### Frontend Build & Lint
```bash
cd frontend
npm run build
npm run lint
```
Expected: **0 errors, 0 warnings**

---

## 🔍 Verify Integration

### Check Backend Health
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"ok"}`

### Check Real Data
```bash
curl http://localhost:8000/api/v1/model-metrics
```
Expected: JSON with `"isDemo": false` and `"bestModel": "Histogram Gradient Boosting"`

### Check Frontend
1. Open http://localhost:3000/models
2. Look for **no yellow demo banner** (means backend is connected)
3. Verify "Best Model: Histogram Gradient Boosting"
4. Verify "MAE: 0.321 kW" (real result)

---

## 📊 What You'll See

### Model Lab Page
- **Best Model:** Histogram Gradient Boosting
- **MAE:** 0.3210 kW (real test result)
- **RMSE:** 0.4641 kW
- **Performance Chart:** All 4 models compared
- **Feature Importance:** Top predictive features

### Data Health Page
- **Total Samples:** 31,631 hourly records
- **Coverage:** 92.6%
- **Date Range:** Dec 2006 - Nov 2010
- **Validation Status:** PASSED
- **Hourly Distribution Chart**

### Overview Dashboard
- **Current Power:** Latest test value
- **Daily Average:** Last 24h mean
- **Weekly Trend:** Comparison chart
- **Anomalies:** Count from test set
- **Recent Consumption:** 7-day chart

---

## ⚠️ Troubleshooting

### Backend won't start
**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Fix:**
```bash
cd backend
pip install -r requirements.txt
```

### Frontend shows demo data
**Check:**
1. Is backend running? (http://localhost:8000/health)
2. Check browser console for errors (F12)
3. Verify `.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000`

**Fix:**
```bash
# Restart backend
cd backend
uvicorn app.main:app --reload
```

### Port already in use
**Error:** `Address already in use`

**Fix:**
```bash
# Windows: Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port
uvicorn app.main:app --reload --port 8001
```

---

## 🎯 Quick Verification (30 seconds)

Run this to verify everything works:

```bash
# 1. ML tests
python -m pytest tests/ -v
# Expected: 109 passed ✅

# 2. Backend tests  
cd backend && python -m pytest tests/ -v && cd ..
# Expected: 14 passed ✅

# 3. Frontend build
cd frontend && npm run build && npm run lint && cd ..
# Expected: Successful build, 0 errors ✅
```

If all three pass: **✅ System is ready!**

---

## 📚 More Information

- **Full Integration Guide:** `docs/INTEGRATION_GUIDE.md`
- **Backend API Docs:** `backend/README.md`
- **Frontend Implementation:** `FRONTEND_IMPLEMENTATION.md`
- **Real Experiment Results:** `REAL_DATA_RESULTS.md`
- **Current Status:** `STATUS.md`

---

## 💡 Pro Tips

1. **Keep terminals open** - Both backend and frontend need to run simultaneously
2. **Check browser console** - Press F12 to see API requests and responses
3. **Use API docs** - Visit http://localhost:8000/docs for interactive API testing
4. **Demo mode is OK** - If backend is stopped, frontend still works with demo data

---

**Ready to start?** Open 2 terminals, run the commands above, and visit http://localhost:3000 🚀
