# GridPulse dashboard

Next.js dashboard for GridPulse's historical household power experiment. The production views call the FastAPI service; this project does not display live campus or meter readings.

## Run locally

Start the backend at `http://localhost:8000` after following [backend setup](../backend/README.md), then:

```bash
npm ci
cp .env.example .env.local
npm run dev
```

Set `NEXT_PUBLIC_API_URL` to the API origin if it differs from `http://localhost:8000`. Synthetic screens are available only by adding `?demo=1` and are labeled as demo data.

Quality checks: `npm run lint`, `npx tsc --noEmit`, and `npm run build`. See [deployment notes](../docs/DEPLOYMENT.md).
