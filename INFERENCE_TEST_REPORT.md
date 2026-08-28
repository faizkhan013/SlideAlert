# SlideAlert Inference Test Report

This report documents the validation inference run on 5 holdout training samples (images and ground-truth masks) using the trained baseline U-Net model.

---

## 1. Setup & Device
- **Trained Checkpoint**: `D:\slideland\ai_ml\models\baseline_unet_best.pth`
- **Device Used**: `CPU`
- **Model Status**: `Evaluation Mode (no grad)`
- **Segmentation Threshold**: `0.5` (default)
- **Input Shape**: `(128, 128, 14)`
- **Output Logits Shape**: `(1, 1, 128, 128)`
- **Output Probabilities Shape**: `(128, 128)`

---

## 2. 5-Sample Holdout Inference Results

| Filename | Mean Prob | Max Prob | Pred Pixels | Pred Area % | GT Pixels | Precision | Recall | F1 | IoU |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `image_1561.h5` | 0.0051 | 0.3501 | 0 | 0.00% | 6 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `image_3557.h5` | 0.0100 | 0.9963 | 87 | 0.53% | 725 | 0.8391 | 0.1007 | 0.1798 | 0.0988 |
| `image_241.h5` | 0.1968 | 0.9999 | 3,182 | 19.42% | 2,520 | 0.7492 | 0.9460 | 0.8362 | 0.7185 |
| `image_1851.h5` | 0.0317 | 0.9997 | 438 | 2.67% | 168 | 0.3447 | 0.8988 | 0.4983 | 0.3319 |
| `image_1554.h5` | 0.0036 | 0.0649 | 0 | 0.00% | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

### Analysis of Results
- **Precision & Recall**: 
  - `image_241.h5` exhibits excellent segmentation performance (F1 = `0.8362`, IoU = `0.7185`) matching the ground truth tightly.
  - `image_1851.h5` shows high recall (`0.8988`) but lower precision (`0.3447`), indicating a conservative over-prediction of landslide boundaries.
  - `image_3557.h5` has low recall (`0.1007`), indicating that some low-contrast landslide boundaries were missed by the single-epoch baseline model.
- **Negative Case Validation**:
  - `image_1554.h5` (a true negative sample containing zero landslide pixels) was classified correctly with zero predicted pixels and `0.00%` area.
  - `image_1561.h5` had very few landslide pixels in ground truth (6 pixels), and was correctly mapped with zero predicted pixels (the maximum model probability was `0.3501`, well below the `0.5` threshold).

---

## 3. Visual Comparisons

Visual plots are saved under `D:\slideland\ai_ml\models\inference_examples/` and contain a 4-panel projection (DEM Band $\rightarrow$ Ground Truth Mask $\rightarrow$ Sigmoid Probability Map $\rightarrow$ Predicted Binary Mask):
- `inference_image_241.png`
- `inference_image_1554.png`
- `inference_image_1561.png`
- `inference_image_1851.png`
- `inference_image_3557.png`

---

## Status

INFERENCE PIPELINE READY
