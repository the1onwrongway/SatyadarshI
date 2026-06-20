import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# --- Load Parquet ---
parquet_path = "data/ahmedabad_nov2024.parquet"
df = pd.read_parquet(parquet_path)

print(f"Loaded {len(df)} pixels")

# --- Calculate NDVI ---
# Cast to float64 to avoid float32 precision issues during division
red = df["red"].values.astype(np.float64)
nir = df["nir"].values.astype(np.float64)

denominator = nir + red

# Guard against division by zero
# Where denominator is 0, set NDVI to 0 instead of NaN or inf
ndvi = np.where(
    denominator == 0,
    0.0,
    (nir - red) / denominator
)

df["ndvi"] = ndvi

print(f"\n--- NDVI Stats ---")
print(f"Min:  {ndvi.min():.4f}")
print(f"Max:  {ndvi.max():.4f}")
print(f"Mean: {ndvi.mean():.4f}")

# --- Classify pixels ---
def classify_ndvi(value):
    if value < 0:
        return "water"
    elif value < 0.2:
        return "urban_bare"
    elif value < 0.4:
        return "sparse_vegetation"
    elif value < 0.6:
        return "moderate_vegetation"
    else:
        return "dense_vegetation"

df["land_cover"] = df["ndvi"].apply(classify_ndvi)

print(f"\n--- Land Cover Distribution ---")
print(df["land_cover"].value_counts())
print(f"\nAs percentage:")
print((df["land_cover"].value_counts() / len(df) * 100).round(2))

# --- Save updated Parquet ---
df.to_parquet(parquet_path, index=False)
print(f"\nSaved NDVI + land_cover back to {parquet_path}")

# --- Visualize NDVI as heatmap ---
height = df["row"].max() + 1
width  = df["col"].max() + 1

ndvi_grid = ndvi.reshape(height, width)

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(
    ndvi_grid,
    cmap="RdYlGn",     # Red (low NDVI) → Yellow → Green (high NDVI)
    vmin=-0.3,
    vmax=0.7
)
plt.colorbar(im, ax=ax, label="NDVI")
ax.set_title("NDVI — Ahmedabad (Nov 2024)")
ax.set_xlabel("Column (West → East)")
ax.set_ylabel("Row (North → South)")

plt.tight_layout()
plt.savefig("data/ahmedabad_ndvi.png", dpi=150, bbox_inches="tight")
plt.show()
print("Saved: data/ahmedabad_ndvi.png")