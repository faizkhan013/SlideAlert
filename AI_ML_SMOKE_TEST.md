# SlideAlert AI/ML Module Smoke Test Report

This document records the results of the environment validation and the dataset/model pipeline smoke test.

---

## 1. Environment & Package Verification

- **Python Version**: `3.12.10` (64-bit)
- **Virtual Environment Path**: `D:\slideland\.venv`
- **NVIDIA CUDA Availability**: `False` (CPU-only build installed)
- **GPU Name**: `None` (System utilizes Intel(R) Iris(R) Xe Graphics)
- **Library Versions**:
  - `numpy`: `2.5.2`
  - `pandas`: `3.0.5`
  - `h5py`: `3.16.0`
  - `torch`: `2.13.0+cpu`
  - `torchvision`: `0.28.0+cpu`
  - `scikit-learn`: `1.9.0`
  - `matplotlib`: `3.11.1`

---

## 2. Dataset Loader Test

- **Dataset Path**: `D:\slideland\dataset\Landslide4Sense`
- **Total Samples Detected**: `3,799` images
- **Sample 0 (`image_1.h5`)**:
  - Image shape: `[14, 128, 128]` | Dtype: `torch.float32` | NaNs: `False` | Infs: `False`
  - Mask shape: `[128, 128]` | Dtype: `torch.float32` | NaNs: `False` | Infs: `False` | Unique values: `[0.0, 1.0]`
  - Validation: **OK** (Passes all DataValidator dimensions and quality checks)
- **Sample 1 (`image_10.h5`)**:
  - Image shape: `[14, 128, 128]` | Dtype: `torch.float32` | NaNs: `False` | Infs: `False`
  - Mask shape: `[128, 128]` | Dtype: `torch.float32` | NaNs: `False` | Infs: `False` | Unique values: `[0.0]`
  - Validation: **OK** (All background pixels)
- **Sample 2 (`image_100.h5`)**:
  - Image shape: `[14, 128, 128]` | Dtype: `torch.float32` | NaNs: `False` | Infs: `False`
  - Mask shape: `[128, 128]` | Dtype: `torch.float32` | NaNs: `False` | Infs: `False` | Unique values: `[0.0, 1.0]`
  - Validation: **OK**

*Verification confirms that images are read lazily one at a time and PyTorch tensors have correct float32 precision, shapes, and normalization.*

---

## 3. DataLoader Batch Test

- **Configured Batch Size**: `2`
- **Images Batch Shape**: `[2, 14, 128, 128]`
- **Masks Batch Shape**: `[2, 128, 128]`
- **Status**: **PASSED** (Batch shape contains correct channel and spatial dimensions)

---

## 4. U-Net Forward Pass Test

- **Configured Channels**: Input = 14, Output = 1
- **Forward Pass Logits Shape**: `[2, 1, 128, 128]`
- **Output Dtype**: `torch.float32`
- **Output Quality Check**: NaNs = `False` | Infs = `False`
- **Status**: **PASSED**

---

## 5. Loss Calculation Test

- **Loss Formula**: `CombinedLoss(0.5 * BCE + 0.5 * Dice)`
- **Loss Value**: `0.9703255891799927`
- **Dtype**: `float` (Python scalar)
- **Is Finite**: `True`
- **Status**: **PASSED**

---

## 6. Metric Evaluation Test

Calculated on predictions vs target masks:
- **`overall_accuracy`**: `0.057098`
- **`precision`**: `0.007263`
- **`recall`**: `0.969957`
- **`f1_score`**: `0.014418`
- **`iou`**: `0.007261`
- **Status**: **PASSED** (Functionally correct and runs without divide-by-zero crashes)

---

## 7. Single Prediction Helper Test

Tested on raw file loading:
- **Probability Map Shape**: `[128, 128]`
- **Binary Mask Shape**: `[128, 128]`
- **Area Percentage Calculation**: `100.0` (evaluated on untrained model weights)
- **Status**: **PASSED**

---

## 8. Errors & Fixes
- None encountered. Import mappings and tensor dimensions align with expectations.

---

## Final Status

SMOKE TEST PASSED — READY FOR TRAINING
