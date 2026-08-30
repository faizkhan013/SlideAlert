# Final U-Net Model Evaluation & Performance Report

This report documents the performance evaluation of the trained baseline U-Net segmentation model on the Landslide4Sense holdout validation dataset.

---

## 1. Evaluation Configuration

*   **Dataset Used**: Landslide4Sense (Holdout Validation Set)
*   **Number of Evaluation Samples**: `760` patches (independent subset of TrainData)
*   **Input Dimensions**: 14 x 128 x 128 (14 multi-spectral/topographic bands)
*   **Model Architecture**: 2D U-Net (31M parameters, 14 input channels, 1 output channel)
*   **Checkpoint Used**: `baseline_unet_best.pth` (65.95 MB)
*   **Preprocessing / Normalization**: Multi-band standardization (subtract mean, divide by standard deviation per channel)
*   **Threshold**: `0.5` (default sigmoid classification threshold)
*   **Evaluation Device**: CPU (Intel-based environment)
*   **Approximate Evaluation Time**: `130 seconds` (~0.17 seconds per image)

---

## 2. Quantitative Performance Metrics

Calculated globally across all 12,451,840 pixels in the 760 holdout validation patches:

| Metric | Value | Interpretation |
| :--- | :---: | :--- |
| **Pixel Accuracy** | `96.38%` | High raw pixel agreement, heavily dominated by non-landslide background pixels. |
| **Precision** | `35.60%` | Probability that a predicted landslide pixel is actually a landslide (indicates some false positives). |
| **Recall** | `80.31%` | Proportion of actual landslide pixels successfully detected by the model (indicates high sensitivity). |
| **F1 Score** | `49.33%` | Harmonic mean of precision and recall (class-level balanced metric). |
| **Intersection over Union (IoU)** | `32.74%` | Jaccard index measuring the overlap area divided by union area of prediction vs. target. |
| **Dice Coefficient** | `49.33%` | Overlap metric mathematically equivalent to F1 score for binary classes. |

---

## 3. Class Imbalance & Pixel Distribution

Landslide hazard segmentation is extremely imbalanced. The global pixel counts are:

*   **Total Pixels**: `12,451,840`
*   **Landslide Pixels (Positive)**: `273,450` (**2.20%** of total pixels)
*   **Non-Landslide Pixels (Negative)**: `12,178,390` (**97.80%** of total pixels)

> [!WARNING]
> **Class Imbalance Note**:
> Because 97.80% of pixels belong to the non-landslide background class, a model that predicts "no landslide" everywhere would achieve 97.80% accuracy. Raw pixel accuracy alone is therefore a misleading metric. The **F1 Score (49.33%)** and **IoU (32.74%)** provide a much more realistic measurement of the model's true localization performance.

---

## 4. Confusion Matrix

The pixel-level confusion matrix is saved to `ai_ml/models/evaluation/confusion_matrix.csv`:

| Actual \ Predicted | Predicted Non-Landslide | Predicted Landslide |
| :--- | :---: | :---: |
| **Actual Non-Landslide** | `11,781,105` (TN) | `397,285` (FP) |
| **Actual Landslide** | `53,837` (FN) | `219,613` (TP) |

*   **True Positives (TP)**: `219,613` pixels (correctly mapped landslides)
*   **True Negatives (TN)**: `11,781,105` pixels (correctly mapped background)
*   **False Positives (FP)**: `397,285` pixels (false alarms)
*   **False Negatives (FN)**: `53,837` pixels (missed landslides)

---

## 5. Qualitative Predictions & Examples

The 10 example predictions have been saved under `ai_ml/models/evaluation/examples/`:
- `example_image_1561.png`
- `example_image_3557.png`
- `example_image_241.png` (Representative Sohra HDF5 patch)
- `example_image_1851.png` (Representative Mangan HDF5 patch)
- `example_image_1554.png`
- `example_image_854.png`
- `example_image_1296.png`
- `example_image_2990.png`
- `example_image_2177.png`
- `example_image_2236.png`

### Observations
1.  **High Sensitivity (Recall)**: The U-Net is highly capable of identifying landslide clusters and marking them correctly.
2.  **Over-segmentation (False Positives)**: The model tends to draw slightly larger boundary borders than the ground truth, resulting in a higher false positive count (397,285 pixels) and lower precision.
3.  **Clean Demarcation**: Topographic features (DEM, slope) strongly contribute to clean spatial boundaries around high-gradient valleys.

---

## 6. Data Leakage Assessment

*   **Independence**: **VERIFIED**. The evaluation images are entirely separate from the training set. The model checkpoint is frozen (`baseline_unet_best.pth`), and no evaluation samples were used to update model weights.
*   **Split Verification**: The `val_split.txt` and `train_split.txt` log files guarantee a clean, non-overlapping partition of the Landslide4Sense dataset.

---

## 7. Scientific Limitations

> [!IMPORTANT]
> **Important Scientific Classifications**:
> 1.  **Spatial Segmentation, Not Forecasting**: The U-Net model performs **spatial image segmentation** (locating existing landslides in satellite imagery). It does **not** predict future landslide occurrences.
> 2.  **Rainfall Risk Correlation**: To compute future warnings, the SlideAlert risk engine combines this spatial vulnerability index with dynamic meteorological telemetry (Open-Meteo rainfall forecasting).
> 3.  **Baseline Threshold**: The current model uses a standard decision boundary (0.5). In physical applications, this threshold must be calibrated using receiver operating characteristic (ROC) curves to balance false alarm rates.
