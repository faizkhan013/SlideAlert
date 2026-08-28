import numpy as np
import torch

# Constants from Landslide4Sense baseline
# Order of 14 bands: B1-B12 (Sentinel-2), B13 (Slope), B14 (DEM)
BAND_MEANS = [-0.4914, -0.3074, -0.1277, -0.0625, 0.0439, 0.0803, 0.0644, 0.0802, 0.3000, 0.4082, 0.0823, 0.0516, 0.3338, 0.7819]
BAND_STDS = [0.9325, 0.8775, 0.8860, 0.8869, 0.8857, 0.8418, 0.8354, 0.8491, 0.9061, 1.6072, 0.8848, 0.9232, 0.9018, 1.2913]

class BandNormalizer:
    """
    Standard normalizer for Landslide4Sense 14-channel satellite imagery.
    Standardizes each channel based on baseline training statistics.
    """
    def __init__(self, means=BAND_MEANS, stds=BAND_STDS):
        self.means = np.array(means, dtype=np.float32)
        self.stds = np.array(stds, dtype=np.float32)

    def normalize_numpy(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize a numpy array of shape (C, H, W).
        """
        C, H, W = image.shape
        assert C == 14, f"Expected 14 channels, got {C}"
        
        # Broadcasting means and stds along spatial dimensions
        normalized = (image - self.means[:, None, None]) / self.stds[:, None, None]
        return normalized.astype(np.float32)

    def normalize_tensor(self, image: torch.Tensor) -> torch.Tensor:
        """
        Normalize a PyTorch tensor of shape (C, H, W) or (B, C, H, W).
        """
        device = image.device
        dtype = image.dtype
        means = torch.tensor(self.means, device=device, dtype=dtype)
        stds = torch.tensor(self.stds, device=device, dtype=dtype)
        
        if image.dim() == 3:
            # (C, H, W)
            return (image - means[:, None, None]) / stds[:, None, None]
        elif image.dim() == 4:
            # (B, C, H, W)
            return (image - means[None, :, None, None]) / stds[None, :, None, None]
        else:
            raise ValueError(f"Expected 3D or 4D tensor, got {image.dim()}D")
