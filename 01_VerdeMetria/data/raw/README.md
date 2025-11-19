# Raw Data

Place downloaded satellite imagery here. This directory is gitignored to prevent committing large files.

## Expected Structure

```
raw/
├── sentinel2_L2A_20230115/
│   ├── B04.tif  (Red band)
│   ├── B08.tif  (NIR band)
│   └── metadata.xml
└── sentinel2_L2A_20230315/
    ├── B04.tif
    ├── B08.tif
    └── metadata.xml
```

## Download Instructions

See the main README.md for download options (sentinelsat, AWS S3, manual download).
