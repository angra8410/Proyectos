# VerdeMetria Architecture

## Overview

VerdeMetria is designed as a modular, scalable remote sensing data pipeline for NDVI computation and vegetation change detection.

## Technology Stack

### Core Components

- **Python 3.10**: Base language
- **Rasterio**: Low-level raster I/O and operations
- **RioXarray**: Higher-level xarray integration for multi-dimensional arrays
- **GeoPandas**: Vector data handling
- **NumPy**: Array computations

### Data Access

- **Sentinelsat**: Sentinel-2 data discovery and download
- **Boto3**: AWS S3 access for public datasets
- **s3fs**: S3 filesystem integration
- **stackstac**: Lazy loading of STAC items

### Optional Components

- **Apache Airflow**: Workflow orchestration (optional, see dags/)
- **MinIO**: Self-hosted S3-compatible object storage (optional, see docker/)
- **PostgreSQL/PostGIS**: Metadata storage (optional future addition)

## Data Flow

```
1. Data Acquisition
   ├─ Sentinelsat API → Download Sentinel-2 tiles
   ├─ AWS S3 → Stream COG tiles
   └─ Manual → Place in data/raw/

2. Preprocessing (scripts/)
   ├─ Band extraction (Red, NIR)
   ├─ Cloud masking (future)
   └─ Reprojection (if needed)

3. NDVI Computation (src/verdemetria/)
   ├─ compute_ndvi_array(): Core computation
   └─ Validation and QA

4. Change Detection
   ├─ Temporal differencing
   ├─ Area calculation
   └─ Statistics aggregation

5. Outputs
   ├─ GeoTIFF files (outputs/)
   ├─ Vector summaries (GeoJSON)
   └─ Reports (CSV/JSON)
```

## Module Structure

```
src/verdemetria/
├── __init__.py           # Package initialization
├── processing.py         # Core NDVI algorithms
└── io.py                 # I/O helpers

scripts/
├── ndvi_compute.py       # Standalone NDVI computation
├── ndvi_diff_area.py     # Temporal analysis
└── utils.py              # Shared utilities
```

## Execution Modes

### 1. Interactive (Notebooks)

For exploration and ad-hoc analysis:
```bash
jupyter lab
# Open notebooks/01-exploracion-ndvi.ipynb
```

### 2. Batch Processing (Scripts)

For production runs:
```bash
python scripts/ndvi_compute.py --red ... --nir ... --out ...
```

### 3. Automated Workflows (Airflow)

For scheduled, repeatable pipelines:
```bash
# Optional: Start Airflow
airflow standalone
# DAGs in dags/ directory
```

## Scalability Considerations

### Local Development

- Single-machine processing
- Files on local disk
- Suitable for small areas (< 100 km²)

### Production Deployment (Future)

- Distributed processing with Dask
- Cloud object storage (S3, MinIO)
- Airflow for orchestration
- PostgreSQL for metadata
- Docker containers for reproducibility

## Testing Strategy

- **Unit tests**: `tests/test_processing.py` - Core algorithms
- **Integration tests**: (Future) End-to-end workflows
- **CI/CD**: GitHub Actions runs tests on PRs

## Security and Credentials

- **No credentials in code**: Use environment variables
- **Sentinelsat**: `~/.config/sentinelsat/` or env vars
- **AWS**: `~/.aws/credentials` or IAM roles
- **GitHub Actions**: Repository secrets for CI

## Performance Optimization

- **Lazy loading**: Use rioxarray for large files
- **Chunked processing**: Process tiles in chunks
- **Compression**: LZW compression for outputs
- **COG format**: Use Cloud-Optimized GeoTIFFs

## Future Enhancements

1. **Cloud masking**: Integrate Sen2Cor or FMask
2. **Time series analysis**: Trend detection, anomaly detection
3. **Machine learning**: Vegetation classification
4. **API**: REST API for programmatic access
5. **Dashboard**: Web interface for visualization
6. **Multi-sensor**: Support for Landsat, MODIS

## Development Guidelines

See [README-DEV.md](../README-DEV.md) for:
- Coding standards
- Testing requirements
- PR workflow
- Branch policies
