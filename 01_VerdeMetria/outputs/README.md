# Outputs Directory

Analysis outputs and final results are saved here.

This directory is gitignored to prevent committing large files.

## Expected Contents

- NDVI GeoTIFFs
- Difference rasters
- Statistics CSVs
- Visualization outputs (PNG, PDF)
- Reports (JSON, HTML)

## Usage

All scripts save outputs to this directory by default:
```bash
python scripts/ndvi_compute.py --red data/raw/B04.tif --nir data/raw/B08.tif --out outputs/ndvi.tif
```
