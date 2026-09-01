# SlideAlert — NER Landslide Early Warning (SIH26001)

React + Vite frontend wired directly to the Django backend's zone API.
No mock data — the app makes a single boot call to `GET /api/zones/` and
every panel (map, alerts, stat cards, sensor grid, sparkline) derives from
that response.

## Run it

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # production build to dist/
```

## Point it at your backend

Edit `src/config.js`:

```js
export const API_BASE = "https://YOUR-BACKEND-HOST/api";
```

## API endpoints used

| Endpoint | Purpose | Called by |
|---|---|---|
| `GET /api/zones/` | All zones — live rainfall, computed risk, 14-day series | `useZones()` on boot, polled every 5 min. Feeds the map, stat cards, sensor grid, sparkline, and derived alerts — this is the only call the app makes on load. |
| `POST /api/zones/:id/refresh/` | Force a live re-fetch from Open-Meteo, bypassing the 30-min cache | "Force refresh" button in `ZoneDetailPanel.jsx` |
| `GET /api/zones/:id/` | Single zone, same shape | Exposed as `fetchZoneDetail()` in `hooks/useApi.js`, not called yet — use it if you build a per-zone detail route |
| `GET /api/alerts/` | Server-filtered/sorted version of the alert list | Exposed as `fetchServerAlerts()`, not called by default — the app currently derives alerts client-side from `/zones/` (`deriveAlerts()` in `App.jsx`). Swap it in if you'd rather the backend own that logic. |
| `GET /api/stats/` | Pre-computed summary counts | Exposed as `fetchServerStats()`, not called by default — the app currently derives stats client-side from `/zones/` (`deriveStats()` in `App.jsx`). Swap it in the same way. |
| `/admin/` | Django admin | Not called from the frontend — for managing `Zone` rows / inspecting cached `RainfallReading`s by hand. |

### Zone shape expected

```json
{
  "id": 1,
  "name": "Sohra (Cherrapunji)",
  "state": "Meghalaya",
  "latitude": 25.285,
  "longitude": 91.7362,
  "rainfall_24h_mm": 42.6,
  "risk": "moderate",
  "last_updated": "2026-08-28T14:02:11+05:30",
  "series": [{ "date": "2026-08-15", "precipitation_mm": 8.1 }]
}
```

`risk` is treated as `"low" | "moderate" | "high"` (a `"severe"` value is also
handled, mapped to the same "high" styling) — see `riskClass()` in
`src/config.js` if your backend uses different labels.

## Project structure

```
src/
  config.js                API_BASE, riskClass(), RISK_SEVERITY
  App.jsx                  boot() call + client-side deriveStats/deriveAlerts
  main.jsx
  styles.css                design tokens (topographic/survey theme)
  hooks/useApi.js            useZones, useZoneRefresh, fetchZoneDetail,
                              fetchServerAlerts, fetchServerStats
  components/
    Sidebar.jsx             zone list + backend connection light
    MapPane.jsx             Leaflet map (react-leaflet), risk-colored markers
    StatCards.jsx           total / high / moderate / low counts + last sync
    SensorGrid.jsx          card-per-zone grid (name, state, rainfall, risk)
    ZoneDetailPanel.jsx     selected zone's risk + rainfall + refresh button
    SparklinePanel.jsx      14-day precipitation line chart from zone.series
    AlertsPanel.jsx         zones with risk != low, worst first
    Ticker.jsx              scrolling alert banner
    Clock.jsx               live IST clock
```

## Swapping to server-side stats/alerts

`deriveStats()` and `deriveAlerts()` in `App.jsx` currently compute
everything from the `/zones/` payload. To move that logic server-side:

```js
import { fetchServerStats, fetchServerAlerts } from "./hooks/useApi.js";
// replace the useMemo(deriveStats/deriveAlerts, ...) calls with your own
// fetch-on-zones-change effect that calls these instead.
```
