# VerdeMetria

**Project ID:** 1FF90423-A5E2-4B91-9C41-8D7E6F2B3C10

## Purpose

VerdeMetria is a remote sensing data pipeline for computing Normalized Difference Vegetation Index (NDVI) from satellite imagery and detecting vegetation changes over time. The project provides tools for:

- Computing NDVI from red and NIR bands
- Calculating temporal NDVI differences
- Computing area statistics for vegetation change detection
- Automated workflows using Apache Airflow (optional)
- **Interactive Streamlit app** for visualizing results

## Streamlit App Deployment

### Option 1: Deploy to Streamlit Cloud

1. Go to [Streamlit Cloud](https://streamlit.io/cloud) and sign in with GitHub
2. Create a new app pointing to:
   - Repository: `angra8410/Proyectos`
   - Branch: `main`
   - Main file path: `01_VerdeMetria/app/streamlit_app.py`
3. Configure secrets (see [Secrets Configuration](#secrets-configuration) below)
4. Deploy!

### Option 2: Run Locally

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r 01_VerdeMetria/app/requirements.txt

# Run the app
streamlit run 01_VerdeMetria/app/streamlit_app.py
```

## Secrets Configuration

### Streamlit Cloud Secrets

In your Streamlit Cloud app settings, go to **Settings → Secrets** and add:

```toml
# OneDrive Public Link (if using public sharing)
ONEDRIVE_PUBLIC_LINK = "https://1drv.ms/your-public-link"

# OneDrive Graph API (if using authenticated access)
ONEDRIVE_SHARE_URL = "https://onedrive.live.com/your-share-url"
ONEDRIVE_TENANT_ID = "your-azure-tenant-id"
ONEDRIVE_CLIENT_ID = "your-azure-client-id"
ONEDRIVE_CLIENT_SECRET = "your-azure-client-secret"

# Optional: Specific file URLs
ONEDRIVE_CSV_URL = "https://1drv.ms/csv-file-link"
ONEDRIVE_GEOJSON_URL = "https://1drv.ms/geojson-file-link"
```

### GitHub Actions Secrets

For automated output generation, add these secrets in **Repository → Settings → Secrets and variables → Actions**:

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `ONEDRIVE_PUBLIC_LINK` | Public OneDrive share link | If using public sharing |
| `ONEDRIVE_SHARE_URL` | OneDrive share URL for Graph API | If using Graph API |
| `ONEDRIVE_TENANT_ID` | Azure AD Tenant ID | If using Graph API |
| `ONEDRIVE_CLIENT_ID` | Azure AD App Client ID | If using Graph API |
| `ONEDRIVE_CLIENT_SECRET` | Azure AD App Client Secret | If using Graph API |

> **Note:** `GITHUB_TOKEN` is automatically provided by GitHub Actions.

### Setting Up Azure AD App (for Graph API)

1. Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory
2. Navigate to **App registrations** → **New registration**
3. Register your app with a name (e.g., "VerdeMetria-OneDrive")
4. Note the **Application (client) ID** and **Directory (tenant) ID**
5. Go to **Certificates & secrets** → **New client secret**
6. Copy the secret value (shown only once!)
7. Go to **API permissions** → **Add permission** → **Microsoft Graph** → **Application permissions**
8. Add: `Files.Read.All` or `Sites.Read.All`
9. Click **Grant admin consent**

## Generated Outputs

The following files are automatically generated in `outputs/`:

| File | Description |
|------|-------------|
| `areas_by_sector_vs_2016.csv` | Raw area statistics by sector |
| `areas_by_sector_vs_2016_filtered.csv` | Filtered areas (≥1 ha) |
| `top10_by_year.csv` | Top 10 municipalities by year/kind |
| `areas_by_municipio_2025.geojson` | Municipality boundaries with data |
| `choropleth_cumulative_pct.html` | Interactive choropleth map |
| `top10_gain_*.png` | Bar chart for vegetation gain |
| `top10_loss_*.png` | Bar chart for vegetation loss |

## Testing Commands

### Test Generate Derived Outputs

```bash
# Activate environment
source .venv/bin/activate

# Run with test data
python 01_VerdeMetria/scripts/generate_derived.py --test

# Verify outputs
ls -la 01_VerdeMetria/outputs/
```

### Test OneDrive Download Helper

```bash
# Test URL conversion (no actual download)
python 01_VerdeMetria/scripts/download_from_onedrive.py \
  --url "https://1drv.ms/your-link" \
  --dest "/tmp/test.csv" \
  --test
```

### Test Streamlit App

```bash
# Run with mock secrets (set environment variables)
export ONEDRIVE_PUBLIC_LINK="your-link"
streamlit run 01_VerdeMetria/app/streamlit_app.py
```

## GitHub Actions Workflow

The `generate_and_commit_outputs.yml` workflow:

- **Triggers:** Push to main (scripts/data changes), weekly schedule, manual dispatch
- **Actions:** Downloads data from OneDrive (if configured), generates derived outputs, creates PR with changes
- **Manual Trigger:** Go to Actions → "Generate and Commit Outputs" → Run workflow

### Workflow Options

When manually triggering:
- `force_regenerate`: Force regeneration even without changes
- `create_pr`: Create PR (default) or direct commit

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
├── app/                  # Streamlit application
│   ├── streamlit_app.py  # Main app with OneDrive fallback
│   └── requirements.txt  # App dependencies
├── data/
│   ├── aoi/              # Area of Interest geometries
│   ├── ancillary/        # Supporting data (boundaries, etc.)
│   ├── raw/              # Raw satellite imagery (gitignored)
│   └── processed/        # Processed outputs (gitignored)
├── scripts/              # Standalone processing scripts
│   ├── download_from_onedrive.py  # OneDrive download helper
│   ├── generate_derived.py        # Output generation script
│   └── ...
├── src/verdemetria/      # Python package with core functions
├── notebooks/            # Jupyter notebooks for exploration
├── outputs/              # Analysis outputs (lightweight files committed)
├── tests/                # Unit tests
├── dags/                 # Airflow DAGs (optional)
├── docker/               # Docker configurations (optional)
└── docs/                 # Additional documentation
```

## Running Tests

```bash
pytest tests/
```

## Reverting Changes

If you need to revert the automated output generation:

```bash
# Revert to previous commit
git revert HEAD

# Or reset outputs directory
git checkout HEAD~1 -- 01_VerdeMetria/outputs/
```

## Development

See [README-DEV.md](README-DEV.md) for development guidelines.

## Contact

For questions or issues, please open an issue in the repository or contact the maintainer.

## License

MIT License - see [LICENSE](LICENSE) file for details.
