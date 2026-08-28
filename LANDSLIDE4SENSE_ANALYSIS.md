# Landslide4Sense Dataset and Baseline Analysis Report

This document reviews the **Landslide4Sense (2022)** dataset and baseline implementation, assesses its alignment with the **SlideAlert** backend, and details the recommended AI/ML integration pipeline.

---

## 1. Dataset Availability

After a recursive filesystem search inside `D:\slideland\Landslide4Sense-2022-main`, we report the following status:

- **Training dataset present**: NO
- **Validation dataset present**: NO
- **Test dataset present**: NO
- **Total .h5 files**: 0
- **Total .hdf5 files**: 0
- **Total .npy files**: 0
- **Total .npz files**: 0
- **Exact directories containing them**: None (the directories `TrainData/`, `ValidData/`, and `TestData/` referenced in the baseline README do not exist in the current workspace).

---

## 2. HDF5 Structure & Format

Although the `.h5` files are not present in the local workspace, the dataset format is defined in `dataset/landslide_dataset.py` and the README:

- **Dataset Keys**:
  - Image files: `'img'`
  - Mask files: `'mask'`
- **Array Shapes**:
  - Raw image: `(128, 128, 14)` (representing Height $\times$ Width $\times$ Channels)
  - Loaded tensor: `(14, 128, 128)` (after `transpose((-1, 0, 1))` in PyTorch)
  - Mask: `(128, 128)` (Height $\times$ Width)
- **Data Types**:
  - Images: `float32` (processed as `np.float32`)
  - Labels/Masks: `float32` (processed as `np.float32` during training; saved as `uint8` during inference)
- **Value Ranges**:
  - Satellite bands are normalized in the loader using channel-specific mean and standard deviation values.
- **Label Codes**:
  - `0`: Non-landslide (Background)
  - `1`: Landslide
  - It is a **binary semantic segmentation** task.

---

## 3. The 14 Input Bands (Channels)

The 14 channels in each image patch represent the following sensor measurements:

| Band Index (0-indexed) | Band Name | Upstream Sensor / Source | Resolution |
| :---: | :--- | :--- | :--- |
| `0` | **B1** (Aerosols) | Sentinel-2 Multispectral | ~10m (resampled) |
| `1` | **B2** (Blue) | Sentinel-2 Multispectral | ~10m |
| `2` | **B3** (Green) | Sentinel-2 Multispectral | ~10m |
| `3` | **B4** (Red) | Sentinel-2 Multispectral | ~10m |
| `4` | **B5** (Red Edge 1) | Sentinel-2 Multispectral | ~10m (resampled) |
| `5` | **B6** (Red Edge 2) | Sentinel-2 Multispectral | ~10m (resampled) |
| `6` | **B7** (Red Edge 3) | Sentinel-2 Multispectral | ~10m (resampled) |
| `7` | **B8** (NIR) | Sentinel-2 Multispectral | ~10m |
| `8` | **B9** (Water Vapor) | Sentinel-2 Multispectral | ~10m (resampled) |
| `9` | **B10** (SWIR - Cirrus) | Sentinel-2 Multispectral | ~10m (resampled) |
| `10` | **B11** (SWIR 1) | Sentinel-2 Multispectral | ~10m (resampled) |
| `11` | **B12** (SWIR 2) | Sentinel-2 Multispectral | ~10m (resampled) |
| `12` | **B13** (Slope) | ALOS PALSAR Radar | ~10m (resampled) |
| `13` | **B14** (DEM) | ALOS PALSAR Radar (Elevation) | ~10m (resampled) |

*Note: Band 8a in the Sentinel-2 image is omitted, meaning B1 to B12 map directly to the 12 standard Sentinel-2 spectral bands.*

---

## 4. Existing Baseline Code Review

The baseline implementation contains:
- **Dataset Loader** (`dataset/landslide_dataset.py`): Loads `.h5` files, applies channel transpose, and normalizes channels.
- **Preprocessing & Normalization** (`dataset/landslide_dataset.py`): Performs channel-wise standardization using hardcoded constants:
  - `mean = [-0.4914, -0.3074, -0.1277, -0.0625, 0.0439, 0.0803, 0.0644, 0.0802, 0.3000, 0.4082, 0.0823, 0.0516, 0.3338, 0.7819]`
  - `std = [0.9325, 0.8775, 0.8860, 0.8869, 0.8857, 0.8418, 0.8354, 0.8491, 0.9061, 1.6072, 0.8848, 0.9232, 0.9018, 1.2913]`
- **Augmentation**: None implemented in baseline.
- **Model Architecture** (`model/Networks.py`): A classic 2D U-Net mapping 14 input channels to 2 output classes. Uses double convolution blocks, max pooling for downscaling, bilinear upsampling for upscaling, and skip connections.
- **Loss Function & Optimizer** (`Train.py`): `CrossEntropyLoss(ignore_index=255)` with `Adam` optimizer (`lr=1e-3`, `weight_decay=5e-4`).
- **Training Process** (`Train.py`): Runs for 5000 steps (mini-batches) with a default batch size of 32. Validation is run every 500 steps.
- **Evaluation** (`utils/tools.py`): Computes pixel-wise true positives (TP), false positives (FP), true negatives (TN), and false negatives (FN). Report measures Overall Accuracy (OA), Precision, Recall, and F1-score of the landslide class.
- **Prediction/Inference** (`Predict.py`): Restores the model state dict from a saved `.pth` file, evaluates on unlabeled images, takes `argmax` over class probabilities, and dumps binary masks to `.h5` files under the key `mask`.

---

## 5. Pipeline Reuse Recommendations

| Pipeline Component | Recommendation | Justification |
| :--- | :--- | :--- |
| **Dataset Loader** | **MODIFY** | Keep HDF5 reader logic, but parameterize pathways for local inference wrappers. |
| **Preprocessing** | **REUSE** | The mean and standard deviation values must remain identical to match the pre-trained weights. |
| **Model Architecture** | **REUSE** | The baseline U-Net is functional, lightweight, and suitable for deployment inside Django. |
| **Training Code** | **NOT NEEDED** | We only need to run inference on the deployed model; training is performed offline. |
| **Evaluation** | **NOT NEEDED** | Offline metric validation is complete; not required for online API inference. |
| **Prediction** | **REPLACE** | Replace the file-based script (`Predict.py`) with an in-memory PyTorch evaluation wrapper that takes numpy arrays/in-memory data and outputs landslide probabilities and area percentages. |
| **Visualization** | **MODIFY** | The frontend MapPane and SparklinePanel should be retained as is, but we will modify them to display ML results. |

---

## 6. SlideAlert AI/ML Pipeline Design & Feasibility

### Proposed Pipeline
1. **Inputs**: 14-band satellite image patch + 14-day rainfall time-series.
2. **Step 1 (Segmentation)**: Standard U-Net model predicts pixel-wise landslide classification mask.
3. **Step 2 (Feature Extraction)**: Compute landslide area percentage:
$$\text{Area \%} = \frac{\text{Landslide Pixels}}{\text{Total Pixels (16,384)}} \times 100$$
4. **Step 3 (Risk Evaluation)**: Combine landslide area percentage, terrain slope/elevation features, and 14-day Open-Meteo rainfall indicators to assign a risk score (0-100) and risk level.
5. **Step 4 (Explainability)**: Use SHAP or Feature Importance to extract key triggers.

### Feasibility Analysis
- **Feasible**: Evaluating a pre-trained U-Net on 14-band satellite imagery to identify landslide extents and compute the area percentage.
- **Limitation (Data Access)**: The Django backend **does not** automatically fetch Sentinel-2 or ALOS PALSAR satellite bands for the monitored locations. Real-time satellite data acquisition is out of scope for the current backend. Therefore, the 14-band image patches must either be pre-loaded as static assets for the zones or fetched via a custom satellite search utility (which requires integration with planetary computer APIs or Google Earth Engine).
- **Limitation (Risk Model)**: Creating a second-stage model (like XGBoost) to map rainfall history + landslide areas to a risk score (0-100) requires training labels consisting of historical landslide event occurrences with timestamps. The Landslide4Sense dataset **does not** contain timestamped event histories mapping daily rainfall to actual sliding dates.

---

## 7. Open-Meteo Feature Integration

The Django backend currently fetches a 14-day series of precipitation sum values. The following rainfall features can be extracted:

1. **Available directly**:
   - `rainfall_24h_mm` (precipitation on the latest day).
2. **Derived from 14-day series**:
   - `rainfall_3d` (cumulative rainfall of the last 3 days - crucial for short-term triggers).
   - `rainfall_7d` (cumulative rainfall of the last 7 days).
   - `rainfall_14d` (cumulative rainfall of the last 14 days - representing antecedent soil saturation).
   - `max_rainfall_14d` (maximum daily rainfall within the 14-day window).
   - `mean_rainfall_14d` (average daily rainfall over 14 days).
   - `heavy_rain_days` (count of days in the 14-day window where precipitation exceeded a threshold like 15.6mm).
3. **Requires additional data**:
   - Forecast rainfall (for predictive early warning) or historical climate baseline.

---

## 8. Important Scientific Check

"Additional labelled historical rainfall + landslide-event data is required for supervised risk-model training."

We cannot train a robust, supervised machine learning model (e.g. XGBoost) to map rainfall data to zone-level risk tiers using only the Landslide4Sense dataset. The Landslide4Sense dataset contains spatial masks of landslides but lacks temporal alignment with daily meteorological triggers. In the absence of this data, the risk-scoring model should be based on established geological threshold formulas (e.g. antecedent rainfall index) rather than supervised learning.

---

## 9. Dataset Availability Status

**ACTUAL DATASET IS NOT PRESENT; ONLY CODE/BASELINE IS PRESENT**
