# SatyadarshI

Personal knowledge and project repository. Built in public.

## What this is
A long-term collection of projects at the intersection of satellite data, 
geospatial analytics, and ground data infrastructure; focused on the 
Indian space ecosystem.

## Current Projects

### learning/project1 — Sentinel-2 NDVI Pipeline (Jun 2026)
[Demo](https://satyadarshi.streamlit.app/) End-to-end satellite data pipeline over Ahmedabad using real Sentinel-2 data.

**Stack:** Python, Sentinel Hub API, Rasterio, NumPy, DuckDB, Streamlit

**What it does:**
- Downloads Sentinel-2 L2A imagery via Copernicus Data Space API
- Reads and inspects GeoTIFF bands with Rasterio
- Flattens 156,746 pixels into Parquet with real-world coordinates
- Calculates NDVI (vegetation index) from Red and NIR bands
- Queries results with DuckDB in under 10ms
- Displays interactive dashboard with spatial map and urban gradient chart

**Key finding:** Ahmedabad's urban NDVI gradient is clearly visible — 
vegetation on western outskirts (NDVI ~0.38), drops to urban core 
(NDVI ~0.10), recovers on eastern outskirts (NDVI ~0.43).

### learning/project2 — FASAL: Crop Damage Claims Verification System (Jun 2026)
Satellite-based claims verification engine using Sentinel-2 L2A constellations to assess agricultural crop damage post-calamity.

**Stack:** Python, Sentinel Hub CDSE API, NumPy, Pandas, Matplotlib, Streamlit, Pillow

**What it does:**
- Queries CDSE Sentinel Hub API for Sentinel-2 L2A imagery before and after reported calamity dates
- Automates cloud correction and mosaicking using Sentinel Hub least-cloud-cover filtering
- Computes pre- and post-calamity NDVI (Normalized Difference Vegetation Index) maps
- Conducts spatial spectral analysis, evaluating Near-Infrared (NIR) and Blue band shifts to distinguish between flooding/water-logging (NIR absorption), cyclone/wind damage, and drought stress
- Generates side-by-side True Color (RGB) imagery comparisons and NDVI difference heatmaps
- Outputs automated claims interpretation verdicts, damage severity distributions, and downloadable CSV verification records