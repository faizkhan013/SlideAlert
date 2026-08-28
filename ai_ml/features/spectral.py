"""
Feature extraction for spectral index metrics (NDVI, NDWI).
"""

def compute_ndvi(red_band, nir_band, epsilon=1e-8):
    """
    Computes Normalized Difference Vegetation Index.
    """
    return (nir_band - red_band) / (nir_band + red_band + epsilon)

def compute_ndwi(green_band, nir_band, epsilon=1e-8):
    """
    Computes Normalized Difference Water Index.
    """
    return (green_band - nir_band) / (green_band + nir_band + epsilon)
