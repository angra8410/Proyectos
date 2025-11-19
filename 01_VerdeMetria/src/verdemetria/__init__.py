"""
VerdeMetria: NDVI computation and vegetation change detection

A Python package for processing satellite imagery and detecting vegetation changes
using NDVI (Normalized Difference Vegetation Index).
"""

__version__ = "0.1.0"

from .processing import compute_ndvi_array, diff_ndvi, mask_threshold
from .io import read_raster, write_raster, read_aoi

__all__ = [
    "compute_ndvi_array",
    "diff_ndvi",
    "mask_threshold",
    "read_raster",
    "write_raster",
    "read_aoi",
]
