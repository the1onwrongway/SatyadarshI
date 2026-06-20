import os
import numpy as np
import rasterio
import matplotlib.pyplot as plt

# Find the downloaded file
# Sentinel Hub saves into data/<hash>/response.tiff
data_dir = "data"
tiff_path = None

for root, dirs, files in os.walk(data_dir):
    for file in files:
        if file.endswith(".tiff") or file.endswith(".tif"):
            tiff_path = os.path.join(root, file)
            break

if not tiff_path:
    raise FileNotFoundError("No TIFF file found in data/. Run download.py first.")

print(f"Found file: {tiff_path}")

# Open with rasterio
with rasterio.open(tiff_path) as src:
    print(f"\n--- File Metadata ---")
    print(f"CRS: {src.crs}")
    print(f"Transform: {src.transform}")
    print(f"Width: {src.width} pixels")
    print(f"Height: {src.height} pixels")
    print(f"Number of bands: {src.count}")
    print(f"Data type: {src.dtypes}")
    print(f"Bounds: {src.bounds}")

    # Read all bands into numpy array
    # Shape will be (bands, height, width) — note: different from what download.py returned
    image = src.read()

print(f"\n--- Array Info ---")
print(f"Array shape: {image.shape}")
print(f"Min value: {image.min():.4f}")
print(f"Max value: {image.max():.4f}")
print(f"Mean value: {image.mean():.4f}")

# Split bands
red  = image[0]  # B04
nir  = image[1]  # B08
blue = image[2]  # B02

print(f"\n--- Per Band Stats ---")
for name, band in zip(["Red (B04)", "NIR (B08)", "Blue (B02)"], [red, nir, blue]):
    print(f"{name}: min={band.min():.4f}, max={band.max():.4f}, mean={band.mean():.4f}")

# Quick visual — stretch values to 0-255 for display
def normalize(band):
    band = np.clip(band, 0, 1)
    return (band * 255).astype(np.uint8)

rgb = np.stack([normalize(red), normalize(blue), normalize(blue)], axis=-1)

plt.figure(figsize=(8, 6))
plt.imshow(rgb)
plt.title("Ahmedabad — Sentinel-2 (Nov 2024)")
plt.axis("off")
plt.savefig("data/ahmedabad_preview.png", dpi=150, bbox_inches="tight")
plt.show()
print("\nSaved preview to data/ahmedabad_preview.png")