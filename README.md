# SatyadarshI ◈

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://satyadarshi.streamlit.app/)

SatyadarshI is a space data infrastructure repository focused on the Space ecosystem, satellite remote sensing, and automated agricultural validation.

---

## 📌 Release Versions

| Version | Name | Stage | Core Architecture | Focus |
| :--- | :--- | :--- | :--- | :--- |
| **v1.0.0** | **SatyadarshI** | MVP | Batch Spatial Pipeline (DuckDB + Parquet + Rasterio) | Sentinel-2 NDVI Analytics & Spatial Profiling (Ahmedabad) |
| **v2.0.0** | **Fasals by SatyadarshI** | Beta | Dynamic API Ingestion & Calamity Analysis (Sentinel Hub CDSE) | Automated Crop Damage Claims Verification |

---

## 📁 Repository Structure

```text
space-data-pipeline/
├── README.md                  # Project documentation
└── learning/
    ├── project1/              # v1.0.0 - SatyadarshI: Batch NDVI Pipeline
    │   ├── data/              # GeoTIFF imagery & processed Parquet datasets
    │   ├── download.py        # CDSE Sentinel-2 downloader
    │   ├── flatten.py         # GeoTIFF raster band flattener (pixel -> coordinates)
    │   ├── ndvi.py            # NDVI calculation and classification
    │   ├── query.py           # DuckDB SQL analytical query client
    │   ├── dashboard.py       # Streamlit exploration dashboard
    │   └── requirements.txt   # Dependencies for v1
    │
    └── project2/              # v2.0.0 - Fasals by SatyadarshI: Claims Verification
        ├── data/              # Baseline datasets
        ├── sentinel_utils.py  # Spatial BBox mapping, CDSE querying & calamity simulation
        ├── dashboard.py       # Claims verdict & True Color comparison dashboard
        └── requirements.txt   # Dependencies for v2
```

---

## ⚙️ Global Configuration & API Setup

Both versions authenticate with the **Copernicus Data Space Ecosystem (CDSE)**. To retrieve live satellite imagery:

1. Register for a free account at [Copernicus Data Space Portal](https://dataspace.copernicus.eu/).
2. Create an OAuth Client in your dashboard to obtain your `Client ID` and `Client Secret`.
3. Set up a `.env` file in the subdirectory of the version you wish to run:

```env
SENTINEL_CLIENT_ID=your_oauth_client_id
SENTINEL_CLIENT_SECRET=your_oauth_client_secret
```

---

## 🚀 Get Started

### v1.0.0: SatyadarshI (Batch NDVI Pipeline)
An end-to-end satellite data processing pipeline over Ahmedabad, converting raw spatial imagery into fast-queryable Parquet columns.

#### 1. Setup & Installation
```bash
cd learning/project1
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Running the Pipeline
Run the steps in order to process the spatial data:
```bash
# Step 1: Download raw bands (Red, NIR, Blue) from CDSE
python download.py

# Step 2: Flatten pixel coordinates and export to Parquet
python flatten.py

# Step 3: Compute NDVI values and classify land cover
python ndvi.py

# Step 4: Run local DuckDB SQL query sample
python query.py

# Step 5: Spin up the interactive map dashboard
streamlit run dashboard.py
```
*Live Demo:* [satyadarshi.streamlit.app](https://satyadarshi.streamlit.app/)

---

### v2.0.0: Fasals by SatyadarshI (Claims Verification)
Satellite-based claims verification engine using Sentinel-2 L2A constellations to dynamically assess agricultural crop damage post-calamity (Floods, Droughts, Cyclones).

#### 1. Setup & Installation
```bash
cd learning/project2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Running the App
Run the interactive claims processing dashboard:
```bash
streamlit run dashboard.py
```
- **Dynamic Mode**: Enter coordinates and calamity dates to fetch real-time pre/post disaster imagery.
- **Simulated Mode**: If credentials are not specified, the system will run self-test verification simulations using historical Ahmedabad datasets.

---

## 🛠️ Stack & Dependencies
- **Data Ingestion**: Copernicus Data Space API, `sentinelhub` Python SDK
- **GIS / Spatial Math**: `rasterio` (GDAL-bindings), `numpy`, `pillow`
- **Data Analytics**: `duckdb` (SQL querying under 10ms), `pandas`
- **UI & Plotting**: `streamlit`, `matplotlib`

---

## 📜 License
Distributed under the MIT License. See [LICENSE](LICENSE) or the repository root for more information.