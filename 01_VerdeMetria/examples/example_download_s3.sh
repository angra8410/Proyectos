#!/bin/bash
# Example script to download Sentinel-2 data from AWS Public Dataset
#
# AWS hosts Sentinel-2 Level-2A data as Cloud-Optimized GeoTIFFs (COGs)
# No authentication required for public buckets
#
# Sentinel-2 on AWS: https://registry.opendata.aws/sentinel-2-l2a-cogs/

set -e

# Configuration
BUCKET="s3://sentinel-cogs"
# Example tile: T18NVJ (Colombia region)
TILE="T18NVJ"
# Example date: January 15, 2023
DATE="2023/1/S2A_18NVJ_20230115_0_L2A"
OUTPUT_DIR="../data/raw/example_s3"

# Bands to download
# B04 = Red (665nm)
# B08 = NIR (842nm)
BANDS=("B04" "B08")

echo "=== Sentinel-2 AWS Download Example ==="
echo "Tile: $TILE"
echo "Date: $DATE"
echo "Output: $OUTPUT_DIR"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check if AWS CLI or s3fs is available
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI not found. Install with:"
    echo "  conda install -c conda-forge awscli"
    echo "  or: pip install awscli"
    exit 1
fi

# Download each band
for BAND in "${BANDS[@]}"; do
    echo "Downloading band $BAND..."
    
    # Construct S3 path
    S3_PATH="${BUCKET}/${DATE}/${BAND}.tif"
    OUTPUT_FILE="${OUTPUT_DIR}/${BAND}.tif"
    
    # Download using AWS CLI (no credentials needed for public data)
    aws s3 cp "$S3_PATH" "$OUTPUT_FILE" --no-sign-request
    
    if [ $? -eq 0 ]; then
        echo "✓ Downloaded: $OUTPUT_FILE"
    else
        echo "✗ Failed to download: $S3_PATH"
    fi
done

echo ""
echo "=== Download Complete ==="
echo "Files saved to: $OUTPUT_DIR"
echo ""
echo "Next steps:"
echo "1. Verify files: gdalinfo $OUTPUT_DIR/B04.tif"
echo "2. Compute NDVI: python scripts/ndvi_compute.py --red $OUTPUT_DIR/B04.tif --nir $OUTPUT_DIR/B08.tif --out outputs/ndvi.tif"
echo ""
echo "Note: The paths above are examples. Adjust for your actual tile and date."
echo "Browse available data: https://sentinel-cogs.s3.us-west-2.amazonaws.com/index.html"
