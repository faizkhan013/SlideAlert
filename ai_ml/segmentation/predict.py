import numpy as np
import torch
from .model import UNet

def predict_single_image(model, image_numpy, device="cpu"):
    """
    Runs model inference on a single 14-band image array.
    image_numpy: shape (128, 128, 14) or (14, 128, 128)
    """
    model.eval()
    
    # Reshape to channel-first if shape is (H, W, C)
    if image_numpy.shape[2] == 14:
        image_numpy = image_numpy.transpose((-1, 0, 1))
        
    # Add batch dimension and convert to float tensor
    image_tensor = torch.from_numpy(image_numpy).float().unsqueeze(0).to(device)
    
    with torch.no_grad():
        logits = model(image_tensor)
        probabilities = torch.sigmoid(logits).squeeze(0).squeeze(0).cpu().numpy()
        
    binary_mask = (probabilities >= 0.5).astype(np.uint8)
    
    # Calculate landslide pixel area percentage
    total_pixels = binary_mask.size
    landslide_pixels = np.sum(binary_mask == 1)
    landslide_area_percent = (landslide_pixels / total_pixels) * 100.0
    
    return {
        "probability_map": probabilities,
        "binary_mask": binary_mask,
        "landslide_area_percent": float(landslide_area_percent)
    }
