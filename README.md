# SlideAlert: Landslide Early Warning System

SlideAlert is an integrated, full-stack geospatial landslide hazard screening and early warning dashboard designed for unstable mountain terrains. The system combines deep-learning-based spatial landslide detection with real-time meteorological forecast features to evaluate localized landslide hazards and map nearby road network risks.

---

## 1. Project Overview
SlideAlert operates as a multi-stage hazard monitoring platform. It uses satellite multi-spectral data and topographic elevation indicators to map historic landslide footprints and evaluate zone susceptibility. This spatial vulnerability is combined dynamically with real-time precipitation forecasts from meteorological APIs to compile a live hazard risk rating (`low`, `moderate`, `high`, `critical`) and display affected road segments on an interactive GIS map.

---

## 2. Key Features
*   **Deep Learning Segmentation**: Leverages a 2D U-Net model mapping 14-channel satellite imagery to locate landslide boundaries.
*   **Dynamic Risk Evaluation**: Fuses spatial landslide masks (50%) with dynamic 14-day cumulative rainfall readings (50%).
*   **GIS Road-Risk Screening**: Intersects localized road networks within a 5 km buffer around monitored zones to highlight hazard routes.
*   **Interactive Dashboard**: Provides real-time stats, 14-day rainfall sparklines, scrolling warning tickers, and Leaflet map panels.
*   **Fail-safe Caching**: Protects APIs against network latency via Django memory caches with automatic fallback configurations.

---

## 3. System Architecture
The application is decoupled into three core project directories:

```text
               ┌──────────────────────────────────────────────────┐
               │              OpenStreetMap / Overpass            │
               │            (Road Geometries 5km Buffer)          │
               └────────────────────────┬─────────────────────────┘
                                        │
                                        ▼ (GeoJSON)
┌──────────────────────┐       ┌─────────────────┐       ┌──────────────────────┐
│    Open-Meteo API    │       │                 │       │   React Dashboard    │
│ (Rainfall Forecast)  ├──────►│  Django Backend ├──────►│      (Leaflet)       │
└──────────────────────┘       │  (REST API /    │       │                      │
                               │   SQLite Cache) │       └──────────────────────┘
┌──────────────────────┐       │                 │
│  Landslide4Sense H5  ├──────►│                 │
│  (14-Band Imagery)   │       └────────┬────────┘
└──────────────────────┘                │
                                        ▼ (Inference Logits)
                               ┌─────────────────┐
                               │  U-Net Model    │
                               │  (PyTorch CPU)  │
                               └─────────────────┘
```

---

## 4. AI/ML Pipeline
1.  **Standardization**: Raw HDF5 files are standardized per-band using pre-calculated dataset baseline mean and standard deviations.
2.  **U-Net Inference**: Passes 14-channel input to obtain sigmoid probabilities mapping to spatial landslide layouts.
3.  **Area Aggregation**: Summarizes the proportion of pixels above the classification threshold ($0.50$) to compute landslide area percentage.
4.  **Weather Fusion**: Integrates spatial area results with 24h, 3d, 7d, and 14d rainfall metrics extracted from Open-Meteo readings.
5.  **Heuristic Classification**: Computes a diagnostic 0–100 risk score and categorizes it into a discrete risk rating.

---

## 5. U-Net Segmentation Models

### Production Candidate — Experiment 2 (Default)
*   **Architecture**: 2D U-Net with 14 input channels (12 Sentinel-2 multispectral bands + 1 ALOS PALSAR Slope band + 1 ALOS PALSAR DEM band) and 1 output channel.
*   **Weight Checkpoint**: `ai_ml/models/experiments/improved_unet/improved_unet_v2_best.pth`
*   **Loss Function**: Combined **Focal Loss + Dice Loss** ($\alpha=0.25, \gamma=2.0$, weight=0.5 / 0.5)
*   **Training**: 2 Epochs with Adam optimizer ($lr=1\times 10^{-3}$, weight decay $=5\times 10^{-4}$).
*   **Performance (760 Holdout Validation Samples at 0.50 Threshold)**:
    *   **Accuracy**: `98.62%`
    *   **Precision**: `66.92%` (nearly doubled vs baseline `35.60%`)
    *   **Recall**: `73.28%` (maintains high landslide capture)
    *   **F1 / Dice**: `69.95%` (+20.62% absolute over baseline `49.33%`)
    *   **IoU**: `53.79%` (+21.05% absolute over baseline `32.74%`)
    *   **False Positives**: `99,066` (**75.06% reduction** from baseline `397,285`)

### Production Baseline (Permanent Fallback)
*   **Weight Checkpoint**: `ai_ml/models/baseline_unet_best.pth` (tracked via Git LFS).
*   **Loss Function**: Combined BCE Loss (0.50) + Dice Loss (0.50), 1 Epoch (F1 `49.33%`, IoU `32.74%`).
*   **Dynamic Fallback / Selection**: Set `SLIDEALERT_MODEL_PATH` to override model checkpoint. Unset defaults to Experiment 2 with automatic baseline fallback if candidate weights are absent.

> [!NOTE]
> Pixel-level segmentation metrics measure spatial boundary accuracy on benchmark imagery and are **not future landslide prediction accuracy**. Future risk assessment is computed by combining spatial segmentation with real-time precipitation forecasts via the `LandslideRiskEngine`.

---

## 6. Landslide4Sense Dataset & Setup
The raw Landslide4Sense dataset is **intentionally NOT stored in this GitHub repository** because of its large size (~9.66 GB total raw size). Team members should clone the repository first, and then separately download and set up the dataset locally.

### A. Download Source
1. Download the Landslide4Sense dataset from the official Zenodo research record:
   [Download Landslide4Sense Dataset — Zenodo](https://zenodo.org/records/10463239)
2. The Zenodo record contains the following downloadable files:
   *   `TrainData.zip` (2.5 GB) — training images and landslide masks.
   *   `ValidData.zip` (143.4 MB) — validation images (no labels).
   *   `TestData.zip` (470.9 MB) — test images (no labels).
3. Refer to the official [iarai/Landslide4Sense-2022 GitHub Repository](https://github.com/iarai/Landslide4Sense-2022) for additional challenge background and documentation if needed.

### B. Expected Dataset Folder Structure
After downloading and extracting, place the dataset locally in your workspace at `D:\slideland\dataset\Landslide4Sense\`. The deep learning scripts, evaluation suite, and Django backend adapter expect EXACTLY the following structure:

```text
dataset/
└── Landslide4Sense/
    ├── TrainData/
    │   ├── img/     # image_1.h5 ... image_3799.h5 (14-channel satellite patches)
    │   └── mask/    # mask_1.h5 ... mask_3799.h5 (1-channel binary ground truths)
    ├── ValidData/
    │   └── img/     # image_1.h5 ... image_245.h5 (no ground truth masks available)
    └── TestData/
        └── img/     # image_1.h5 ... image_800.h5 (no ground truth masks available)
```

> [!IMPORTANT]
> **Git Ignore Enforcement**:
> The following paths, files, and extensions must remain outside the repository commits:
> *   `dataset/` (the entire folder is ignored at line 17 of `.gitignore`)
> *   `TrainData/`, `ValidData/`, `TestData/` (implicitly ignored)
> *   `*.h5`, `*.hdf5` (HDF5 satellite files)
> *   All downloaded dataset `.zip` archives (e.g. `TrainData.zip`)

### C. Operations and Dataset Requirements
Not all operations require the entire 10 GB dataset. Depending on what you are running, check the data requirements below:

| Operation | Dataset Requirement | Description |
| :--- | :--- | :--- |
| **Running the full dashboard** | Minimal demo files | The dynamic dashboard fetches weather and roads from live APIs. However, for local developer testing, the U-Net inference adapter maps seeded zones to specific HDF5 files (e.g. `image_241.h5` for Sohra, `image_1851.h5` for Mangan). Therefore, the specific image files in `TrainData/img/` must exist locally to show ML predictions for those demo zones. |
| **Running standalone inference** | Target image patch | The predictor expects the absolute path to a specific `.h5` file (e.g., `image_241.h5`) to generate the output probability map. |
| **Running model evaluation** | Validation split set | The evaluation runner (`run_evaluation.py`) requires all 760 validation files listed in `val_split.txt` with their corresponding images and masks under `TrainData/` to compute confusion matrices and F1 scores. |
| **Model training/retraining** | Full dataset | Requires the entire `TrainData` directory containing 3,799 images and masks. |

### D. Dataset Verification Checklist
Before running the project, verify your dataset layout:
- [ ] `dataset/` directory exists under `D:\slideland\`.
- [ ] `dataset/Landslide4Sense/TrainData/` exists.
- [ ] `dataset/Landslide4Sense/ValidData/` exists.
- [ ] Mapped demo files are present (e.g., `dataset/Landslide4Sense/TrainData/img/image_241.h5`).
- [ ] Run `git status` to verify that **no HDF5 files or dataset directories** are staged or untracked by Git.

#### Windows Verification Example
You can verify the dataset folder layout using standard Windows Command Prompt (CMD) or PowerShell:
```cmd
cd D:\slideland
dir dataset\Landslide4Sense
dir dataset\Landslide4Sense\TrainData\img\image_241.h5
```
It should report the directory listing showing `TrainData` and `ValidData`, and locate `image_241.h5` (1.75 MB).

### E. Team Workflow
1. **Clone the repository**: `git clone https://github.com/faizkhan013/SlideAlert.git`
2. **Install dependencies**: Set up python environment (`.venv`) and install via `pip install -r ai_ml/requirements.txt`. Install node packages (`npm install` under `frontend/`).
3. **Download dataset separately**: Fetch training/validation zips from IARAI cloud.
4. **Place dataset**: Move the folders to `D:\slideland\dataset\Landslide4Sense\`.
5. **Verify structure**: Check structure via the checklist.
6. **Run dashboard locally**: Double-click `start_dev.bat` to spin up DRF backend and React frontend.

---

## 7. Model Evaluation
The baseline U-Net was evaluated globally across all $12,451,840$ pixels in the $760$ holdout validation split:
*   **Pixel Accuracy**: `96.38%`
*   **Precision**: `35.60%`
*   **Recall**: `80.31%`
*   **F1 / Dice Score**: `49.33%`
*   **Intersection over Union (IoU)**: `32.74%`
*   **Average Validation Loss (Combined BCE + Dice)**: `0.4380`

---

## 8. Rainfall Integration
Dynamic weather readings are handled by the features module inside `ai_ml/features/rainfall.py`. This script extracts window precipitation totals:
*   `rainfall_24h_mm`: Cumulative 24-hour forecast precipitation.
*   `rainfall_3d_mm`, `rainfall_7d_mm`, `rainfall_14d_mm`: Cumulative historical antecedent precipitation.
*   `max_rainfall_14d_mm`, `heavy_rain_days`: Structural rainfall trigger events.

---

## 9. Risk Engine
The risk engine (`ai_ml/risk_model/risk_engine.py`) maps the dynamic landslide risk rating using domain-expert thresholds:
*   **ML Segmentation Score (50%)**: Derived linearly from landslide probability (max 25 pts) and area percentage capped at 15.0% (max 25 pts).
*   **Rainfall Feature Score (50%)**: Computed from 24h forecast (max 15 pts), 3d rain (max 15 pts), 7d rain (max 10 pts), and 14d rain (max 10 pts).
*   **Heuristic Risk Rating**:
    *   $\ge 75$: `critical`
    *   $\ge 50$: `high`
    *   $\ge 25$: `moderate`
    *   $< 25$: `low`

---

## 10. 5 km Road-Risk Screening
*   **Geospatial Scope**: Analyzes road networks within a 5 km radius surrounding the monitored zone center.
*   **Proximity-Based Screening**: Highlights road risk categories based on distance to the zone center, driven by the overall ML output risk level:
    *   *High Risk (Avoid)*: Distance $\le 1.0\text{ km}$ under overall High/Critical zone risk (RED).
    *   *Moderate Risk (Caution)*: Distance $\le 2.5\text{ km}$ under overall High/Critical zone risk, or $\le 2.0\text{ km}$ under Moderate zone risk (ORANGE).
    *   *Low Risk (Low Risk)*: Beyond caution thresholds but inside the 5 km monitoring zone (GREEN).
*   **Demo Disclaimer**: This is a spatial proximity screening feature for demonstration purposes. It does **not** model structural road failures or calculate individual slope collapse probabilities.

---

## 11. Backend — Django + Django REST Framework
The backend service resides in `backend/`. It exposes REST APIs for querying zone statistics, alerts, and roads, and integrates the PyTorch U-Net predictor adapter dynamically.

---

## 12. Database — SQLite
The development environment is configured with a local SQLite database (`backend/db.sqlite3`) managing seeded station zones and cached precipitation telemetry. For high-scale production, this can be migrated to PostgreSQL/PostGIS.

---

## 13. Frontend — React + Leaflet
The user dashboard resides in `frontend/`. It uses React (bootstrapped with Vite) and React-Leaflet to project map markers, sparkline charts, and warning panels.

---

## 14. API Endpoints
*   `GET /api/zones/` - List all monitored zones (live rainfall, overall risk rating, sparkline series).
*   `GET /api/zones/<id>/` - Retrieve a single zone's details.
*   `POST /api/zones/<id>/refresh/` - Force an API re-fetch from Open-Meteo, bypassing cache.
*   `GET /api/stats/` - Retrieve overall dashboard metrics (monitored, covers, high/critical counts).
*   `GET /api/alerts/` - Retrieve active alerts sorted by severity.
*   `GET /api/zones/<id>/affected-roads/` - Retrieve the GeoJSON road network within 5 km of the zone center, with risk attributes.

---

## 15. Project Structure
```text
D:\slideland/
├── ai_ml/                   # Deep learning and feature engineering modules
│   ├── preprocessing/       # Normalization and standardization
│   ├── segmentation/        # U-Net PyTorch models & dataloaders
│   ├── inference/           # Standalone and adapter predictors
│   ├── risk_model/          # Heuristic risk engine & unit tests
│   └── models/              # Checkpoint model file and evaluation CSVs
│
├── backend/                 # Django REST Framework backend
│   ├── monitoring/          # API models, serializers, views, and unit tests
│   └── prahari/             # Project settings, routing, and configurations
│
├── frontend/                # Vite React application
│   ├── src/                 # Application components, Leaflet map, API hooks
│   └── public/              # Static visual assets
│
└── dataset/                 # Landslide4Sense dataset directory (local only)
```

---

## 16. AI/ML Setup
1.  Navigate to the project root and activate the pre-configured virtual environment:
    *   **PowerShell**: `.\.venv\Scripts\Activate.ps1`
    *   **CMD**: `.\.venv\Scripts\activate.bat`
2.  Install dependencies:
    ```bash
    pip install -r ai_ml/requirements.txt
    ```

---

## 17. Backend Setup
1.  From the `backend/` directory, apply database migrations:
    ```bash
    python manage.py migrate
    ```
2.  Seed the default stations:
    ```bash
    python manage.py loaddata seed_zones.json
    ```

---

## 18. Frontend Setup
1.  From the `frontend/` directory, install package dependencies:
    ```bash
    npm install
    ```

---

## 19. How to Run Locally

### Start Django Backend
From the `backend/` folder:
```bash
python manage.py runserver
```
The server will run on `http://127.0.0.1:8000/`.

### Start Vite React Frontend
From the `frontend/` folder:
```bash
npm run dev
```
The dashboard will run on `http://localhost:5173/`.

---

## 20. Model Inference
To run a standalone U-Net prediction from Python:
```python
from ai_ml.inference.predictor import SlideAlertPredictor

predictor = SlideAlertPredictor()
res = predictor.predict_image("D:/slideland/dataset/Landslide4Sense/TrainData/img/image_241.h5", threshold=0.5)
print("Landslide Probability:", res["landslide_probability"])
print("Landslide Area %:", res["landslide_area_percent"])
```

---

## 21. Model Evaluation
To execute the evaluation script and refresh all baseline metrics and threshold charts:
```bash
python ai_ml/models/evaluation/run_evaluation.py
```
This updates files inside `ai_ml/models/evaluation/`.

---

## 22. Testing
*   **Run Django API tests**:
    ```bash
    python backend/manage.py test monitoring
    ```
*   **Run Risk Engine unit tests**:
    ```bash
    python -m unittest ai_ml/risk_model/test_risk_engine.py
    ```

---

## 23. Important Limitations
1.  **Static Segmentation**: The deep learning model identifies *existing* landslides in remote sensing imagery. It is not a predictive modeling tool for future slope failure events.
2.  **Uncalibrated Thresholds**: The 0.50 classification boundary is standard but not statistically optimized. Physical deployments require ROC curve calibrations to balance false warnings.
3.  **Heuristic Risk**: Due to a lack of time-aligned landslide occurrence logs, the risk rating relies on geological threshold rules rather than supervised tabular model training (such as XGBoost).

---

## 24. Team Development Notes
*   **Virtual Environments**: Do not commit the local virtual environment `.venv/` to Git.
*   **Datasets**: Keep `dataset/` under root ignored.
*   **Weight File**: `ai_ml/models/baseline_unet_best.pth` is tracked using Git LFS due to its size (65.95 MB). Do not commit duplicate weight files.
