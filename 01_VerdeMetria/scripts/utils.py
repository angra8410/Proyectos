#!/usr/bin/env python
"""
Utility functions for raster and vector operations.

Provides helper functions for:
- Raster reprojection
- Raster I/O
- GeoJSON AOI reading
"""

import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.crs import CRS
import geopandas as gpd


def reproject_raster(src_raster, src_profile, dst_crs):
    """
    Reproject a raster to a different CRS.
    
    Args:
        src_raster: Source raster array
        src_profile: Source rasterio profile
        dst_crs: Destination CRS (rasterio.crs.CRS or EPSG code)
        
    Returns:
        tuple: (reprojected_array, updated_profile)
    """
    if isinstance(dst_crs, int):
        dst_crs = CRS.from_epsg(dst_crs)
    
    src_crs = src_profile['crs']
    
    if src_crs == dst_crs:
        return src_raster, src_profile
    
    # Calculate transform
    transform, width, height = calculate_default_transform(
        src_crs, dst_crs,
        src_profile['width'], src_profile['height'],
        *rasterio.transform.array_bounds(
            src_profile['height'], 
            src_profile['width'], 
            src_profile['transform']
        )
    )
    
    # Update profile
    dst_profile = src_profile.copy()
    dst_profile.update({
        'crs': dst_crs,
        'transform': transform,
        'width': width,
        'height': height
    })
    
    # Create destination array
    dst_raster = np.empty((height, width), dtype=src_raster.dtype)
    
    # Reproject
    reproject(
        source=src_raster,
        destination=dst_raster,
        src_transform=src_profile['transform'],
        src_crs=src_crs,
        dst_transform=transform,
        dst_crs=dst_crs,
        resampling=Resampling.bilinear,
        src_nodata=src_profile.get('nodata', np.nan),
        dst_nodata=dst_profile.get('nodata', np.nan)
    )
    
    return dst_raster, dst_profile


def save_raster(array, profile, output_path, compress='lzw'):
    """
    Save a raster array to a GeoTIFF file.
    
    Args:
        array: Raster array (2D numpy array)
        profile: Rasterio profile dict
        output_path: Output file path
        compress: Compression method (default: 'lzw')
    """
    profile = profile.copy()
    profile.update({
        'dtype': array.dtype,
        'count': 1,
        'compress': compress
    })
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(array, 1)


def read_geojson_aoi(geojson_path, target_crs=None):
    """
    Read a GeoJSON AOI file and optionally reproject.
    
    Args:
        geojson_path: Path to GeoJSON file
        target_crs: Optional target CRS to reproject to
        
    Returns:
        geopandas.GeoDataFrame
    """
    gdf = gpd.read_file(geojson_path)
    
    if target_crs is not None:
        if isinstance(target_crs, int):
            target_crs = f"EPSG:{target_crs}"
        gdf = gdf.to_crs(target_crs)
    
    return gdf


def clip_raster_to_aoi(raster_path, aoi_gdf, output_path=None):
    """
    Clip a raster to an AOI geometry.
    
    Args:
        raster_path: Path to input raster
        aoi_gdf: GeoDataFrame with AOI geometry
        output_path: Optional output path. If None, returns clipped array and profile.
        
    Returns:
        tuple: (clipped_array, updated_profile) if output_path is None
    """
    from rasterio.mask import mask
    
    with rasterio.open(raster_path) as src:
        # Reproject AOI to raster CRS if needed
        if aoi_gdf.crs != src.crs:
            aoi_gdf = aoi_gdf.to_crs(src.crs)
        
        # Clip
        clipped, transform = mask(src, aoi_gdf.geometry, crop=True)
        
        # Update profile
        profile = src.profile.copy()
        profile.update({
            'height': clipped.shape[1],
            'width': clipped.shape[2],
            'transform': transform
        })
        
        if output_path:
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(clipped)
            return None
        else:
            return clipped[0], profile


def calculate_pixel_area(profile):
    """
    Calculate the area of a pixel in square meters.
    
    Args:
        profile: Rasterio profile with transform
        
    Returns:
        float: Pixel area in square meters
    """
    transform = profile['transform']
    pixel_width = abs(transform[0])
    pixel_height = abs(transform[4])
    
    # For geographic coordinates, this is approximate
    # For projected coordinates in meters, this is accurate
    return pixel_width * pixel_height
