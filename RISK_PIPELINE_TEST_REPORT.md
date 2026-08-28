# SlideAlert Risk Pipeline End-to-End Test Report

This report documents the local end-to-end integration test of the **SlideAlert** prediction pipeline, chaining the trained U-Net segmenter, antecedent rainfall feature extractor, and heuristic risk engine.

---

## 1. Test Setup
- **Trained Model Checkpoint**: `D:\slideland\ai_ml\models\baseline_unet_best.pth` (CPU mode)
- **Input Satellite Image**: Labeled holdout file `image_241.h5` (known to contain active landslide pixels)
- **Input Weather telemetry**: 14-day rainfall series simulating a severe monsoon event:
  - Daily rainfall in mm: `[1.2, 0.0, 4.5, 12.1, 8.4, 0.0, 3.1, 15.6, 22.4, 45.1, 12.0, 58.2, 33.1, 75.4]`
  - Last day rainfall: `75.4 mm` (exceeds the 64.5mm IMD heavy rain warning trigger)
  - 3-day cumulative rainfall: `166.7 mm`
  - 7-day cumulative rainfall: `258.2 mm`
  - 14-day cumulative rainfall: `301.1 mm`

---

## 2. Execution Results

The integration adapter class `SlideAlertMLAdapter` was invoked. The raw JSON payload returned is presented below:

```json
{
    "ml_enabled": true,
    "ml_prediction": {
        "landslide_probability": 0.9999,
        "landslide_area_percent": 19.42,
        "confidence": 0.9,
        "risk_score": 97,
        "risk_factors": [
            "High landslide probability",
            "Large predicted landslide area",
            "Heavy 24-hour rainfall",
            "High 3-day cumulative rainfall",
            "High 7-day cumulative rainfall",
            "High antecedent 14-day rainfall"
        ],
        "ml_risk_level": "critical",
        "predicted_at": "2026-08-28T16:09:19.785218Z"
    }
}
```

---

## 3. Heuristic Score Analysis
The final score of **`97`** falls into the **`critical`** hazard tier and is derived as follows:

1. **ML Segmentation Score (Max 50 points)**:
   - Max U-Net probability = `0.9999` $\rightarrow$ $0.9999 \times 25.0 = 24.99$ points.
   - Landslide area % = `19.42%` $\rightarrow$ exceeds the 15.0% cap $\rightarrow 25.0$ points.
   - Total ML score = $24.99 + 25.00 = 49.99$ points.
2. **Rainfall Score (Max 50 points)**:
   - 24-hour rainfall = `75.4 mm` $\rightarrow (75.4 / 80.0) \times 15 = 14.13$ points.
   - 3-day rainfall = `166.7 mm` $\rightarrow$ exceeds 150mm cap $\rightarrow 15.0$ points.
   - 7-day rainfall = `258.2 mm` $\rightarrow$ exceeds 250mm cap $\rightarrow 10.0$ points.
   - 14-day rainfall = `301.1 mm` $\rightarrow (301.1 / 350.0) \times 10 = 8.60$ points.
   - Total Rainfall score = $14.13 + 15.00 + 10.00 + 8.60 = 47.73$ points.
3. **Total Sum**:
   - Raw score = $49.99 + 47.73 = 97.72$ points.
   - Rounded and constrained score = **`97`** (maps to `"critical"`).

---

## 4. Warnings and Confidence Checks
- **Risk Level**: Checked against React frontend expectations. `"critical"` is a valid class category.
- **Risk Factors**: All 6 risk warnings are triggered logically based on inputs.
- **NaN / Infinite values**: `0` found in the evaluated fields.

---

## Status

RISK PIPELINE READY FOR BACKEND INTEGRATION
