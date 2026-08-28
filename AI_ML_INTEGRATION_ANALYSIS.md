# SlideAlert AI/ML Integration Analysis Report

This document provides a comprehensive analysis of the existing **SlideAlert** application (SIH26001 project) and defines the architectural plan for integrating the AI/ML component without breaking the Django backend or React frontend.

---

## 1. Existing Repository Structure

The `SlideAlert` workspace is structured as follows:

```text
D:\slideland\
├── .git/                               # Git metadata
├── .gitignore                          # Git ignore settings
├── LICENSE                             # Project license
├── README.md                           # Main README
├── Landslide4Sense-2022-main/          # Untracked directory (retained)
├── Landslide4Sense-2022-main.zip      # Untracked zip file (retained)
├── backend/                            # Django Backend Project
│   ├── manage.py                       # Django CLI entrypoint
│   ├── db.sqlite3                      # SQLite Database
│   ├── requirements.txt                # Python dependencies
│   ├── prahari/                        # Configuration app
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── monitoring/                     # Main functional app
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── models.py
│       ├── serializers.py
│       ├── services.py
│       ├── urls.py
│       ├── views.py
│       ├── migrations/
│       └── management/
│           └── commands/
│               └── seed_zones.py       # Seed data script
└── frontend/                           # React Frontend Project
    ├── package.json                    # Node dependencies
    ├── vite.config.js                  # Vite configuration
    ├── index.html                      # Entry HTML
    └── src/
        ├── main.jsx                    # Entry React mount point
        ├── App.jsx                     # Dashboard App layout & state
        ├── config.js                   # API configuration & risk mapping
        ├── styles.css                  # UI styling
        ├── components/                 # UI dashboard widgets
        │   ├── AlertsPanel.jsx
        │   ├── Clock.jsx
        │   ├── MapPane.jsx
        │   ├── SensorGrid.jsx
        │   ├── Sidebar.jsx
        │   ├── SparklinePanel.jsx
        │   ├── StatCards.jsx
        │   ├── Ticker.jsx
        │   └── ZoneDetailPanel.jsx
        └── hooks/
            └── useApi.js               # Custom fetch hooks
```

---

## 2. Backend Architecture

- **Framework**: Django 5.0 + Django REST Framework (DRF) 3.15.
- **Database**: SQLite (`db.sqlite3`).
- **Config App**: `prahari` (hosts settings, routing).
- **Core App**: `monitoring` (handles zones, precipitation readings, and risk logic).
- **Cross-Origin Resource Sharing (CORS)**: Handled by `django-cors-headers`. Currently configured to allow all origins in development (`CORS_ALLOW_ALL_ORIGINS = True`).
- **Time Zone**: Configured to `Asia/Kolkata` (Indian Standard Time).

---

## 3. Frontend Architecture

- **Bundler/Runtime**: Vite + React.
- **Styling**: Vanilla CSS in `src/styles.css` with dark contour styling.
- **Map View**: Integrated via `react-leaflet` with OpenStreetMap tiles.
- **Visualizations**: Time-series line chart rendered via `react-chartjs-2`.
- **API Client**: Native browser `fetch` (no Axios).
- **Data Flow**: Single source of truth. `App.jsx` queries `/api/zones/` on boot and polls it every 5 minutes. Active alerts and summary statistics are derived **client-side** from this single endpoint's response payload.

---

## 4. Database Models

The schema consists of two related tables in `backend/monitoring/models.py`:

### `Zone`
Represents a geographical location under monitoring.
- `name` (`CharField`, max_length=120): The location's name.
- `state` (`CharField`, max_length=80): The state (e.g. Meghalaya, Sikkim).
- `latitude` (`FloatField`): GPS latitude coordinate.
- `longitude` (`FloatField`): GPS longitude coordinate.
- `created_at` (`DateTimeField`, auto_now_add=True): Timestamp of creation.
- *Meta*: Ordered by `['state', 'name']`; unique together constraint on `('name', 'state')`.

### `RainfallReading`
Acts as a cache for daily precipitation.
- `zone` (`ForeignKey` to `Zone`, related_name="readings"): Cascading relation back to the zone.
- `date` (`DateField`): The specific date of the reading.
- `precipitation_mm` (`FloatField`, null/blank): Total rainfall on this day.
- `fetched_at` (`DateTimeField`, auto_now=True): Timestamp recording when this entry was fetched from Open-Meteo.
- *Meta*: Ordered by `['date']`; unique together constraint on `('zone', 'date')`.

---

## 5. API Endpoints

The API router `backend/monitoring/urls.py` exposes 5 endpoints prefixed by `/api/`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/zones/` | Lists all monitored zones with cached weather data and risk evaluation. Triggers cache refresh if stale. |
| `GET` | `/api/zones/<id>/` | Gets details for a single zone. Triggers cache refresh if stale. |
| `POST` | `/api/zones/<id>/refresh/` | Forces an immediate Open-Meteo fetch for the zone, bypassing cache timers. |
| `GET` | `/api/alerts/` | Returns list of zones currently above the `low` risk tier, sorted by severity (`critical` -> `high` -> `moderate`). |
| `GET` | `/api/stats/` | Returns aggregated metrics of monitored zones, states covered, hazard counts, and average rainfall. |

---

## 6. Exact API Response Structures

### GET `/api/zones/` (and GET `/api/zones/<id>/`)
Returns a JSON array (or object) with the following structure:
```json
[
  {
    "id": 1,
    "name": "Mangan",
    "state": "Sikkim",
    "latitude": 27.5,
    "longitude": 88.53,
    "rainfall_24h_mm": 18.2,
    "risk": "moderate",
    "last_updated": "2026-08-28T08:23:45Z",
    "series": [
      {
        "date": "2026-08-14",
        "precipitation_mm": 5.4
      },
      {
        "date": "2026-08-15",
        "precipitation_mm": 12.1
      }
      // ... up to 15 entries (14 past days + current day)
    ]
  }
]
```

### GET `/api/stats/`
```json
{
  "zones_monitored": 5,
  "states_covered": 2,
  "high_critical_count": 1,
  "avg_rainfall_24h_mm": 45.2,
  "zones_reporting": 5
}
```

---

## 7. Open-Meteo Integration

- **Upstream Endpoint**: `https://api.open-meteo.com/v1/forecast`
- **Query Parameters**:
  - `latitude`: Float (Zone Coordinate)
  - `longitude`: Float (Zone Coordinate)
  - `daily`: `"precipitation_sum"`
  - `past_days`: `14` (via `DEFAULT_PAST_DAYS` in `services.py`)
  - `forecast_days`: `0`
  - `timezone`: `"auto"`

---

## 8. Current Rainfall Processing

When pulling weather data:
1. The backend parses `response.json()["daily"]["time"]` (dates list) and `response.json()["daily"]["precipitation_sum"]` (values list).
2. It zips these together and executes `RainfallReading.objects.update_or_create(...)` to cache them in SQLite.
3. The latest reading by date is resolved using `zone.readings.order_by("-date").first()`.
4. Its `precipitation_mm` represents the current `rainfall_24h_mm` for the zone.
5. Its `fetched_at` timestamp defines the `last_updated` value.

---

## 9. Current Risk Calculation

The system maps the 24h rainfall to a qualitative risk tier inside `backend/monitoring/services.py` based on the India Meteorological Department (IMD) intensity scale:
- `rainfall < 15.6 mm` -> `"low"`
- `15.6 <= rainfall < 64.5 mm` -> `"moderate"`
- `64.5 <= rainfall <= 115.5 mm` -> `"high"`
- `rainfall > 115.5 mm` -> `"critical"`
- `rainfall is None` -> `"unknown"`

This calculation only factors in rainfall-intensity and has no terrain, slope, soil, or ML model support.

---

## 10. Frontend Data Requirements

The frontend relies heavily on:
1. `zone.risk`: Must return `"low"`, `"moderate"`, `"high"`, `"critical"`, or `"unknown"` for proper marker color matching and badges.
2. `zone.rainfall_24h_mm`: Displayed as a decimal number.
3. `zone.series`: Must remain a list of `{"date": "...", "precipitation_mm": ...}` objects to plot the sparkline line graph.
4. `zone.latitude` & `zone.longitude`: Critical for placing Leaflet circle markers on the map interface.

---

## 11. AI/ML Integration Point

To incorporate AI/ML predictions seamlessly:
- **Database level**: We should define a new model `MLPrediction` in `backend/monitoring/models.py` referencing the `Zone` model via a `OneToOneField` (or `ForeignKey` to support historical runs). This avoids bloating the core `Zone` model and separates concerns.
- **Service level**: Implement a new service module (e.g. `backend/monitoring/ml_services.py` or a dedicated package) that takes historical rainfall series, latitude/longitude, and terrain constants to run inference and update the `MLPrediction` object.
- **Serializer level**: Modify `ZoneSerializer` to check for an associated `MLPrediction` and append the metrics to the zone JSON payload.

---

## 12. Recommended ML Output Fields

We recommend introducing the following standardized JSON fields to the API:

- `landslide_probability` (Float, range `0.0` to `1.0`): The raw probability of a landslide occurring.
- `landslide_area_percent` (Float, range `0.0` to `100.0`): Expected landslide extent percentage in the area.
- `confidence` (Float, range `0.0` to `1.0`): Model's confidence score in this prediction.
- `risk_score` (Integer, range `0` to `100`): Normalized score incorporating rainfall + ML model output.
- `risk_factors` (List of Strings): Key attributes triggering the risk tier (e.g. `["Steep slope", "Soil saturation", "Heavy rainfall"]`).
- `ml_risk_level` (String): The categorical risk calculated by ML (`"low"`, `"moderate"`, `"high"`, `"critical"`).

---

## 13. Recommended API Integration

The enhanced GET `/api/zones/` payload will merge the core rainfall telemetry with the new ML model outputs:

```json
{
  "id": 1,
  "name": "Mangan",
  "state": "Sikkim",
  "latitude": 27.5,
  "longitude": 88.53,
  "rainfall_24h_mm": 18.2,
  "risk": "high", // We can override this with the ML risk level to automatically color markers
  "last_updated": "2026-08-28T08:23:45Z",
  "series": [
    {"date": "2026-08-14", "precipitation_mm": 5.4}
    // ...
  ],
  "ml_enabled": true,
  "ml_prediction": {
    "landslide_probability": 0.87,
    "landslide_area_percent": 26.4,
    "confidence": 0.91,
    "risk_score": 87,
    "risk_factors": ["Heavy rainfall", "Steep slope (>35°)", "High soil saturation"],
    "ml_risk_level": "high",
    "predicted_at": "2026-08-28T13:50:00Z"
  }
}
```

---

## 14. Files that the AI/ML Developer Should NOT Modify

To prevent regression bugs and build breaks, the AI/ML developer **must NOT modify**:
- `frontend/src/*` (Any frontend React components, styling, or hooks).
- `backend/prahari/settings.py` (Core Django setting configuration).
- `backend/prahari/urls.py` (Project root routing rules).
- `backend/monitoring/admin.py` or `apps.py` (App configuration).

---

## 15. Any Compatibility Issues

- **Risk Category Strings**: The React frontend maps risks using strict case-insensitive equality checks. The returned risk string values MUST strictly be `low`, `moderate` (or `medium`), `high` (or `severe`), or `critical` (which maps to high/severe representation). If the model returns custom names like "extreme" or "yellow warning", the frontend code will fail to style them and show "unknown" badges.
- **Null Safety**: When a zone is new or has no data, `rainfall_24h_mm` or `ml_prediction` can be `null`. The serializers and views must ensure fields return correct defaults instead of throwing serialization errors.
- **CORS Config**: When running the frontend and backend locally (e.g. Vite on `:5173` and Django on `:8000`), CORS headers must remain active.

---

## 16. Recommendations for the AI/ML Module

1. **Inference Pipeline**: Create a separate Python directory `backend/ai_ml/` inside the Django root to house the ML models, weights, preprocess scripts, and pipeline logic.
2. **Offline Training, Online Inference**: Run training offline. Package trained weights (e.g. `.onnx`, `.pt`, `.joblib`) within the repository or fetch them from a secure cloud bucket. The Django backend should only run inference.
3. **Execution Hooks**: Trigger the ML prediction pipeline inside `fetch_and_cache_zone` right after the fresh weather telemetry is fetched from Open-Meteo. This guarantees that model predictions are always run against the latest rainfall readings.
