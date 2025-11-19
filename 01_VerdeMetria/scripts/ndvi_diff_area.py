#!/usr/bin/env python
"""
NDVI Difference and Area Calculation Script

Computes temporal difference between two NDVI rasters and calculates area statistics
for vegetation change detection.

Usage:
    python scripts/ndvi_diff_area.py --ndvi1 outputs/ndvi_t1.tif --ndvi2 outputs/ndvi_t2.tif --out outputs/diff.tif
    python scripts/ndvi_diff_area.py --ndvi1 ndvi_t1.tif --ndvi2 ndvi_t2.tif --out diff.tif --metric_epsg 3116
"""

import argparse
import sys
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling


def validate_ndvi_pair(ndvi1_path, ndvi2_path):
    """
    Validate that two NDVI rasters have matching properties.
    
    Args:
        ndvi1_path: Path to first NDVI GeoTIFF
        ndvi2_path: Path to second NDVI GeoTIFF
        
    Returns:
        tuple: (ndvi1_array, ndvi2_array, profile)
        
    Raises:
        ValueError: If shapes or transforms don't match
    """
    with rasterio.open(ndvi1_path) as src1, rasterio.open(ndvi2_path) as src2:
        # Check shapes
        if src1.shape != src2.shape:
            raise ValueError(
                f"Shape mismatch: NDVI1 {src1.shape} != NDVI2 {src2.shape}"
            )
        
        # Check transforms
        if not np.allclose(src1.transform, src2.transform):
            raise ValueError(
                f"Transform mismatch:\nNDVI1: {src1.transform}\nNDVI2: {src2.transform}"
            )
        
        # Check CRS
        if src1.crs != src2.crs:
            print(
                f"Warning: CRS mismatch (NDVI1: {src1.crs}, NDVI2: {src2.crs}). "
                "Using NDVI1 CRS.",
                file=sys.stderr
            )
        
        ndvi1 = src1.read(1).astype(np.float32)
        ndvi2 = src2.read(1).astype(np.float32)
        profile = src1.profile.copy()
        
    return ndvi1, ndvi2, profile


def compute_ndvi_diff(ndvi1, ndvi2):
    """
    Compute temporal difference: NDVI2 - NDVI1.
    
    Positive values indicate vegetation increase.
    Negative values indicate vegetation decrease.
    
    Args:
        ndvi1: First NDVI array (earlier time)
        ndvi2: Second NDVI array (later time)
        
    Returns:
        Difference array
    """
    diff = ndvi2 - ndvi1
    
    # Preserve NaN values
    diff[np.isnan(ndvi1) | np.isnan(ndvi2)] = np.nan
    
    return diff


def reproject_to_metric(raster, profile, target_epsg):
    """
    Reproject raster to a metric CRS for accurate area calculation.
    
    Args:
        raster: Input raster array
        profile: Rasterio profile
        target_epsg: Target EPSG code (e.g., 3116 for Colombia)
        
    Returns:
        tuple: (reprojected_array, updated_profile)
    """
    from rasterio.crs import CRS
    
    src_crs = profile['crs']
    dst_crs = CRS.from_epsg(target_epsg)
    
    if src_crs == dst_crs:
        print(f"Already in EPSG:{target_epsg}, skipping reprojection")
        return raster, profile
    
    print(f"Reprojecting from {src_crs} to EPSG:{target_epsg}...")
    
    # Calculate transform for destination
    transform, width, height = calculate_default_transform(
        src_crs, dst_crs, 
        profile['width'], profile['height'],
        *rasterio.transform.array_bounds(profile['height'], profile['width'], profile['transform'])
    )
    
    # Update profile
    new_profile = profile.copy()
    new_profile.update({
        'crs': dst_crs,
        'transform': transform,
        'width': width,
        'height': height
    })
    
    # Create destination array
    dst_array = np.empty((height, width), dtype=raster.dtype)
    
    # Reproject
    reproject(
        source=raster,
        destination=dst_array,
        src_transform=profile['transform'],
        src_crs=src_crs,
        dst_transform=transform,
        dst_crs=dst_crs,
        resampling=Resampling.bilinear,
        src_nodata=np.nan,
        dst_nodata=np.nan
    )
    
    return dst_array, new_profile


def calculate_area_stats(diff, profile, thresholds=None):
    """
    Calculate area statistics for NDVI difference.
    
    Args:
        diff: NDVI difference array
        profile: Rasterio profile (should be in metric CRS)
        thresholds: Optional dict with 'increase' and 'decrease' thresholds
        
    Returns:
        dict: Area statistics
    """
    if thresholds is None:
        thresholds = {'increase': 0.1, 'decrease': -0.1}
    
    # Calculate pixel area in square meters
    transform = profile['transform']
    pixel_width = abs(transform[0])  # meters
    pixel_height = abs(transform[4])  # meters
    pixel_area_m2 = pixel_width * pixel_height
    
    # Count pixels
    valid_pixels = ~np.isnan(diff)
    increase_pixels = (diff > thresholds['increase']) & valid_pixels
    decrease_pixels = (diff < thresholds['decrease']) & valid_pixels
    stable_pixels = (
        (diff >= thresholds['decrease']) & 
        (diff <= thresholds['increase']) & 
        valid_pixels
    )
    
    # Calculate areas
    stats = {
        'total_area_km2': np.sum(valid_pixels) * pixel_area_m2 / 1e6,
        'increase_area_km2': np.sum(increase_pixels) * pixel_area_m2 / 1e6,
        'decrease_area_km2': np.sum(decrease_pixels) * pixel_area_m2 / 1e6,
        'stable_area_km2': np.sum(stable_pixels) * pixel_area_m2 / 1e6,
        'increase_threshold': thresholds['increase'],
        'decrease_threshold': thresholds['decrease'],
        'pixel_area_m2': pixel_area_m2
    }
    
    return stats


def save_diff(diff, profile, output_path):
    """
    Save NDVI difference as GeoTIFF.
    
    Args:
        diff: Difference array
        profile: Rasterio profile
        output_path: Output file path
    """
    profile.update(
        dtype=rasterio.float32,
        count=1,
        compress='lzw',
        nodata=np.nan
    )
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(diff.astype(rasterio.float32), 1)
    
    print(f"NDVI difference saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Compute NDVI temporal difference and area statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (geographic coordinates)
  python scripts/ndvi_diff_area.py --ndvi1 ndvi_2023_01.tif --ndvi2 ndvi_2023_03.tif --out diff.tif
  
  # With metric reprojection for accurate areas (Colombia)
  python scripts/ndvi_diff_area.py --ndvi1 ndvi_t1.tif --ndvi2 ndvi_t2.tif --out diff.tif --metric_epsg 3116
  
  # Custom thresholds
  python scripts/ndvi_diff_area.py --ndvi1 ndvi_t1.tif --ndvi2 ndvi_t2.tif --out diff.tif --inc_thresh 0.15 --dec_thresh -0.15
        """
    )
    
    parser.add_argument(
        '--ndvi1',
        required=True,
        help='Path to first NDVI GeoTIFF (earlier time)'
    )
    parser.add_argument(
        '--ndvi2',
        required=True,
        help='Path to second NDVI GeoTIFF (later time)'
    )
    parser.add_argument(
        '--out', '-o',
        required=True,
        help='Output path for difference GeoTIFF'
    )
    parser.add_argument(
        '--metric_epsg',
        type=int,
        help='Optional: Reproject to metric EPSG code for accurate area calculation (e.g., 3116 for Colombia)'
    )
    parser.add_argument(
        '--inc_thresh',
        type=float,
        default=0.1,
        help='Threshold for vegetation increase (default: 0.1)'
    )
    parser.add_argument(
        '--dec_thresh',
        type=float,
        default=-0.1,
        help='Threshold for vegetation decrease (default: -0.1)'
    )
    
    args = parser.parse_args()
    
    try:
        print(f"Reading NDVI rasters...")
        print(f"  Time 1: {args.ndvi1}")
        print(f"  Time 2: {args.ndvi2}")
        
        ndvi1, ndvi2, profile = validate_ndvi_pair(args.ndvi1, args.ndvi2)
        
        print(f"Computing NDVI difference...")
        diff = compute_ndvi_diff(ndvi1, ndvi2)
        
        # Reproject if requested
        if args.metric_epsg:
            diff, profile = reproject_to_metric(diff, profile, args.metric_epsg)
        
        # Calculate area statistics
        print(f"\nCalculating area statistics...")
        thresholds = {
            'increase': args.inc_thresh,
            'decrease': args.dec_thresh
        }
        stats = calculate_area_stats(diff, profile, thresholds)
        
        print(f"\n=== Area Statistics ===")
        print(f"Total area:              {stats['total_area_km2']:.2f} km²")
        print(f"Vegetation increase:     {stats['increase_area_km2']:.2f} km² "
              f"({100 * stats['increase_area_km2'] / stats['total_area_km2']:.1f}%)")
        print(f"Vegetation decrease:     {stats['decrease_area_km2']:.2f} km² "
              f"({100 * stats['decrease_area_km2'] / stats['total_area_km2']:.1f}%)")
        print(f"Stable:                  {stats['stable_area_km2']:.2f} km² "
              f"({100 * stats['stable_area_km2'] / stats['total_area_km2']:.1f}%)")
        print(f"Pixel area:              {stats['pixel_area_m2']:.2f} m²")
        
        print(f"\nSaving output...")
        save_diff(diff, profile, args.out)
        
        print("Done!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
