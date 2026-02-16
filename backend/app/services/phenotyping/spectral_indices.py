
"""
Spectral Indices Service
Ported from ImagebreedPy (vegetative_index.py) for Bijmantra.

This service provides discrete functions to calculate vegetative indices
(NDVI, NDRE, TGI, VARI, CCC) from input image arrays.
"""

import numpy as np
import cv2
import logging
from typing import Optional, Tuple, Union

logger = logging.getLogger(__name__)

def _prepare_image(
    image_path: Optional[str] = None,
    channels: Optional[Tuple[np.ndarray, ...]] = None
) -> Tuple[Optional[np.ndarray], ...]:
    """
    Helper to prepare image channels from path or direct channel input.
    Returns a tuple of channels (e.g., b, g, r) or (nir, re, x).
    """
    if image_path:
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                logger.error(f"Could not read image at {image_path}")
                return (None, None, None)
            return cv2.split(img)
        except Exception as e:
            logger.error(f"Error reading image {image_path}: {e}")
            return (None, None, None)
    elif channels:
        return channels
    return (None, None, None)

def calculate_ccc(
    rgb_image_path: Optional[str] = None,
    r_image_path: Optional[str] = None,
    g_image_path: Optional[str] = None,
    b_image_path: Optional[str] = None,
    outfile_path: Optional[str] = None
) -> Optional[np.ndarray]:
    """
    Canopy Cover Crop (CCC) estimation using thresholding.
    """
    b, g, r = None, None, None

    if rgb_image_path:
        b, g, r = _prepare_image(image_path=rgb_image_path)
    elif r_image_path and g_image_path and b_image_path:
        r = cv2.imread(str(r_image_path), cv2.IMREAD_GRAYSCALE)
        g = cv2.imread(str(g_image_path), cv2.IMREAD_GRAYSCALE)
        b = cv2.imread(str(b_image_path), cv2.IMREAD_GRAYSCALE)

    if b is None or g is None or r is None:
        return None

    # Theta values from original implementation
    theta1 = 0.95
    theta2 = 0.95
    theta3 = 20

    # Avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        cond1 = (r / g) < theta1
        cond2 = (b / g) < theta2
        cond3 = (2 * g.astype(int) - r.astype(int) - b.astype(int)) > theta3

    mask = cond1 & cond2 & cond3

    # Create output image (255 for canopy, 0 for background)
    ccc_image = np.zeros_like(g, dtype=np.uint8)
    ccc_image[mask] = 255

    if outfile_path:
        cv2.imwrite(outfile_path, ccc_image)

    return ccc_image

def calculate_ndvi(
    nir_path: Optional[str] = None,
    red_path: Optional[str] = None,
    composite_path: Optional[str] = None,
    outfile_path: Optional[str] = None
) -> Optional[np.ndarray]:
    """
    Normalized Difference Vegetation Index (NDVI)
    NDVI = (NIR - Red) / (NIR + Red)
    """
    nir, red = None, None

    if composite_path:
        # Assuming composite is NIR-Red-Blue (standard for some drones)
        # But standard mapping varies. Assuming standard cv2 split (B,G,R) map to (Blue, Red, NIR)?
        # WARNING: Original code assumption was: nir, r, x = cv2.split(img)
        # This implies standard BGR load -> B=NIR, G=Red, R=X.
        # We will expose explicit paths for safety.
        channels = _prepare_image(image_path=composite_path)
        if channels[0] is not None:
             nir, red, _ = channels # Following original logic
    elif nir_path and red_path:
         nir = cv2.imread(str(nir_path), cv2.IMREAD_GRAYSCALE)
         red = cv2.imread(str(red_path), cv2.IMREAD_GRAYSCALE)

    if nir is None or red is None:
        return None

    nir = nir.astype(float)
    red = red.astype(float)

    with np.errstate(divide='ignore', invalid='ignore'):
        numerator = nir - red
        denominator = nir + red
        ndvi = np.divide(numerator, denominator)
        ndvi[np.isnan(ndvi)] = 0
        ndvi[np.isinf(ndvi)] = 0

    # Scale to 0-255 uint8 for visualization
    # Standard NDVI is -1 to 1. Mapping it to image:
    # (ndvi + 1) / 2 * 255

    # Original code simple multiplication: ndvi = ndvi * 255.
    # This implies raw ndvi (0 to 1 mostly for vegetation).
    # We will stick to original implementation for fidelity.
    ndvi_img = (ndvi * 255).astype(np.uint8)

    if outfile_path:
        cv2.imwrite(outfile_path, ndvi_img)

    return ndvi_img

def calculate_tgi(
    rgb_image_path: Optional[str] = None,
    outfile_path: Optional[str] = None
) -> Optional[np.ndarray]:
    """
    Triangular Greenness Index (TGI)
    TGI = G - 0.39*R - 0.61*B
    """
    b, g, r = None, None, None
    if rgb_image_path:
        b, g, r = _prepare_image(image_path=rgb_image_path)

    if b is None:
        return None

    g = g.astype(float)
    r = r.astype(float)
    b = b.astype(float)

    tgi = g - 0.39 * r - 0.61 * b

    # Normalize for display? Original code writes directly.
    # TGI can be negative. cv2.imwrite handles clipping/wrapping for uint8?
    # Ideally should normalize.
    # Original: cv2.imwrite(str(outfile_path), tgi)

    tgi_img = np.clip(tgi, 0, 255).astype(np.uint8)

    if outfile_path:
        cv2.imwrite(outfile_path, tgi_img)

    return tgi_img
