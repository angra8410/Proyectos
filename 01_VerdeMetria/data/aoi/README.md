# Areas of Interest (AOI)

This directory contains GeoJSON files defining geographic areas of interest for NDVI analysis.

## Usage

AOI files can be used to:
- Filter satellite imagery downloads
- Clip rasters to specific regions
- Define study areas for change detection

## Format

AOI files should be valid GeoJSON with:
- CRS: WGS84 (EPSG:4326)
- Geometry type: Polygon or MultiPolygon
- Recommended: Include descriptive properties (name, description, date)

## Example

See `bogota.geojson` for a sample AOI.

## Creating Your Own AOI

1. Use [geojson.io](https://geojson.io) to draw polygons
2. Export as GeoJSON
3. Save in this directory
4. Reference in scripts: `--aoi data/aoi/your_aoi.geojson`
