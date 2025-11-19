# VerdeMetria

**Project ID:** 1FF90423-A5E2-4B91-9C41-8D7E6F2B3C10

## Purpose

VerdeMetria is a remote sensing data pipeline for computing Normalized Difference Vegetation Index (NDVI) from satellite imagery and detecting vegetation changes over time. The project provides tools for:

- Computing NDVI from red and NIR bands
- Calculating temporal NDVI differences
- Computing area statistics for vegetation change detection
- Automated workflows using Apache Airflow (optional)

## Quick Start

### Prerequisites

- Miniconda or Mambaforge installed
- ~2GB disk space for environment

### Installation

1. Clone the repository:
```bash
git clone https://github.com/angra8410/Proyectos.git
cd Proyectos/01_VerdeMetria
```

2. Create and activate the conda environment:
```bash
conda env create -f environment.yml
conda activate ndvi
```

### Usage

#### Computing NDVI

```bash
python scripts/ndvi_compute.py \
  --red data/raw/red_band.tif \
  --nir data/raw/nir_band.tif \
  --out outputs/ndvi.tif
```

#### Computing NDVI Difference and Areas

```bash
python scripts/ndvi_diff_area.py \
  --ndvi1 outputs/ndvi_t1.tif \
  --ndvi2 outputs/ndvi_t2.tif \
  --out outputs/ndvi_diff.tif \
  --metric_epsg 3116
```

### Getting Sample Data

#### Option 1: AWS Public Sentinel-2 Dataset

Use the example script to download a sample tile:
```bash
bash examples/example_download_s3.sh
```

#### Option 2: Sentinelsat API

Configure your Copernicus credentials and use sentinelsat:
```bash
sentinelsat -u USERNAME -p PASSWORD -g data/aoi/bogota.geojson -s 20230101 -e 20230131 --download
```

#### Option 3: Manual Download

Download sample Sentinel-2 L2A data from:
- [Copernicus Open Access Hub](https://scihub.copernicus.eu/)
- [Google Earth Engine](https://earthengine.google.com/)

Place downloaded files in `data/raw/` (this folder is gitignored).

## Project Structure

```
01_VerdeMetria/
├── data/
│   ├── aoi/              # Area of Interest geometries
│   ├── raw/              # Raw satellite imagery (gitignored)
│   └── processed/        # Processed outputs (gitignored)
├── scripts/              # Standalone processing scripts
├── src/verdemetria/      # Python package with core functions
├── notebooks/            # Jupyter notebooks for exploration
├── outputs/              # Analysis outputs (gitignored)
├── tests/                # Unit tests
├── dags/                 # Airflow DAGs (optional)
├── docker/               # Docker configurations (optional)
└── docs/                 # Additional documentation
```

## Running Tests

```bash
pytest tests/
```

## Development

See [README-DEV.md](README-DEV.md) for development guidelines.

## Contact

For questions or issues, please open an issue in the repository or contact the maintainer.

## License

MIT License - see [LICENSE](LICENSE) file for details.
