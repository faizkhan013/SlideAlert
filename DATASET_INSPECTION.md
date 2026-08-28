# Landslide4Sense HDF5 Dataset Inspection Report

This document records the detailed content verification, band meanings, data types, value distributions, and data quality check of the HDF5 files (`.h5`) in the **Landslide4Sense** dataset.

---

## 1. Directory and File Summary

The dataset structure is verified as follows:
- **Training Image Directory**: `D:\slideland\dataset\Landslide4Sense\TrainData\img`
  - Total files: `3,799` files (named `image_1.h5` through `image_3799.h5`)
- **Training Mask Directory**: `D:\slideland\dataset\Landslide4Sense\TrainData\mask`
  - Total files: `3,799` files (named `mask_1.h5` through `mask_3799.h5`)
- **Validation Directory**: `D:\slideland\dataset\Landslide4Sense\ValidData`
  - `ValidData/img/`: `245` files (named `image_1.h5` through `image_245.h5`)
  - `ValidData/mask/`: `245` files (named `mask_1.h5` through `mask_245.h5`)

---

## 2. Representative Training Image Analysis (`image_1.h5`)

A check on a representative training image (`TrainData/img/image_1.h5`) yields the following HDF5 telemetry:
- **HDF5 Keys**: `['img']`
- **Array Shape**: `(128, 128, 14)` (representing Height $\times$ Width $\times$ Channels)
- **Data Type**: `float64` (in the file, but standard PyTorch dataloaders cast this to `float32` before feeding to the network)
- **Number of Channels**: `14`
- **Spatial Dimensions**: `128 x 128` pixels
- **Statistical Summary**:
  - Minimum value: `0.0`
  - Maximum value: `6.397335147428777`
  - Mean value: `1.3700195019139179`
  - Standard deviation: `0.35815143774344566`
- **Missing/Anomaly count**:
  - NaN count: `0`
  - Infinite-value count: `0`

---

## 3. Representative Training Mask Analysis (`mask_1.h5`)

A check on the corresponding mask (`TrainData/mask/mask_1.h5`) yields the following HDF5 telemetry:
- **HDF5 Keys**: `['mask']`
- **Array Shape**: `(128, 128)` (Height $\times$ Width)
- **Data Type**: `uint8`
- **Unique Values**: `0` and `1` (binary semantic segmentation)
  - `0`: Non-landslide (Background) - Count: `15,979` pixels
  - `1`: Landslide - Count: `405` pixels
- **Missing/Anomaly count**:
  - NaN count: `0`
  - Infinite-value count: `0`

---

## 4. Image-Mask Pairing Verification

We verified the pairing between the `img` and `mask` folders for all files using a Python comparison script.
- **Naming Pattern**: `image_x.h5` $\leftrightarrow$ `mask_x.h5` (where `x` matches the sample index).
- **Tested Pairs**:
  - `image_1.h5` $\leftrightarrow$ `mask_1.h5` (Verified)
  - `image_25.h5` $\leftrightarrow$ `mask_25.h5` (Verified)
  - `image_100.h5` $\leftrightarrow$ `mask_100.h5` (Verified)
  - `image_500.h5` $\leftrightarrow$ `mask_500.h5` (Verified)
  - `image_1000.h5` $\leftrightarrow$ `mask_1000.h5` (Verified)
- **Global Check**: Zero mismatches exist across all 3,799 training files and all 245 validation files.

---

## 5. The 14 Channels (Bands) Ordering

The channels are stored in the following sequential order inside the HDF5 image arrays:

| Channel Index | Dataset Band | Meaning | Source Sensor | Spatial Resolution |
| :---: | :---: | :--- | :--- | :---: |
| **0** | B1 | Coastal Aerosol | Sentinel-2 Multispectral | ~10m |
| **1** | B2 | Blue | Sentinel-2 Multispectral | ~10m |
| **2** | B3 | Green | Sentinel-2 Multispectral | ~10m |
| **3** | B4 | Red | Sentinel-2 Multispectral | ~10m |
| **4** | B5 | Red Edge 1 | Sentinel-2 Multispectral | ~10m |
| **5** | B6 | Red Edge 2 | Sentinel-2 Multispectral | ~10m |
| **6** | B7 | Red Edge 3 | Sentinel-2 Multispectral | ~10m |
| **7** | B8 | NIR (Near Infrared) | Sentinel-2 Multispectral | ~10m |
| **8** | B9 | Water Vapor | Sentinel-2 Multispectral | ~10m |
| **9** | B10 | SWIR - Cirrus | Sentinel-2 Multispectral | ~10m |
| **10** | B11 | SWIR 1 | Sentinel-2 Multispectral | ~10m |
| **11** | B12 | SWIR 2 | Sentinel-2 Multispectral | ~10m |
| **12** | B13 | Slope | ALOS PALSAR Radar | ~10m |
| **13** | B14 | DEM (Digital Elevation Model) | ALOS PALSAR Radar | ~10m |

*Note: Band 8a in the standard Sentinel-2 spectral channel list is omitted from the dataset.*

---

## 6. Validation Data Inspection

Inspection of a validation sample (`ValidData/img/image_1.h5`) confirms:
- **Keys**: `['img']`
- **Shape**: `(128, 128, 14)`
- **Data Type**: `float64`
- **Value Range**: `0.0` to `13.37554678749841` (depending on the image)
- **Validation Masks**: **YES**, validation masks are provided under `ValidData/mask/` (e.g., `mask_10.h5` contains landslide labels `[0, 1]`). This allows full validation computations offline before inference tests.

---

## 7. Data Quality Findings

A subset scan of the first 20 training images was performed to verify quality:
- **NaN / Infinite values**: `0` found.
- **Zero Channels**: No channels are completely zero (`0/20` files).
- **Constant Channels**: No channels are constant/unvarying across the spatial patch (`0/20` files).
- **Dimensions**: All files match the expected `(128, 128, 14)` and `(128, 128)` sizes.

---

## 8. Recommendations for Preprocessing

1. **Precision Reduction**: Convert the `float64` imagery data to `float32` during dataset loading. This reduces memory footprint by 50% and matches PyTorch deep learning parameters.
2. **Standardization**: Standardize the channels using the pre-computed training mean and std values in the baseline loader:
   - `mean = [-0.4914, -0.3074, -0.1277, -0.0625, 0.0439, 0.0803, 0.0644, 0.0802, 0.3000, 0.4082, 0.0823, 0.0516, 0.3338, 0.7819]`
   - `std = [0.9325, 0.8775, 0.8860, 0.8869, 0.8857, 0.8418, 0.8354, 0.8491, 0.9061, 1.6072, 0.8848, 0.9232, 0.9018, 1.2913]`
3. **Data Augmentation**: To improve model generalization, apply random horizontal/vertical flips during training (carefully keeping image and label masks aligned).
4. **Imbalance Handling**: The landslide class (1) has significantly fewer pixels than background (0) (e.g., ~2.5% in `mask_1.h5`). Consider using weighted CrossEntropyLoss or Dice Loss to mitigate class imbalance.

---

## Status

DATA STRUCTURE VERIFIED — READY FOR PREPROCESSING
