"""
predictor.py - Django-facing interface for running live SlideAlert predictions.
Supports U-Net spatial segmentation, thresholding, and risk evaluation stub interfaces.
"""
import os
import sys
import argparse
import h5py
import numpy as np
import torch

# Ensure slideland root is in search path
sys.path.append("D:/slideland")

from ai_ml.preprocessing.normalization import BandNormalizer
from ai_ml.segmentation.model import UNet

# Project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Candidate production model (Experiment 2) with baseline fallback available
FALLBACK_BASELINE_PATH = os.path.join(BASE_DIR, "ai_ml", "models", "baseline_unet_best.pth")
DEFAULT_MODEL_PATH = os.environ.get(
    "SLIDEALERT_MODEL_PATH",
    os.path.join(BASE_DIR, "ai_ml", "models", "experiments", "improved_unet", "improved_unet_v2_best.pth")
)

class SlideAlertPredictor:
    """
    Standard interface called by monitoring views and services.
    Loads models and executes inference pipelines.
    """
    def __init__(self, model_path=None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = UNet(n_channels=14, n_classes=1)
        self.normalizer = BandNormalizer()
        
        path = model_path if model_path else os.environ.get("SLIDEALERT_MODEL_PATH", DEFAULT_MODEL_PATH)
        if not os.path.exists(path) and os.path.exists(FALLBACK_BASELINE_PATH):
            path = FALLBACK_BASELINE_PATH

        if os.path.exists(path):
            self.model.load_state_dict(torch.load(path, map_location=self.device))
            # print(f"Model loaded successfully from: {path} on device: {self.device}")
        else:
            print(f"Warning: Model checkpoint not found at: {path}. Using random weights.")
            
        self.model.to(self.device)
        self.model.eval()

    def predict_image(self, image_numpy_or_path, threshold=0.5):
        """
        Runs U-Net inference on a single 14-band image.
        image_numpy_or_path: numpy array of shape (128, 128, 14) or (14, 128, 128),
                             or an absolute path to a .h5 file.
        threshold: floating point segmentation threshold (0.0 to 1.0)
        """
        # Load from path if string
        if isinstance(image_numpy_or_path, str):
            if not os.path.exists(image_numpy_or_path):
                raise FileNotFoundError(f"Image file not found: {image_numpy_or_path}")
            with h5py.File(image_numpy_or_path, "r") as hf:
                image_numpy = hf["img"][:]
        else:
            image_numpy = image_numpy_or_path

        # Shape formatting: Ensure channel-first (14, 128, 128)
        if image_numpy.shape[2] == 14:
            image_numpy = image_numpy.transpose((-1, 0, 1))

        # Convert to float32
        image_numpy = np.asarray(image_numpy, dtype=np.float32)
        
        # Apply standardization normalization
        image_norm = self.normalizer.normalize_numpy(image_numpy)
        
        # Convert to tensor and run inference
        image_tensor = torch.from_numpy(image_norm).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            logits = self.model(image_tensor)
            probabilities = torch.sigmoid(logits).squeeze(0).squeeze(0).cpu().numpy()
            
        binary_mask = (probabilities >= threshold).astype(np.uint8)
        
        # Calculations
        total_pixels = int(binary_mask.size)
        predicted_landslide_pixels = int(np.sum(binary_mask == 1))
        landslide_area_percent = (predicted_landslide_pixels / total_pixels) * 100.0
        
        max_prob = float(probabilities.max())
        mean_prob = float(probabilities.mean())
        
        return {
            "probability_map": probabilities,
            "binary_mask": binary_mask,
            "landslide_probability": max_prob,
            "landslide_pixel_count": predicted_landslide_pixels,
            "total_pixel_count": total_pixels,
            "landslide_area_percent": float(landslide_area_percent),
            "mean_probability": mean_prob,
            "max_probability": max_prob,
            "segmentation_threshold": float(threshold)
        }

    def predict_zone(self, image_numpy, rainfall_series, threshold=0.5):
        """
        Runs the combined spatial U-Net + temporal rainfall alert inference.
        Kept for backward-compatibility with django services.
        """
        seg_results = self.predict_image(image_numpy, threshold=threshold)
        area_pct = seg_results["landslide_area_percent"]
        
        # Simple combined alert heuristic
        latest_rainfall = rainfall_series[-1] if rainfall_series else 0.0
        risk_score = min(area_pct * 3.0 + latest_rainfall * 0.5, 100.0)
        
        if risk_score > 75.0 or latest_rainfall > 115.5:
            risk_level = "critical"
        elif risk_score > 45.0 or latest_rainfall >= 64.5:
            risk_level = "high"
        elif risk_score > 15.0 or latest_rainfall >= 15.6:
            risk_level = "moderate"
        else:
            risk_level = "low"
            
        risk_factors = []
        if latest_rainfall >= 64.5:
            risk_factors.append("Heavy rainfall")
        if area_pct > 10.0:
            risk_factors.append("Active landslide segments detected")
        if not risk_factors:
            risk_factors.append("Stable terrain indices")
            
        return {
            "landslide_probability": seg_results["landslide_probability"],
            "landslide_area_percent": float(area_pct),
            "confidence": 0.85,
            "risk_score": int(risk_score),
            "risk_factors": risk_factors,
            "risk_level": risk_level,
            "mean_probability": seg_results["mean_probability"],
            "max_probability": seg_results["max_probability"],
            "segmentation_threshold": float(threshold)
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SlideAlert Inference Predictor CLI")
    parser.add_argument("image_path", type=str, help="Path to Landslide4Sense .h5 image file")
    parser.add_argument("--threshold", type=float, default=0.5, help="Segmentation probability threshold (default: 0.5)")
    parser.add_argument("--model_path", type=str, default=None, help="Custom U-Net model checkpoint path")
    
    args = parser.parse_args()
    
    try:
        predictor = SlideAlertPredictor(model_path=args.model_path)
        res = predictor.predict_image(args.image_path, threshold=args.threshold)
        
        print("\n=== SLIDEALERT INFERENCE CLI ===")
        print(f"Image Path            : {args.image_path}")
        print(f"Device Used           : {predictor.device}")
        print(f"Segmentation Threshold: {res['segmentation_threshold']:.2f}")
        print(f"Mean Probability      : {res['mean_probability']:.4f}")
        print(f"Max Probability       : {res['max_probability']:.4f}")
        print(f"Landslide Pixel Count : {res['landslide_pixel_count']} / {res['total_pixel_count']}")
        print(f"Landslide Area %      : {res['landslide_area_percent']:.2f}%")
        print("================================")
    except Exception as e:
        print(f"Inference error: {e}")
        sys.exit(1)
