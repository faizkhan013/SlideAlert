# SlideAlert AI/ML Project Module

This module provides the independent machine learning implementation for the **SlideAlert** landslide early warning system. It is structured to handle data preprocessing, landslide segmentation modeling, feature extraction, and risk assessment workflows.

---

## Project Structure

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
│   ├── train.py            # Training execution logic (structure only)
│   ├── evaluate.py         # Segmentation metrics (F1, IoU, Accuracy)
│   └── predict.py          # Single image inference and area calculations
│
├── features/               # Tabular feature aggregators
│   ├── rainfall.py         # Antecedent rainfall metrics from Open-Meteo
│   ├── terrain.py          # Slope and elevation summary statistics
│   └── spectral.py         # Remote sensing indices (NDVI, NDWI)
│
├── risk_model/             # Tabular hazard risk classifiers (stubs)
│   ├── dataset.py
│   ├── train.py
│   ├── evaluate.py
│   └── predict.py
│
├── explainability/         # Model transparency engines (stubs)
│   └── shap_explainer.py
│
├── inference/              # Core interfaces serving Django endpoints
│   └── predictor.py        # Django-facing prediction handler
│
├── models/                 # Model checkpoints (ignored by Git)
├── tests/                  # Package tests
├── requirements.txt        # Initial dependencies configuration
└── README.md               # Project documentation
```

---

## Dataset Information

- **Primary Source**: Landslide4Sense (2022) competition dataset.
- **Input Channels**: 14 channels (12 Sentinel-2 multispectral bands + 1 ALOS PALSAR Slope band + 1 ALOS PALSAR DEM band).
- **Target Dimensions**: Height $\times$ Width $\times$ Channels = `128 x 128 x 14`.
- **Target Mask**: Binary pixel-level segmentation mask (`128 x 128`).
  - `0`: Non-landslide
  - `1`: Landslide

---

## Segmentation Model: U-Net
The deep learning module uses a standard PyTorch 2D U-Net to perform semantic segmentation. It maps the 14 input channels to a single channel of logits (`1 x 128 x 128`). Sigmoid probabilities are then extracted to create the binary mask and evaluate the landslide area coverage percentage.

---

## Architectural Decision: Two-Stage Risk Pipeline

To ensure scientific integrity, the model is split into two logical stages:

1. **Stage 1 (Spatial Segmentation)**: Train the U-Net on Landslide4Sense images to predict the *active landslide area percentage* for a given zone coordinate.
2. **Stage 2 (Temporal Risk Classification)**: Predict a final hazard risk category (`low`, `moderate`, `high`, `critical`) by combining the U-Net landslide area output, terrain constants, and antecedent rainfall metrics derived from the Open-Meteo API.

*Note: Supervised training of the Stage 2 XGBoost classifier requires historical zone landslide dates. Until temporal event logs are obtained, risk evaluation runs on established geological threshold heuristics.*
