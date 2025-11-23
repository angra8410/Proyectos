#!/usr/bin/env python3
"""
Aggregate annual NDVI TIFFs (already in metric CRS, e.g. EPSG:32618), compute
stats and differences vs baseline year, and produce CSV + trend plot.

Usage:
  conda activate ndvi
  python scripts/aggregate_ndvi_years.py --input-dir data/raw --out-dir outputs --baseline 2016 --veg_thr 0.3 --gain_thr 0.15 --loss_thr -0.15
"""
import argparse
import os
import re
import glob
import rasterio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def find_ndvi_files(input_dir):
    pattern = os.path.join(input_dir, 'ndvi_*.tif')
    files = sorted(glob.glob(pattern))
    # extract year from filename
    year_file = []
    for f in files:
        m = re.search(r'ndvi_(\d{4})', os.path.basename(f))
        if m:
            year_file.append((int(m.group(1)), f))
    year_file.sort()
    return year_file

def read_ndvi(path):
    with rasterio.open(path) as src:
        arr = src.read(1).astype('float32')
        meta = src.meta.copy()
    return arr, meta

def pixel_area_from_transform(transform):
    # transform.a is pixel width, transform.e is negative pixel height
    return abs(transform.a) * abs(transform.e)

def compute_metrics(arr, transform, veg_thr=0.3):
    valid = np.isfinite(arr)
    arr_valid = arr[valid]
    mean = float(np.nanmean(arr_valid)) if arr_valid.size>0 else np.nan
    std = float(np.nanstd(arr_valid)) if arr_valid.size>0 else np.nan
    pixel_area = pixel_area_from_transform(transform)
    veg_mask = (arr >= veg_thr) & valid
    veg_count = int(np.nansum(veg_mask))
    veg_area_m2 = veg_count * pixel_area
    return {'mean': mean, 'std': std, 'veg_count': veg_count, 'veg_area_m2': veg_area_m2}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input-dir', default='01_VerdeMetria/data/raw')
    p.add_argument('--out-dir', default='01_VerdeMetria/outputs')
    p.add_argument('--baseline', type=int, default=2016, help='baseline year for diffs')
    p.add_argument('--veg_thr', type=float, default=0.3)
    p.add_argument('--gain_thr', type=float, default=0.15)
    p.add_argument('--loss_thr', type=float, default=-0.15)
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    year_files = find_ndvi_files(args.input_dir)
    if not year_files:
        raise SystemExit(f"No NDVI files found in {args.input_dir} with pattern ndvi_YYYY.tif")

    records = []
    metas = {}
    arrays = {}
    for year, path in year_files:
        arr, meta = read_ndvi(path)
        metas[year] = meta
        arrays[year] = arr
        metrics = compute_metrics(arr, meta['transform'], veg_thr=args.veg_thr)
        metrics.update({'year': year, 'path': path})
        records.append(metrics)

    df = pd.DataFrame(records).sort_values('year')
    # convert m2 to ha
    df['veg_area_ha'] = df['veg_area_m2'] / 10000.0
    csv_out = os.path.join(args.out_dir, 'ndvi_yearly_metrics.csv')
    df.to_csv(csv_out, index=False)
    print("Saved yearly metrics to", csv_out)

    # compute diffs vs baseline
    if args.baseline not in arrays:
        print(f"Baseline {args.baseline} not found in input files. Skipping diffs.")
    else:
        base_arr = arrays[args.baseline]
        base_meta = metas[args.baseline]
        transform = base_meta['transform']
        pixel_area = pixel_area_from_transform(transform)
        diffs = []
        for year in sorted(arrays.keys()):
            if year == args.baseline:
                continue
            arr = arrays[year]
            if arr.shape != base_arr.shape:
                print(f"Warning: shape mismatch for {year}; skipping")
                continue
            diff = arr - base_arr
            gain_mask = (diff >= args.gain_thr) & np.isfinite(diff)
            loss_mask = (diff <= args.loss_thr) & np.isfinite(diff)
            gain_m2 = float(np.nansum(gain_mask)) * pixel_area
            loss_m2 = float(np.nansum(loss_mask)) * pixel_area
            diffs.append({'baseline': args.baseline, 'year': year,
                          'gain_m2': gain_m2, 'loss_m2': loss_m2,
                          'gain_ha': gain_m2/10000.0, 'loss_ha': loss_m2/10000.0})
        df_diff = pd.DataFrame(diffs)
        diff_csv = os.path.join(args.out_dir, f'ndvi_diffs_vs_{args.baseline}.csv')
        df_diff.to_csv(diff_csv, index=False)
        print("Saved diffs to", diff_csv)

    # plot trend of vegetated area
    plt.figure(figsize=(8,4))
    plt.plot(df['year'], df['veg_area_ha'], marker='o')
    plt.title('Área vegetal (ha) por año')
    plt.xlabel('Año')
    plt.ylabel('Área vegetal (ha)')
    plt.grid(True)
    plot_path = os.path.join(args.out_dir, 'ndvi_veg_area_trend.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print("Saved trend plot to", plot_path)

if __name__ == "__main__":
    main()