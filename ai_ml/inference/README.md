# SlideAlert AI/ML Inference Package

This sub-module provides the production-ready inference execution layer for the SlideAlert landslide detection segmentation model.

---

## Model Checkpoint
- **Standard Location**: `D:\slideland\ai_ml\models\baseline_unet_best.pth`
- **Architecture**: PyTorch 2D U-Net (14 input channels, 1 output channel mapping to logits).

---

## Input Image Format
- **Format**: HDF5 file (`.h5`) containing a dataset named `'img'`.
- **Dimensions**: Shape `(128, 128, 14)` or `(14, 128, 128)`.
- **Dtype**: Stored as `float64`, automatically converted to `float32` upon load.
- **Bands Info**:
  - Channels 0-11: Sentinel-2 Multispectral bands (B1-B12, B8a omitted).
  - Channel 12: ALOS PALSAR Slope.
  - Channel 13: ALOS PALSAR DEM (Elevation).

---

## Preprocessing
The input image is normalized using standard Landslide4Sense constants before running U-Net predictions:
$$\text{Normalized Channel} = \frac{\text{Raw Channel} - \text{Mean}}{\text{Std}}$$
Where the channel-wise means and stds are:
- `mean = [-0.4914, -0.3074, -0.1277, -0.0625, 0.0439, 0.0803, 0.0644, 0.0802, 0.3000, 0.4082, 0.0823, 0.0516, 0.3338, 0.7819]`
- `std = [0.9325, 0.8775, 0.8860, 0.8869, 0.8857, 0.8418, 0.8354, 0.8491, 0.9061, 1.6072, 0.8848, 0.9232, 0.9018, 1.2913]`

---

## Configurable Threshold
The segmentation model outputs sigmoid probability maps where each pixel value is in the range `[0.0, 1.0]`. Pixels are classified as landslide if their probability exceeds a configurable threshold. The default threshold is `0.5`, which should be calibrated based on precision-recall requirements.

---

## Core Output Fields
When calling `SlideAlertPredictor.predict_image`, the returned dictionary contains:
- `probability_map`: Sigmoid spatial output (`(128, 128)`)
- `binary_mask`: Thresholded spatial mask (`(128, 128)`)
- `landslide_probability`: Maximum probability value in the map (range `[0.0, 1.0]`)
- `landslide_pixel_count`: Number of pixels predicted as landslide (value `1` in mask)
- `total_pixel_count`: Total pixels in the patch (`16,384`)
- `landslide_area_percent`: Percentage of predicted landslide pixels over total pixels
- `mean_probability`: Average probability across the map
- `max_probability`: Equivalent to `landslide_probability`
- `segmentation_threshold`: The threshold value utilized during evaluation

---

## Example Programmatic Usage

```python
import sys
sys.path.append("D:/slideland")

from ai_ml.inference.predictor import SlideAlertPredictor

# Initialize predictor (automatically selects CUDA/CPU)
predictor = SlideAlertPredictor()

# Run prediction
results = predictor.predict_image("D:/slideland/dataset/Landslide4Sense/TrainData/img/image_1.h5", threshold=0.5)

print(f"Max Probability : {results['landslide_probability']}")
print(f"Area Percentage : {results['landslide_area_percent']:.2f}%")
```

---

## Command Line Interface (CLI) Test

You can run direct command-line inference on any HDF5 file using the following command:

```bash
D:\slideland\.venv\Scripts\python.exe -m ai_ml.inference.predictor D:\slideland\dataset\Landslide4Sense\TrainData\img\image_1.h5 --threshold 0.5
```

---

## Scientific Limitation Note

The U-Net model output is a **spatial landslide presence segmentation mask**. It must NOT be interpreted as a "future landslide forecast". Instead, this spatial output provides static landslide presence mapping which the SlideAlert risk classification layer will later combine with rainfall datasets and geological triggers to estimate warning risk levels.
