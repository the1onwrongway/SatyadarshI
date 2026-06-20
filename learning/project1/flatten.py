import os
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import xy

# --- Find the TIFF ---
data_dir = "data"
tiff_path = None

for root, dirs, files in os.walk(data_dir):
    for file in files:
        if file.endswith(".tiff") or file.endswith(".tif"):
            tiff_path = os.path.join(root, file)
            break

if not tiff_path:
    raise FileNotFoundError("No TIFF found. Run download.py first.")

print(f"Reading: {tiff_path}")

# --- Read bands ---
with rasterio.open(tiff_path) as src:
    image = src.read()          # shape: (3, 362, 433)
    transform = src.transform   # affine matrix — maps pixel → coordinates
    height = src.height
    width = src.width

red  = image[0]  # B04
nir  = image[1]  # B08
blue = image[2]  # B02

print(f"Image shape: {image.shape}")

# --- Build coordinate arrays ---
# We need a longitude and latitude value for every pixel
# rasterio.transform.xy() does this: given row,col → returns lon,lat

rows, cols = np.meshgrid(
    np.arange(height),
    np.arange(width),
    indexing="ij"
)
# rows and cols are now both (362, 433) arrays
# rows[i,j] = i, cols[i,j] = j — the pixel index of every position

longitudes, latitudes = xy(transform, rows.ravel(), cols.ravel())
# .ravel() flattens 2D → 1D so xy() can process all pixels at once
# returns two 1D arrays of length 156,746

print(f"Total pixels: {len(longitudes)}")

# --- Build DataFrame ---
df = pd.DataFrame({
    "row":       rows.ravel(),
    "col":       cols.ravel(),
    "longitude": longitudes,
    "latitude":  latitudes,
    "red":       red.ravel(),
    "nir":       nir.ravel(),
    "blue":      blue.ravel(),
    "date":      "2024-11-01",   # the time window we requested
})

print(f"\nDataFrame shape: {df.shape}")
print(df.head())
print(f"\nData types:\n{df.dtypes}")

# --- Save to Parquet ---
output_path = "data/ahmedabad_nov2024.parquet"
df.to_parquet(output_path, index=False)

size_mb = os.path.getsize(output_path) / (1024 * 1024)
print(f"\nSaved: {output_path}")
print(f"File size: {size_mb:.2f} MB")