"""
Core processing functions for NDVI computation and analysis.
"""

import numpy as np
from typing import Optional, Tuple


def compute_ndvi_array(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    Compute NDVI from red and NIR arrays.
    
    NDVI = (NIR - Red) / (NIR + Red)
    
    Args:
        red: Red band array (wavelength ~665nm)
        nir: Near-infrared band array (wavelength ~842nm)
        
    Returns:
        NDVI array with values in range [-1, 1], NaN for invalid pixels
        
    Raises:
        ValueError: If array shapes don't match
        
    Examples:
        >>> red = np.array([[100, 120], [110, 130]], dtype=np.float32)
        >>> nir = np.array([[150, 180], [160, 190]], dtype=np.float32)
        >>> ndvi = compute_ndvi_array(red, nir)
        >>> ndvi.shape
        (2, 2)
    """
    if red.shape != nir.shape:
        raise ValueError(
            f"Shape mismatch: red {red.shape} != nir {nir.shape}"
        )
    
    # Convert to float32 if needed
    red = red.astype(np.float32)
    nir = nir.astype(np.float32)
    
    # Add small epsilon to avoid division by zero
    denominator = nir + red + 1e-8
    ndvi = (nir - red) / denominator
    
    # Handle invalid values
    ndvi[np.isnan(red) | np.isnan(nir)] = np.nan
    ndvi[(red == 0) & (nir == 0)] = np.nan
    
    # Clip to valid NDVI range
    ndvi = np.clip(ndvi, -1.0, 1.0)
    
    return ndvi


def diff_ndvi(
    ndvi1: np.ndarray, 
    ndvi2: np.ndarray
) -> np.ndarray:
    """
    Compute temporal difference between two NDVI arrays.
    
    Difference = NDVI2 - NDVI1
    Positive values indicate vegetation increase.
    Negative values indicate vegetation decrease.
    
    Args:
        ndvi1: First NDVI array (earlier time)
        ndvi2: Second NDVI array (later time)
        
    Returns:
        Difference array
        
    Raises:
        ValueError: If array shapes don't match
        
    Examples:
        >>> ndvi1 = np.array([[0.3, 0.4], [0.5, 0.6]], dtype=np.float32)
        >>> ndvi2 = np.array([[0.4, 0.5], [0.3, 0.7]], dtype=np.float32)
        >>> diff = diff_ndvi(ndvi1, ndvi2)
        >>> diff[0, 0]  # Increase of 0.1
        0.1
    """
    if ndvi1.shape != ndvi2.shape:
        raise ValueError(
            f"Shape mismatch: ndvi1 {ndvi1.shape} != ndvi2 {ndvi2.shape}"
        )
    
    diff = ndvi2 - ndvi1
    
    # Preserve NaN values
    diff[np.isnan(ndvi1) | np.isnan(ndvi2)] = np.nan
    
    return diff


def mask_threshold(
    array: np.ndarray,
    threshold: float,
    comparison: str = 'greater'
) -> np.ndarray:
    """
    Create a boolean mask based on a threshold.
    
    Args:
        array: Input array
        threshold: Threshold value
        comparison: Comparison operator ('greater', 'less', 'equal', 'greater_equal', 'less_equal')
        
    Returns:
        Boolean mask array
        
    Raises:
        ValueError: If comparison operator is invalid
        
    Examples:
        >>> arr = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32)
        >>> mask = mask_threshold(arr, 0.25, 'greater')
        >>> mask
        array([[False, False],
               [ True,  True]])
    """
    valid = ~np.isnan(array)
    
    if comparison == 'greater':
        mask = (array > threshold) & valid
    elif comparison == 'less':
        mask = (array < threshold) & valid
    elif comparison == 'equal':
        mask = np.isclose(array, threshold) & valid
    elif comparison == 'greater_equal':
        mask = (array >= threshold) & valid
    elif comparison == 'less_equal':
        mask = (array <= threshold) & valid
    else:
        raise ValueError(
            f"Invalid comparison operator: {comparison}. "
            "Must be one of: greater, less, equal, greater_equal, less_equal"
        )
    
    return mask


def calculate_vegetation_metrics(
    ndvi: np.ndarray,
    thresholds: Optional[dict] = None
) -> dict:
    """
    Calculate basic vegetation metrics from NDVI array.
    
    Args:
        ndvi: NDVI array
        thresholds: Optional dict with classification thresholds
                   Default: {'bare': 0.2, 'sparse': 0.4, 'moderate': 0.6}
        
    Returns:
        Dictionary with metrics (mean, std, pixel counts per category)
        
    Examples:
        >>> ndvi = np.array([[0.1, 0.3], [0.5, 0.7]], dtype=np.float32)
        >>> metrics = calculate_vegetation_metrics(ndvi)
        >>> 'mean' in metrics
        True
    """
    if thresholds is None:
        thresholds = {
            'bare': 0.2,
            'sparse': 0.4,
            'moderate': 0.6
        }
    
    valid_ndvi = ndvi[~np.isnan(ndvi)]
    
    if len(valid_ndvi) == 0:
        return {
            'mean': np.nan,
            'std': np.nan,
            'min': np.nan,
            'max': np.nan,
            'bare_count': 0,
            'sparse_count': 0,
            'moderate_count': 0,
            'dense_count': 0
        }
    
    # Basic statistics
    metrics = {
        'mean': float(valid_ndvi.mean()),
        'std': float(valid_ndvi.std()),
        'min': float(valid_ndvi.min()),
        'max': float(valid_ndvi.max()),
    }
    
    # Classification counts
    valid_mask = ~np.isnan(ndvi)
    metrics['bare_count'] = int(np.sum((ndvi < thresholds['bare']) & valid_mask))
    metrics['sparse_count'] = int(np.sum(
        (ndvi >= thresholds['bare']) & 
        (ndvi < thresholds['sparse']) & 
        valid_mask
    ))
    metrics['moderate_count'] = int(np.sum(
        (ndvi >= thresholds['sparse']) & 
        (ndvi < thresholds['moderate']) & 
        valid_mask
    ))
    metrics['dense_count'] = int(np.sum((ndvi >= thresholds['moderate']) & valid_mask))
    
    return metrics
