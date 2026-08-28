import numpy as np

class DataValidator:
    """
    Validation checks for raw/preprocessed Landslide4Sense input data.
    """
    @staticmethod
    def validate_image_numpy(image: np.ndarray, expected_channels=14, expected_height=128, expected_width=128):
        """
        Validate shape, dtype, and quality of a numpy image.
        Returns (is_valid: bool, error_list: list).
        """
        shape = image.shape
        errors = []
        
        if len(shape) != 3:
            errors.append(f"Image must be 3-dimensional. Got shape: {shape}")
            return False, errors
            
        # Check channels and spatial dimensions (detect channel-first or channel-last)
        if shape[2] == expected_channels:
            # Channel-last (H, W, C)
            h, w, c = shape
        elif shape[0] == expected_channels:
            # Channel-first (C, H, W)
            c, h, w = shape
        else:
            errors.append(f"Expected {expected_channels} channels. Got shape: {shape}")
            return False, errors

        if h != expected_height or w != expected_width:
            errors.append(f"Expected spatial dimensions ({expected_height}, {expected_width}). Got: ({h}, {w})")
            
        if np.isnan(image).any():
            errors.append("Image contains NaN values.")
            
        if np.isinf(image).any():
            errors.append("Image contains infinite values.")
            
        return len(errors) == 0, errors

    @staticmethod
    def validate_mask_numpy(mask: np.ndarray, expected_height=128, expected_width=128):
        """
        Validate binary mask properties.
        """
        shape = mask.shape
        errors = []
        
        if len(shape) != 2:
            errors.append(f"Mask must be 2-dimensional. Got shape: {shape}")
            return False, errors
            
        h, w = shape
        if h != expected_height or w != expected_width:
            errors.append(f"Expected spatial dimensions ({expected_height}, {expected_width}). Got: ({h}, {w})")
            
        unique_vals = np.unique(mask)
        invalid_labels = [v for v in unique_vals if v not in (0, 1)]
        if invalid_labels:
            errors.append(f"Mask contains invalid labels. Only 0 (background) and 1 (landslide) allowed. Got: {unique_vals}")
            
        if np.isnan(mask).any():
            errors.append("Mask contains NaN values.")
            
        return len(errors) == 0, errors
