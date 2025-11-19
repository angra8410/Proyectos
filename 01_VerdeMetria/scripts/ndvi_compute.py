#!/usr/bin/env python
"""
NDVI Computation Script

Computes Normalized Difference Vegetation Index (NDVI) from red and NIR bands.
Validates input shapes and transforms before computation.

Usage:
    python scripts/ndvi_compute.py --red data/raw/red.tif --nir data/raw/nir.tif --out outputs/ndvi.tif
"""

import argparse
import sys
import numpy as np
import rasterio
from rasterio.transform import Affine


def validate_bands(red_path, nir_path):
    """
    Validate that red and NIR bands have matching shapes and transforms.
    
    Args:
        red_path: Path to red band GeoTIFF
        nir_path: Path to NIR band GeoTIFF
        
    Returns:
        tuple: (red_array, nir_array, profile) if validation passes
        
    Raises:
        ValueError: If shapes or transforms don't match
    """
    with rasterio.open(red_path) as red_src, rasterio.open(nir_path) as nir_src:
        # Check shapes
        if red_src.shape != nir_src.shape:
            raise ValueError(
                f"Shape mismatch: Red {red_src.shape} != NIR {nir_src.shape}"
            )
        
        # Check transforms (allowing for small floating point differences)
        if not np.allclose(red_src.transform, nir_src.transform):
            raise ValueError(
                f"Transform mismatch:\nRed: {red_src.transform}\nNIR: {nir_src.transform}"
            )
        
        # Check CRS
        if red_src.crs != nir_src.crs:
            print(
                f"Warning: CRS mismatch (Red: {red_src.crs}, NIR: {nir_src.crs}). "
                "Using red band CRS.",
                file=sys.stderr
            )
        
        # Read data
        red = red_src.read(1).astype(np.float32)
        nir = nir_src.read(1).astype(np.float32)
        
        # Get profile for output
        profile = red_src.profile.copy()
        
    return red, nir, profile


def compute_ndvi(red, nir):
    """
    Compute NDVI from red and NIR arrays.
    
    NDVI = (NIR - Red) / (NIR + Red)
    
    Args:
        red: Red band array (wavelength ~665nm)
        nir: Near-infrared band array (wavelength ~842nm)
        
    Returns:
        NDVI array with values in range [-1, 1], NaN for invalid pixels
    """
    # Add small epsilon to avoid division by zero
    denominator = nir + red + 1e-8
    ndvi = (nir - red) / denominator
    
    # Set no-data values to NaN
    ndvi[np.isnan(red) | np.isnan(nir)] = np.nan
    ndvi[(red == 0) & (nir == 0)] = np.nan
    
    return ndvi


def save_ndvi(ndvi, profile, output_path):
    """
    Save NDVI array as GeoTIFF.
    
    Args:
        ndvi: NDVI array
        profile: Rasterio profile dict
        output_path: Output file path
    """
    # Update profile for single-band float32 output
    profile.update(
        dtype=rasterio.float32,
        count=1,
        compress='lzw',
        nodata=np.nan
    )
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(ndvi.astype(rasterio.float32), 1)
    
    print(f"NDVI saved to: {output_path}")
    
    # Print basic statistics
    valid_ndvi = ndvi[~np.isnan(ndvi)]
    if len(valid_ndvi) > 0:
        print(f"NDVI Statistics:")
        print(f"  Min:  {valid_ndvi.min():.4f}")
        print(f"  Max:  {valid_ndvi.max():.4f}")
        print(f"  Mean: {valid_ndvi.mean():.4f}")
        print(f"  Std:  {valid_ndvi.std():.4f}")


def main():
    parser = argparse.ArgumentParser(
        description="Compute NDVI from red and NIR bands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/ndvi_compute.py --red data/raw/B04.tif --nir data/raw/B08.tif --out outputs/ndvi.tif
  python scripts/ndvi_compute.py -r red.tif -n nir.tif -o ndvi.tif
        """
    )
    
    parser.add_argument(
        '--red', '-r',
        required=True,
        help='Path to red band GeoTIFF (e.g., Sentinel-2 B04)'
    )
    parser.add_argument(
        '--nir', '-n',
        required=True,
        help='Path to NIR band GeoTIFF (e.g., Sentinel-2 B08)'
    )
    parser.add_argument(
        '--out', '-o',
        required=True,
        help='Output path for NDVI GeoTIFF'
    )
    
    args = parser.parse_args()
    
    try:
        print(f"Reading bands...")
        print(f"  Red: {args.red}")
        print(f"  NIR: {args.nir}")
        
        red, nir, profile = validate_bands(args.red, args.nir)
        
        print(f"Computing NDVI...")
        ndvi = compute_ndvi(red, nir)
        
        print(f"Saving output...")
        save_ndvi(ndvi, profile, args.out)
        
        print("Done!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
