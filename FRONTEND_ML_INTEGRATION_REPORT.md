# SlideAlert Frontend ML Integration Report

This report documents the integration of backend AI/ML landslide hazard prediction payloads into the **Terrain Watch** React frontend.

---

## 1. Modifications

### Files Modified
- [`frontend/src/config.js`](file:///D:/slideland/frontend/src/config.js): Added `getEffectiveRisk` helper to dynamically resolve the active risk string (ML risk level if available, otherwise standard risk). Added `"critical"` category mappings to `riskClass` and `RISK_SEVERITY` severity rankings.
- [`frontend/src/App.jsx`](file:///D:/slideland/frontend/src/App.jsx): Updated `deriveStats` and `deriveAlerts` to apply the `getEffectiveRisk` logic and mapped `"critical"` and `"severe"` values to high-severity counts.
- [`frontend/src/components/MapPane.jsx`](file:///D:/slideland/frontend/src/components/MapPane.jsx): Updated marker circle colors to resolve based on `getEffectiveRisk`.
- [`frontend/src/components/Sidebar.jsx`](file:///D:/slideland/frontend/src/components/Sidebar.jsx): Updated list dot indicators to resolve based on `getEffectiveRisk`.
- [`frontend/src/components/SensorGrid.jsx`](file:///D:/slideland/frontend/src/components/SensorGrid.jsx): Updated card badges to resolve based on `getEffectiveRisk`.
- [`frontend/src/components/ZoneDetailPanel.jsx`](file:///D:/slideland/frontend/src/components/ZoneDetailPanel.jsx): Added a dedicated AI/ML Prediction layout section to display U-Net outputs, risk scores, confidence levels, and list factor warnings, or a neutral unavailable message.

---

## 2. API Fields Consumed
Under `selected` zone objects:
- `ml_enabled`: Boolean flag determining model presence.
- `ml_prediction`: Nested dictionary containing:
  - `landslide_probability`: Float mapped to probability percent (`Math.round(val * 100)%`).
  - `landslide_area_percent`: Float mapped to area percent (`Math.round(val)%`).
  - `confidence`: Float mapped to confidence percent (`Math.round(val * 100)%`).
  - `risk_score`: Heuristic score index (printed as `/ 100`).
  - `ml_risk_level`: String resolving color badges (`"low"`, `"moderate"`, `"high"`, `"critical"`).
  - `risk_factors`: Array of human-readable warnings.

---

## 3. UI and Risk Integration Details

### Map & List Components
Map markers, sidebar stations, sensor cards, and detail panels query `getEffectiveRisk(zone)`. If a zone is ML-enabled and contains prediction logs, the color code, text level, and alert classification resolve using `ml_prediction.ml_risk_level`. If ML is disabled, it transparently falls back to the original `risk` field.

### Alerts and Ticker
Alert filters and sorts in `App.jsx` are derived using `getEffectiveRisk(zone)`. Zones evaluated as `"critical"` or `"high"` trigger active alert cards and scroll across the top news-ticker automatically.

---

## 4. Null Safety & Fallbacks
- **ML Disabled**: If `ml_enabled === false` or `ml_prediction === null`, the detail panel displays: *"AI/ML prediction unavailable for this zone."*
- **Baseline Rainfall**: Daily precipitation (`rainfall_24h_mm`) and 14-day history graphs (`series`) remain displayed in parallel. No baseline fields are removed or replaced.
- **Error Robustness**: Missing fields or null items default cleanly without throwing errors or causing console-breaking crashes.

---

## 5. Build Verification Results
The frontend was successfully compiled:
```bash
npm run build
```
Vite production build completed with **zero errors and warnings**:
- Transformed 89 modules.
- Compiled `dist/assets/index-CTl8u50r.js` and `dist/assets/index-Cu1ppMMg.css` successfully.

---

## 6. Scientific Limitations
- **Topographic Segmenter**: U-Net displays spatial segmentations mapping surface indices. It does not represent temporal forecasts.
- **Scoring System**: Combined hazard index values represent prototype decision bounds, not statistically calibrated physical likelihoods.
