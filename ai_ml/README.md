# SlideAlert AI/ML Project Module

This module provides the independent machine learning implementation for the **SlideAlert** landslide early warning system. It handles data preprocessing, landslide segmentation modeling, feature extraction, and risk assessment workflows.

---

## 1. Project Structure

```text
ai_ml/
├── preprocessing/          # Data validation and normalization modules
│   ├── normalization.py    # Channel standardization using baseline averages
│   └── validation.py       # Input data shape/anomaly verification utilities
│
├── segmentation/           # Deep learning landslide detection models
│   ├── dataset.py          # PyTorch HDF5 data loader
│   ├── model.py            # U-Net architecture
│   ├── losses.py           # Dice Loss and Combined Dice+BCE Loss formulas
│   ├── train.py            # Training execution logic
│   ├── evaluate.py         # Segmentation metrics computation
│   └── predict.py          # Single image inference and area calculations
│
├── features/               # Tabular feature aggregators
│   ├── rainfall.py         # Antecedent rainfall metrics from Open-Meteo
│   ├── terrain.py          # Slope and elevation summary statistics
│   └── spectral.py         # Remote sensing indices (NDVI, NDWI)
│
├── risk_model/             # Tabular hazard risk classifiers
│   ├── risk_engine.py      # Rule-based diagnostic hazard scoring
│   ├── test_risk_engine.py # Unit tests for the risk engine
│   └── dataset.py, train.py, evaluate.py, predict.py
│
├── explainability/         # Model transparency engines (stubs)
│   └── shap_explainer.py
│
├── inference/              # Core interfaces serving Django endpoints
│   ├── predictor.py        # Single image U-Net prediction handler
│   └── slidealert_predictor.py # Unified spatial U-Net + temporal rainfall adapter
│
├── models/                 # Model checkpoints and evaluation artifacts
│   ├── baseline_unet_best.pth  # Trained model weights (65.95 MB)
│   ├── val_split.txt           # Validation filenames split list (760 files)
│   ├── train_split.txt         # Training filenames split list (3,039 files)
│   └── evaluation/             # Model evaluation CSVs and prediction plots
│       ├── final_metrics.csv   # Accuracy, F1, precision, recall, IoU at 0.50
│       ├── confusion_matrix.csv# Pixel-level TP, TN, FP, FN counts at 0.50
│       ├── threshold_comparison.csv # Performance comparison across thresholds
│       └── examples/           # 10 qualitative predicted overlay PNG images
```

---

## 2. Dataset Information

*   **Primary Source**: Landslide4Sense (2022) competition dataset.
*   **Path**: `D:\slideland\dataset\Landslide4Sense`
*   **Expected Structure**:
    *   `TrainData/img/` - 14-channel input image files (e.g. `image_1.h5` ... `image_3799.h5`)
    *   `TrainData/mask/` - 1-channel target segmentation mask files (e.g. `mask_1.h5` ... `mask_3799.h5`)
    *   `ValidData/img/` - 14-channel validation image files (without target masks)
*   **Input Dimensions**: Height $\times$ Width $\times$ Channels = `128 x 128 x 14`
*   **Target Mask**: Binary pixel-level segmentation mask (`128 x 128`)
    *   `0`: Non-landslide
    *   `1`: Landslide

---

## 3. Python Environment & Setup

1.  **Virtual Environment**: A virtual environment is pre-configured at `D:\slideland\.venv`.
2.  **Activation**:
    *   **PowerShell**: `.\.venv\Scripts\Activate.ps1`
    *   **CMD**: `.\.venv\Scripts\activate.bat`
3.  **Required Packages**: Dependencies are configured in `D:\slideland\ai_ml\requirements.txt`. Key packages include:
    *   `torch`, `numpy`, `h5py`, `matplotlib`

---

## 4. How to Run Training, Inference, and Evaluation

### Run Training
To execute the training script from the project root:
```bash
python ai_ml/segmentation/train.py
```
This splits the training data 80/20 (saved to `models/train_split.txt` and `models/val_split.txt`) and saves the model checkpoint to `models/baseline_unet_best.pth`.

### Run Model Evaluation
To evaluate the checkpoint and compute metrics across multiple thresholds:
```bash
python ai_ml/models/evaluation/run_evaluation.py
```
This saves `final_metrics.csv`, `confusion_matrix.csv`, `threshold_comparison.csv`, and qualitative plots inside `models/evaluation/`.

### Run Standalone Inference
```python
from ai_ml.inference.predictor import SlideAlertPredictor

# Initialize predictor (loads baseline checkpoint by default)
predictor = SlideAlertPredictor()

# Predict on an image path
results = predictor.predict_image("D:/slideland/dataset/Landslide4Sense/TrainData/img/image_241.h5", threshold=0.5)
print("Landslide Area %:", results["landslide_area_percent"])
```

---

## 5. Integration Flow with Django Backend

```text
[Django ZoneSerializer]
       │
       ▼ (invokes)
[ai_ml.inference.slidealert_predictor.get_ml_prediction]
       │
       ├─► [SlideAlertPredictor.predict_image] (loads HDF5 -> standardizes bands -> U-Net -> binary mask)
       │
       ├─► [Open-Meteo API / Cached readings] (obtains 14-day rainfall time-series)
       │
       ▼ (passes variables to)
[LandslideRiskEngine.compute_risk]
       │
       ├─► evaluates combined risk score: ML Area (50%) + Weather Telemetry (50%)
       │
       ▼ (returns payload)
{
    "ml_enabled": true,
    "ml_prediction": {
        "landslide_probability": 0.9999,
        "landslide_area_percent": 19.42,
        "confidence": 0.9,
        "risk_score": 69,
        "risk_factors": ["High landslide probability", ...],
        "ml_risk_level": "high",
        "predicted_at": "..."
    }
}
```

---

## 6. Important Limitations

1.  **Spatial Segmentation vs Forecasting**: The U-Net model performs **spatial image segmentation** (locating existing landslide areas in satellite imagery). It does **not** predict future landslide occurrences.
2.  **Rainfall Risk Calibration**: To compute active hazards, the `LandslideRiskEngine` combines the spatial vulnerability index from the U-Net with dynamic precipitation forecasts.
3.  **Heuristic Classification**: Stage 2 utilizes heuristic risk rules derived from geological indices because historical time-aligned landslide event records are unavailable.
4.  **Demo Mode**: In production, `SLIDEALERT_DEMO_MODE` is enabled, mapping specific stations to representative HDF5 files on disk for demonstration purposes. Other stations safely report `ml_enabled: false`.
