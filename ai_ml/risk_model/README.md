# SlideAlert Risk Scoring Engine

This package implements the SlideAlert landslide hazard risk-scoring engine, combining spatial machine learning segmentations with temporal meteorological rainfall telemetry.

---

## Why XGBoost is not being trained yet

Supervised training of tabular classifiers (such as XGBoost) to map rainfall history to zone landslide risk requires timestamped historical events (dates when landslides occurred paired with antecedent rainfall records). The Landslide4Sense dataset is purely spatial and contains no temporal/weather attributes. 

Creating a synthetic dataset of fake rainfall and event dates would compromise scientific integrity. Consequently, this engine implements a transparent, domain-informed heuristic risk formula. This will serve as a robust prototype until historical landslide occurrence dates are acquired to train a supervised model.

---

## Input Parameters

The risk engine accepts:
1. **Landslide Probability**: Maximum spatial confidence output from U-Net (`0.0` to `1.0`).
2. **Landslide Area Percentage**: Proportion of landslide pixels detected over the spatial patch (`0.0` to `100.0%`).
3. **Rainfall Series**: 14-day chronological sequence of daily precipitation sums in mm (either a list of floats or list of dicts).

---

## Risk Scoring Formula

The final risk score ($S_{risk}$) ranges from `0` to `100` and is calculated as:
$$S_{risk} = W_{ml} \cdot S_{ml} + W_{rain} \cdot S_{rain}$$
Where:
- **ML Weight ($W_{ml}$)**: `0.50` (50%)
- **Rainfall Weight ($W_{rain}$)**: `0.50` (50%)

### 1. ML Score ($S_{ml}$, Max 50 points)
$$S_{ml} = S_{prob} + S_{area}$$
- **Probability Sub-score ($S_{prob}$, Max 25 points)**:
  $$S_{prob} = P_{max} \times 25.0$$
- **Area Sub-score ($S_{area}$, Max 25 points)**: Capped at 15.0% landslide area to reach maximum points:
  $$S_{area} = \min\left(\frac{A_{pct}}{15.0}, 1.0\right) \times 25.0$$

### 2. Rainfall Score ($S_{rain}$, Max 50 points)
Aggregates precipitation metrics across multiple window intervals:
- **24-hour Intensity (Max 15 points)**: Capped at 80.0 mm.
  $$S_{24h} = \min\left(\frac{R_{24h}}{80.0}, 1.0\right) \times 15.0$$
- **3-day Cumulative (Max 15 points)**: Capped at 150.0 mm (measures immediate storm accumulation).
  $$S_{3d} = \min\left(\frac{R_{3d}}{150.0}, 1.0\right) \times 15.0$$
- **7-day Cumulative (Max 10 points)**: Capped at 250.0 mm.
  $$S_{7d} = \min\left(\frac{R_{7d}}{250.0}, 1.0\right) \times 10.0$$
- **14-day Cumulative (Max 10 points)**: Capped at 350.0 mm (measures long-term antecedent soil saturation).
  $$S_{14d} = \min\left(\frac{R_{14d}}{350.0}, 1.0\right) \times 10.0$$

---

## Categorical Risk Levels

The 0–100 score is mapped directly to one of the four categories expected by the React frontend:

- **0–24**: `"low"`
- **25–49**: `"moderate"`
- **50–74**: `"high"`
- **75–100**: `"critical"`

---

## Risk Factor Generation

Human-readable warnings are triggered when individual metrics exceed predefined thresholds:
- **`max_probability >= 0.70`**: `"High landslide probability"`
- **`area_percent >= 5.0%`**: `"Large predicted landslide area"`
- **`rainfall_24h >= 64.5 mm`**: `"Heavy 24-hour rainfall"` (IMD threshold)
- **`rainfall_3d >= 100.0 mm`**: `"High 3-day cumulative rainfall"`
- **`rainfall_7d >= 150.0 mm`**: `"High 7-day cumulative rainfall"`
- **`rainfall_14d >= 250.0 mm`**: `"High antecedent 14-day rainfall"`
- If no warnings are active: `"Stable terrain indices and low precipitation"`

---

## Confidence Interpretation

Confidence is defined as the distance of U-Net predictions from the ambiguous `0.5` decision boundary:
$$\text{Confidence} = 0.5 + |P_{max} - 0.5| \times 0.8$$
This represents the model's certainty regarding the spatial classifications.

---

## Scientific Limitation Statement

> [!IMPORTANT]
> **Scientific Rule**: Current risk scoring is a transparent prototype and is not a statistically calibrated probability of landslide occurrence. It is a heuristic hazard index indicating susceptibility under combined topographic indicators and rainfall triggers.
