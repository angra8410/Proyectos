"""
I/O functions for reading and writing rasters and vector data.
"""

import numpy as np
import rasterio
from rasterio.crs import CRS
import geopandas as gpd
from typing import Optional, Tuple, Union


def read_raster(
    path: str,
    band: int = 1
) -> Tuple[np.ndarray, dict]:
    """
    Read a raster file and return array and profile.
    
    Args:
        path: Path to raster file
        band: Band number to read (default: 1)
        
    Returns:
        tuple: (array, profile_dict)
        
    Examples:
        >>> # array, profile = read_raster('data/raw/B04.tif')
        >>> # print(array.shape, profile['crs'])
        pass
    """
    with rasterio.open(path) as src:
        array = src.read(band).astype(np.float32)
        profile = src.profile.copy()
    
    return array, profile


def write_raster(
    array: np.ndarray,
    profile: dict,
    path: str,
    compress: str = 'lzw',
    nodata: Optional[float] = None
) -> None:
    """
    Write a raster array to a GeoTIFF file.
    
    Args:
        array: Raster array (2D numpy array)
        profile: Rasterio profile dict
        path: Output file path
        compress: Compression method (default: 'lzw')
        nodata: NoData value (default: None, uses np.nan for float types)
        
    Examples:
        >>> # array = np.array([[1, 2], [3, 4]], dtype=np.float32)
        >>> # profile = {'driver': 'GTiff', 'height': 2, 'width': 2, ...}
        >>> # write_raster(array, profile, 'output.tif')
        pass
    """
    profile = profile.copy()
    
    # Set nodata value
    if nodata is None and np.issubdtype(array.dtype, np.floating):
        nodata = np.nan
    
    profile.update({
        'dtype': array.dtype,
        'count': 1,
        'compress': compress,
        'nodata': nodata
    })
    
    with rasterio.open(path, 'w', **profile) as dst:
        dst.write(array, 1)


def read_aoi(
    path: str,
    target_crs: Optional[Union[int, str, CRS]] = None
) -> gpd.GeoDataFrame:
    """
    Read an Area of Interest (AOI) from a GeoJSON or other vector file.
    
    Args:
        path: Path to vector file (GeoJSON, Shapefile, etc.)
        target_crs: Optional target CRS to reproject to (EPSG code, WKT, or CRS object)
        
    Returns:
        GeoDataFrame with AOI geometries
        
    Examples:
        >>> # aoi = read_aoi('data/aoi/bogota.geojson', target_crs=4326)
        >>> # print(aoi.crs, aoi.geometry[0])
        pass
    """
    gdf = gpd.read_file(path)
    
    if target_crs is not None:
        if isinstance(target_crs, int):
            target_crs = CRS.from_epsg(target_crs)
        elif isinstance(target_crs, str):
            target_crs = CRS.from_string(target_crs)
        
        if gdf.crs != target_crs:
            gdf = gdf.to_crs(target_crs)
    
    return gdf


def clip_raster_by_aoi(
    raster_path: str,
    aoi: gpd.GeoDataFrame,
    output_path: Optional[str] = None
) -> Union[Tuple[np.ndarray, dict], None]:
    """
    Clip a raster to the extent of an AOI geometry.
    
    Args:
        raster_path: Path to input raster
        aoi: GeoDataFrame with AOI geometry
        output_path: Optional output path. If provided, saves to file.
        
    Returns:
        If output_path is None: tuple of (clipped_array, updated_profile)
        If output_path is provided: None (writes to file)
        
    Examples:
        >>> # aoi = read_aoi('data/aoi/bogota.geojson')
        >>> # clipped, profile = clip_raster_by_aoi('data/raw/B04.tif', aoi)
        >>> # print(clipped.shape)
        pass
    """
    from rasterio.mask import mask
    
    with rasterio.open(raster_path) as src:
        # Reproject AOI to match raster CRS if needed
        if aoi.crs != src.crs:
            aoi = aoi.to_crs(src.crs)
        
        # Clip the raster
        clipped, transform = mask(src, aoi.geometry, crop=True, filled=False)
        
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
            # Return first band if single band, otherwise return all
            if clipped.shape[0] == 1:
                return clipped[0], profile
            else:
                return clipped, profile


def get_raster_bounds(
    path: str,
    as_geometry: bool = False
) -> Union[Tuple[float, float, float, float], dict]:
    """
    Get the bounding box of a raster.
    
    Args:
        path: Path to raster file
        as_geometry: If True, returns as dict with geometry info
        
    Returns:
        Tuple of (minx, miny, maxx, maxy) or dict with geometry
        
    Examples:
        >>> # bounds = get_raster_bounds('data/raw/B04.tif')
        >>> # print(f"Extent: {bounds}")
        pass
    """
    with rasterio.open(path) as src:
        bounds = src.bounds
        
        if as_geometry:
            from shapely.geometry import box
            return {
                'bounds': bounds,
                'geometry': box(*bounds),
                'crs': src.crs
            }
        else:
            return bounds.left, bounds.bottom, bounds.right, bounds.top
