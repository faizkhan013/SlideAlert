# SlideAlert U-Net Baseline Training Report

This report documents the training parameters, dataset split, validation metrics, and qualitative outcomes of the **Baseline U-Net** experiment.

---

## 1. Dataset & Preprocessing

- **Dataset**: Landslide4Sense (2022)
- **Dataset Location**: `D:\slideland\dataset\Landslide4Sense`
- **Input Dimensions**: $128 \times 128$ spatial pixels
- **Input Channels**: 14 (12 Sentinel-2 multispectral bands + 1 ALOS PALSAR Slope band + 1 ALOS PALSAR DEM band)
- **Preprocessing**: Channel-wise normalization (subtraction of baseline training means, division by standard deviations)
- **Augmentation**: Simple spatial transformations applied identically to image and mask:
  - Random horizontal flips ($p = 0.5$)
  - Random vertical flips ($p = 0.5$)
  - Random 90-degree rotations (0°, 90°, 180°, 270°)

---

## 2. Dataset Split Configuration

To establish a clean validation environment, the training set was split programmatically using a fixed random seed:
- **Random Seed**: `42`
- **Split Ratio**: 80% training / 20% holdout validation
- **Total Training Samples**: `3,039` files (logged in `train_split.txt`)
- **Total Holdout Validation Samples**: `760` files (logged in `val_split.txt`)

> [!IMPORTANT]
> **Scientific Rule**: The holdout validation results presented in this report represent an **Internal labeled holdout evaluation** using a deterministic subset of the Landslide4Sense training dataset. They do not represent the official Landslide4Sense competition/test leaderboard score. The public validation set was not used as training validation.

---

## 3. Model & Hyperparameters

- **Model Architecture**: 2D U-Net (14 input channels, 1 output channel mapping to logits)
- **Loss Function**: Combined BCE + Dice Loss (weighted 50% each)
- **Optimizer**: Adam
- **Learning Rate**: `1e-3`
- **Weight Decay**: `5e-4`
- **Batch Size**: `16`
- **Epochs**: `1` (configured for immediate CPU execution verification)
- **Early Stopping**: Patience = `5` (monitored validation F1 score)
- **Execution Device**: CPU (NVIDIA CUDA not available on host machine)

---

## 4. Training Performance and Metrics

The model was evaluated on the **Internal labeled holdout evaluation** set (760 samples) using the best epoch checkpoint:

- **Training Time**: `2007.5` seconds (~33.46 minutes)
- **Best Epoch**: `1`
- **Best Validation F1**: `0.4933`
- **Validation IoU (Jaccard Index)**: `0.3274`
- **Validation Precision**: `0.3560`
- **Validation Recall**: `0.8031`
- **Overall Accuracy**: `0.9638`
- **Validation Loss**: `0.3354`

### Pixel Statistics
- **Total Validation Pixels**: `12,451,840`
- **True Landslide Pixels**: `273,450` (2.20%)
- **True Non-Landslide Pixels**: `12,178,390` (97.80%)
- **Predicted Landslide Pixels**: `616,898` (4.95%)

---

## 5. Artifact and Output Paths

- **Best Model Checkpoint Path**: `D:\slideland\ai_ml\models\baseline_unet_best.pth`
- **Training History CSV Path**: `D:\slideland\ai_ml\models\baseline_training_history.csv`
- **Qualitative Predictions Directory**: `D:\slideland\ai_ml\models\baseline_predictions\`
  - Generates 4-panel image comparisons showing: Elevation (DEM) $\rightarrow$ Ground Truth Mask $\rightarrow$ Predicted Probability Map $\rightarrow$ Predicted Binary Mask.
  - Plotted samples:
    *   `prediction_image_241.png`
    *   `prediction_image_1554.png`
    *   `prediction_image_1561.png`
    *   `prediction_image_1851.png`
    *   `prediction_image_3557.png`

---

## Final Status

BASELINE TRAINING COMPLETED
