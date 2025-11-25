#!/usr/bin/env python3
"""
Generate Derived Outputs for VerdeMetria

This script generates/optimizes derived outputs from raw data:
- Simplified GeoJSON files
- Filtered/aggregated CSV files  
- Choropleth HTML maps
- PNG visualizations

Usage:
    python generate_derived.py [--test]
    
    --test: Run with sample data for testing
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

import pandas as pd

# Optional imports - gracefully handle if not available
try:
    import geopandas as gpd
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False

try:
    from shapely.geometry import shape, mapping
    from shapely import simplify
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUTS_DIR = PROJECT_DIR / "outputs"
ANCILLARY_DIR = DATA_DIR / "ancillary"


def ensure_output_dir():
    """Create outputs directory if it doesn't exist."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {OUTPUTS_DIR}")


def simplify_geojson(input_path: Path, output_path: Path, tolerance: float = 0.001) -> bool:
    """
    Simplify a GeoJSON file to reduce file size.
    
    Args:
        input_path: Path to input GeoJSON
        output_path: Path to output simplified GeoJSON
        tolerance: Simplification tolerance (in degrees for WGS84)
        
    Returns:
        bool: True if successful
    """
    if not input_path.exists():
        logger.warning(f"Input file not found: {input_path}")
        return False
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        if HAS_SHAPELY:
            # Simplify geometries using Shapely
            for feature in geojson_data.get('features', []):
                if 'geometry' in feature and feature['geometry']:
                    geom = shape(feature['geometry'])
                    simplified = simplify(geom, tolerance, preserve_topology=True)
                    feature['geometry'] = mapping(simplified)
        
        # Write simplified output
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(geojson_data, f, ensure_ascii=False)
        
        original_size = input_path.stat().st_size / 1024
        new_size = output_path.stat().st_size / 1024
        logger.info(f"Simplified {input_path.name}: {original_size:.1f}KB -> {new_size:.1f}KB")
        return True
        
    except Exception as e:
        logger.error(f"Error simplifying GeoJSON: {e}")
        return False


def generate_filtered_csv(input_path: Path, output_path: Path, min_area_ha: float = 1.0) -> bool:
    """
    Generate filtered CSV with minimum area threshold.
    
    Args:
        input_path: Path to input CSV
        output_path: Path to output filtered CSV
        min_area_ha: Minimum area in hectares to include
        
    Returns:
        bool: True if successful
    """
    if not input_path.exists():
        logger.warning(f"Input file not found: {input_path}")
        return False
    
    try:
        df = pd.read_csv(input_path)
        
        # Determine area column
        area_col = None
        if 'area_ha' in df.columns:
            area_col = 'area_ha'
        elif 'area_m2' in df.columns:
            df['area_ha'] = df['area_m2'] / 10000.0
            area_col = 'area_ha'
        
        if area_col:
            original_count = len(df)
            df = df[df[area_col] >= min_area_ha]
            logger.info(f"Filtered {input_path.name}: {original_count} -> {len(df)} rows (min {min_area_ha} ha)")
        
        df.to_csv(output_path, index=False)
        return True
        
    except Exception as e:
        logger.error(f"Error generating filtered CSV: {e}")
        return False


def generate_top10_csv(input_path: Path, output_dir: Path, name_col: str = "NAME_2") -> bool:
    """
    Generate Top 10 CSV files by year and kind.
    
    Args:
        input_path: Path to input CSV with area data
        output_dir: Directory to save top10 files
        name_col: Column name for municipality/region name
        
    Returns:
        bool: True if successful
    """
    if not input_path.exists():
        logger.warning(f"Input file not found: {input_path}")
        return False
    
    try:
        df = pd.read_csv(input_path)
        
        # Ensure area_ha column exists
        if 'area_ha' not in df.columns and 'area_m2' in df.columns:
            df['area_ha'] = df['area_m2'] / 10000.0
        
        if 'year' not in df.columns or 'kind' not in df.columns:
            logger.warning("CSV missing required columns (year, kind)")
            return False
        
        # Generate top 10 for each year/kind combination
        top_all = []
        for year in df['year'].unique():
            for kind in df['kind'].unique():
                subset = df[(df['year'] == year) & (df['kind'] == kind)]
                top10 = subset.nlargest(10, 'area_ha')
                top10 = top10.copy()
                top10['rank'] = range(1, len(top10) + 1)
                top_all.append(top10)
        
        if top_all:
            combined = pd.concat(top_all, ignore_index=True)
            output_path = output_dir / "top10_by_year.csv"
            combined.to_csv(output_path, index=False)
            logger.info(f"Generated {output_path.name} with {len(combined)} rows")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error generating top10 CSV: {e}")
        return False


def generate_municipio_geojson(
    gpkg_path: Path,
    csv_path: Path,
    output_dir: Path,
    year: int = 2025,
    name_col: str = "NAME_2",
    simplify_tolerance: float = 0.001
) -> bool:
    """
    Generate GeoJSON with municipality boundaries and NDVI data.
    
    Args:
        gpkg_path: Path to GeoPackage with municipality geometries
        csv_path: Path to CSV with area statistics
        output_dir: Directory to save output
        year: Year to generate for
        name_col: Column name for municipality name
        simplify_tolerance: Geometry simplification tolerance
        
    Returns:
        bool: True if successful
    """
    if not HAS_GEOPANDAS:
        logger.warning("GeoPandas not available - skipping GeoJSON generation")
        return False
    
    if not gpkg_path.exists():
        logger.warning(f"GeoPackage not found: {gpkg_path}")
        return False
    
    try:
        # Read geometries
        gdf = gpd.read_file(gpkg_path)
        
        # Simplify geometries if shapely available
        if HAS_SHAPELY and simplify_tolerance > 0:
            gdf['geometry'] = gdf['geometry'].simplify(simplify_tolerance, preserve_topology=True)
        
        # Join with CSV data if available
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            if 'year' in df.columns:
                df = df[df['year'] == year]
            
            # Pivot to get gain/loss columns
            if 'kind' in df.columns and name_col in df.columns:
                pivot = df.pivot_table(
                    index=name_col,
                    columns='kind',
                    values='area_ha',
                    aggfunc='sum'
                ).reset_index()
                
                gdf = gdf.merge(pivot, on=name_col, how='left')
        
        # Save as GeoJSON
        output_path = output_dir / f"areas_by_municipio_{year}.geojson"
        gdf.to_file(output_path, driver='GeoJSON')
        
        size_kb = output_path.stat().st_size / 1024
        logger.info(f"Generated {output_path.name} ({size_kb:.1f} KB)")
        return True
        
    except Exception as e:
        logger.error(f"Error generating municipio GeoJSON: {e}")
        return False


def generate_choropleth_html(
    geojson_path: Path,
    output_dir: Path,
    value_col: str = "gain",
    name_col: str = "NAME_2"
) -> bool:
    """
    Generate an interactive choropleth HTML map using Folium.
    
    Args:
        geojson_path: Path to GeoJSON file
        output_dir: Directory to save output
        value_col: Column to use for choropleth values
        name_col: Column for feature names
        
    Returns:
        bool: True if successful
    """
    if not HAS_FOLIUM:
        logger.warning("Folium not available - skipping HTML map generation")
        return False
    
    if not geojson_path.exists():
        logger.warning(f"GeoJSON not found: {geojson_path}")
        return False
    
    try:
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        # Calculate center point
        coords = []
        for feature in geojson_data.get('features', []):
            if feature.get('geometry'):
                geom = feature['geometry']
                if geom['type'] == 'Polygon':
                    coords.extend(geom['coordinates'][0])
                elif geom['type'] == 'MultiPolygon':
                    for poly in geom['coordinates']:
                        coords.extend(poly[0])
        
        if coords:
            lats = [c[1] for c in coords]
            lons = [c[0] for c in coords]
            center = [sum(lats)/len(lats), sum(lons)/len(lons)]
        else:
            center = [11.0, -74.85]  # Default: Barranquilla area
        
        # Create map
        m = folium.Map(location=center, zoom_start=10, tiles='CartoDB positron')
        
        # Check which fields are available in the GeoJSON
        available_fields = set()
        for feature in geojson_data.get('features', []):
            available_fields.update(feature.get('properties', {}).keys())
        
        # Determine tooltip fields
        tooltip_fields = [name_col] if name_col in available_fields else []
        tooltip_aliases = ['Municipio'] if name_col in available_fields else []
        
        if value_col and value_col in available_fields:
            tooltip_fields.append(value_col)
            tooltip_aliases.append('Área (ha)')
        
        # Add GeoJSON layer
        geojson_layer_args = {
            'data': geojson_data,
            'name': 'Municipios',
            'style_function': lambda feat: {
                'fillColor': _get_color(feat.get('properties', {}).get(value_col, 0) if value_col else 0),
                'color': '#444',
                'weight': 0.5,
                'fillOpacity': 0.6
            }
        }
        
        if tooltip_fields:
            geojson_layer_args['tooltip'] = folium.GeoJsonTooltip(
                fields=tooltip_fields,
                aliases=tooltip_aliases
            )
        
        folium.GeoJson(**geojson_layer_args).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Save
        output_path = output_dir / "choropleth_cumulative_pct.html"
        m.save(str(output_path))
        
        size_kb = output_path.stat().st_size / 1024
        logger.info(f"Generated {output_path.name} ({size_kb:.1f} KB)")
        return True
        
    except Exception as e:
        logger.error(f"Error generating choropleth HTML: {e}")
        return False


def _get_color(value: float) -> str:
    """Get color for choropleth based on value."""
    if value is None or value == 0:
        return '#ffffff'
    elif value > 100:
        return '#1a9850'
    elif value > 50:
        return '#91cf60'
    elif value > 10:
        return '#d9ef8b'
    elif value > 0:
        return '#fee08b'
    else:
        return '#fc8d59'


def generate_bar_chart_png(
    csv_path: Path,
    output_dir: Path,
    year: int = None,
    kind: str = "gain",
    top_n: int = 10,
    name_col: str = "NAME_2"
) -> bool:
    """
    Generate bar chart PNG showing top municipalities.
    
    Args:
        csv_path: Path to CSV with area data
        output_dir: Directory to save output
        year: Year to filter (None for latest)
        kind: Type of change ('gain' or 'loss')
        top_n: Number of top items to show
        name_col: Column for municipality names
        
    Returns:
        bool: True if successful
    """
    if not HAS_MATPLOTLIB:
        logger.warning("Matplotlib not available - skipping PNG generation")
        return False
    
    if not csv_path.exists():
        logger.warning(f"CSV not found: {csv_path}")
        return False
    
    try:
        df = pd.read_csv(csv_path)
        
        # Ensure area_ha exists
        if 'area_ha' not in df.columns and 'area_m2' in df.columns:
            df['area_ha'] = df['area_m2'] / 10000.0
        
        # Filter by year if specified
        if year and 'year' in df.columns:
            df = df[df['year'] == year]
        elif 'year' in df.columns:
            year = df['year'].max()
            df = df[df['year'] == year]
        
        # Filter by kind
        if 'kind' in df.columns:
            df = df[df['kind'] == kind]
        
        # Get top N
        top = df.nlargest(top_n, 'area_ha')
        
        if top.empty:
            logger.warning("No data for bar chart")
            return False
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        colors = 'green' if kind == 'gain' else 'red'
        ax.barh(top[name_col].astype(str), top['area_ha'], color=colors)
        ax.invert_yaxis()
        ax.set_xlabel('Área (ha)')
        ax.set_title(f'Top {top_n} municipios - {kind.capitalize()} - {year}')
        
        plt.tight_layout()
        
        # Save
        output_path = output_dir / f"top{top_n}_{kind}_{year}.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        size_kb = output_path.stat().st_size / 1024
        logger.info(f"Generated {output_path.name} ({size_kb:.1f} KB)")
        return True
        
    except Exception as e:
        logger.error(f"Error generating bar chart PNG: {e}")
        return False


def generate_sample_data(output_dir: Path) -> bool:
    """
    Generate sample data for testing when no real data is available.
    
    Args:
        output_dir: Directory to save sample data
        
    Returns:
        bool: True if successful
    """
    logger.info("Generating sample data for testing...")
    
    # Sample municipalities
    municipios = [
        "Barranquilla", "Soledad", "Malambo", "Galapa", "Puerto Colombia",
        "Sabanalarga", "Baranoa", "Polonuevo", "Santo Tomás", "Palmar de Varela"
    ]
    
    # Sample data
    rows = []
    for year in [2020, 2021, 2022, 2023, 2024, 2025]:
        for kind in ['gain', 'loss']:
            for i, muni in enumerate(municipios):
                # Generate random-ish but consistent values
                base = (hash(muni + str(year) + kind) % 1000) / 10
                rows.append({
                    'NAME_2': muni,
                    'year': year,
                    'kind': kind,
                    'area_ha': base,
                    'area_m2': base * 10000
                })
    
    df = pd.DataFrame(rows)
    
    # Save CSV
    csv_path = output_dir / "areas_by_sector_vs_2016.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Generated sample CSV: {csv_path}")
    
    # Generate sample GeoJSON (simple polygons)
    if HAS_SHAPELY:
        features = []
        for i, muni in enumerate(municipios):
            # Simple square polygons offset by index
            lon = -74.85 + (i % 5) * 0.1
            lat = 11.0 + (i // 5) * 0.1
            coords = [
                [lon, lat],
                [lon + 0.08, lat],
                [lon + 0.08, lat + 0.08],
                [lon, lat + 0.08],
                [lon, lat]
            ]
            features.append({
                "type": "Feature",
                "properties": {"NAME_2": muni},
                "geometry": {"type": "Polygon", "coordinates": [coords]}
            })
        
        geojson = {"type": "FeatureCollection", "features": features}
        geojson_path = output_dir / "areas_by_municipio_2025.geojson"
        with open(geojson_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False)
        logger.info(f"Generated sample GeoJSON: {geojson_path}")
    
    return True


def main():
    """Main entry point for generate_derived script."""
    parser = argparse.ArgumentParser(description="Generate derived outputs for VerdeMetria")
    parser.add_argument("--test", action="store_true", help="Run with sample data for testing")
    parser.add_argument("--skip-geojson", action="store_true", help="Skip GeoJSON generation")
    parser.add_argument("--skip-html", action="store_true", help="Skip HTML map generation")
    parser.add_argument("--skip-png", action="store_true", help="Skip PNG generation")
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("VerdeMetria - Generate Derived Outputs")
    logger.info("=" * 60)
    
    # Report available libraries
    logger.info(f"GeoPandas available: {HAS_GEOPANDAS}")
    logger.info(f"Shapely available: {HAS_SHAPELY}")
    logger.info(f"Matplotlib available: {HAS_MATPLOTLIB}")
    logger.info(f"Folium available: {HAS_FOLIUM}")
    
    ensure_output_dir()
    
    # If test mode or no data exists, generate sample data
    csv_path = OUTPUTS_DIR / "areas_by_sector_vs_2016.csv"
    if args.test or not csv_path.exists():
        generate_sample_data(OUTPUTS_DIR)
    
    success_count = 0
    total_tasks = 0
    
    # 1. Generate filtered CSV
    total_tasks += 1
    if generate_filtered_csv(
        csv_path,
        OUTPUTS_DIR / "areas_by_sector_vs_2016_filtered.csv",
        min_area_ha=1.0
    ):
        success_count += 1
    
    # 2. Generate top 10 CSV
    total_tasks += 1
    if generate_top10_csv(csv_path, OUTPUTS_DIR):
        success_count += 1
    
    # 3. Generate/simplify GeoJSON
    if not args.skip_geojson:
        total_tasks += 1
        gpkg_path = ANCILLARY_DIR / "gadm41_COL.gpkg"
        if generate_municipio_geojson(
            gpkg_path,
            csv_path,
            OUTPUTS_DIR,
            year=2025
        ):
            success_count += 1
        else:
            # Try simplifying existing GeoJSON
            geojson_path = OUTPUTS_DIR / "areas_by_municipio_2025.geojson"
            if geojson_path.exists():
                if simplify_geojson(
                    geojson_path,
                    OUTPUTS_DIR / "areas_by_municipio_2025_simplified.geojson"
                ):
                    success_count += 1
    
    # 4. Generate choropleth HTML
    if not args.skip_html:
        total_tasks += 1
        geojson_path = OUTPUTS_DIR / "areas_by_municipio_2025.geojson"
        if generate_choropleth_html(geojson_path, OUTPUTS_DIR):
            success_count += 1
    
    # 5. Generate PNG charts
    if not args.skip_png:
        for kind in ['gain', 'loss']:
            total_tasks += 1
            if generate_bar_chart_png(csv_path, OUTPUTS_DIR, kind=kind):
                success_count += 1
    
    logger.info("=" * 60)
    logger.info(f"Completed: {success_count}/{total_tasks} tasks successful")
    logger.info(f"Output directory: {OUTPUTS_DIR}")
    
    # List generated files
    generated = list(OUTPUTS_DIR.glob("*"))
    generated = [f for f in generated if f.is_file() and not f.name.startswith('.')]
    logger.info(f"Generated files: {[f.name for f in generated]}")
    
    return 0 if success_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
