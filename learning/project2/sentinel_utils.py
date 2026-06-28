import os
import math
import numpy as np
import pandas as pd
from sentinelhub import (
    SHConfig,
    SentinelHubRequest,
    DataCollection,
    MimeType,
    BBox,
    CRS,
    bbox_to_dimensions,
)

def get_bbox_from_lat_lon(lat: float, lon: float, size_meters: float) -> BBox:
    """
    Computes a WGS84 Bounding Box centered at (lat, lon) with a width/height of size_meters.
    Uses a local spherical Earth approximation.
    """
    lat_rad = math.radians(lat)
    # Earth radius in meters
    R = 6378137.0
    
    # Calculate offset in radians
    half_size = size_meters / 2.0
    d_lat = half_size / R
    d_lon = half_size / (R * math.cos(lat_rad))
    
    # Convert to degrees
    delta_lat = math.degrees(d_lat)
    delta_lon = math.degrees(d_lon)
    
    return BBox(
        bbox=(lon - delta_lon, lat - delta_lat, lon + delta_lon, lat + delta_lat),
        crs=CRS.WGS84
    )

def download_sentinel_image(
    bbox: BBox,
    start_date: str,
    end_date: str,
    client_id: str,
    client_secret: str,
    resolution: float = 10.0
) -> np.ndarray:
    """
    Queries Sentinel Hub CDSE API for Sentinel-2 L2A imagery.
    Returns a numpy array of shape (height, width, 4) with Bands:
    [Red (B04), NIR (B08), Green (B03), Blue (B02)].
    """
    config = SHConfig()
    config.sh_client_id = client_id
    config.sh_client_secret = client_secret
    config.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    config.sh_base_url = "https://sh.dataspace.copernicus.eu"
    
    # Compute image shape in pixels based on desired resolution (meters/pixel)
    width, height = bbox_to_dimensions(bbox, resolution=resolution)
    
    # Evalscript selecting Red, NIR, Green, Blue (reflectance)
    evalscript = """
    //VERSION=3
    function setup() {
        return {
            input: [{ bands: ["B04", "B08", "B03", "B02"], units: "REFLECTANCE" }],
            output: { bands: 4, sampleType: "FLOAT32" }
        };
    }

    function evaluatePixel(sample) {
        return [sample.B04, sample.B08, sample.B03, sample.B02];
    }
    """
    
    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A.define_from(
                    "s2l2a",
                    service_url="https://sh.dataspace.copernicus.eu"
                ),
                time_interval=(start_date, end_date),
                other_args={"dataFilter": {"mosaickingOrder": "leastCC"}}
            )
        ],
        responses=[
            SentinelHubRequest.output_response("default", MimeType.TIFF)
        ],
        bbox=bbox,
        size=(width, height),
        config=config
    )
    
    # download data as in-memory list of numpy arrays
    data = request.get_data(save_data=False)
    if not data or len(data) == 0:
        raise ValueError(
            f"No satellite images found in the date range {start_date} to {end_date}. "
            "Please try widening the search window or checking for cloud cover."
        )
        
    img = data[0]
    
    # Standardize image layout to (height, width, bands)
    if len(img.shape) == 3:
        if img.shape[0] == 4:
            img = np.transpose(img, (1, 2, 0))
            
    return img

def calculate_ndvi(img: np.ndarray) -> np.ndarray:
    """
    Computes NDVI from Red (Band 0) and NIR (Band 1).
    NDVI = (NIR - Red) / (NIR + Red)
    """
    red = img[:, :, 0].astype(np.float64)
    nir = img[:, :, 1].astype(np.float64)
    
    denom = nir + red
    # Guard against division by zero or negative denominator
    ndvi = np.where(denom <= 0.0, 0.0, (nir - red) / denom)
    return np.clip(ndvi, -1.0, 1.0)

def get_mock_comparison_data(calamity_type: str):
    """
    Simulates a calamity effect (Flood, Drought, Cyclone) on the local Ahmedabad dataset.
    Returns pre_img, post_img of shape (height, width, 4) with Bands [Red, NIR, Green, Blue].
    """
    parquet_path = "data/ahmedabad_nov2025.parquet"
    if not os.path.exists(parquet_path):
        # Try parent directory / alternate path
        parquet_path = "learning/project2/data/ahmedabad_nov2025.parquet"
        if not os.path.exists(parquet_path):
            raise FileNotFoundError(
                f"Local Ahmedabad baseline data not found at {parquet_path}. "
                "Please check the data folder."
            )
            
    df = pd.read_parquet(parquet_path)
    
    height = int(df["row"].max()) + 1
    width = int(df["col"].max()) + 1
    
    pre_red = np.zeros((height, width))
    pre_nir = np.zeros((height, width))
    pre_blue = np.zeros((height, width))
    
    # Fast vectorized pixel reconstruction
    rows_idx = df["row"].values.astype(int)
    cols_idx = df["col"].values.astype(int)
    
    pre_red[rows_idx, cols_idx] = df["red"].values
    pre_nir[rows_idx, cols_idx] = df["nir"].values
    pre_blue[rows_idx, cols_idx] = df["blue"].values
    
    # Reconstruct/approximate a beautiful green channel
    # Vegetation reflects NIR strongly and Green moderately.
    # We blend Red, Blue, and NIR to produce a rich natural-looking green.
    pre_green = pre_red * 0.45 + pre_blue * 0.25 + pre_nir * 0.30
    
    pre_img = np.stack([pre_red, pre_nir, pre_green, pre_blue], axis=-1)
    
    # Create the post-calamity image
    post_img = pre_img.copy()
    
    np.random.seed(42)
    
    if calamity_type == "Flood":
        # Vectorized flooding simulation
        rows_grid, cols_grid = np.indices((height, width))
        dist_to_river = np.abs(cols_grid - rows_grid * 0.7 - 80)
        noise = np.random.rand(height, width)
        
        flood_mask = (dist_to_river < 35) | ((dist_to_river < 60) & (noise > 0.45)) | (noise > 0.96)
        
        # Apply water signatures
        post_img[flood_mask, 0] = 0.03  # Red drops
        post_img[flood_mask, 1] = 0.01  # NIR drops to ~0
        post_img[flood_mask, 2] = 0.07  # Green
        post_img[flood_mask, 3] = 0.16  # Blue increases
        
    elif calamity_type == "Drought":
        # Vectorized drought simulation (drying of crops)
        ndvi_val = calculate_ndvi(pre_img)
        veg_mask = ndvi_val > 0.15
        
        severity = 0.35 + 0.15 * np.random.rand(height, width)
        
        # Drying modifications
        post_img[veg_mask, 1] = pre_img[veg_mask, 1] * (1.0 - severity[veg_mask])
        post_img[veg_mask, 0] = pre_img[veg_mask, 0] * (1.0 + severity[veg_mask] * 0.5)
        post_img[veg_mask, 2] = pre_img[veg_mask, 2] * (1.0 + severity[veg_mask] * 0.1)
        
    elif calamity_type == "Cyclone / Storm Damage":
        # Vectorized storm wind swath simulation
        rows_grid, cols_grid = np.indices((height, width))
        dist_to_track = np.abs(cols_grid - (height - rows_grid) - 20)
        cyclone_mask = dist_to_track < 75
        
        severity = (1.0 - (dist_to_track / 75.0)) * 0.45
        
        # Flattened/damaged crop modifications
        post_img[cyclone_mask, 1] = pre_img[cyclone_mask, 1] * (1.0 - severity[cyclone_mask])
        post_img[cyclone_mask, 0] = pre_img[cyclone_mask, 0] * (1.0 + severity[cyclone_mask] * 0.35)
        post_img[cyclone_mask, 2] = pre_img[cyclone_mask, 2] * (1.0 - severity[cyclone_mask] * 0.15)
        
    return pre_img, post_img

if __name__ == "__main__":
    print("Testing coordinate bounding box math...")
    bbox = get_bbox_from_lat_lon(23.02, 72.57, 1000.0)
    print(f"Calculated BBox centered at (23.02, 72.57) with size 1000m:")
    print(f"Lower bounds: Lon={bbox.lower_left[0]:.6f}, Lat={bbox.lower_left[1]:.6f}")
    print(f"Upper bounds: Lon={bbox.upper_right[0]:.6f}, Lat={bbox.upper_right[1]:.6f}")
    
    print("\nTesting mock comparison generator...")
    try:
        pre, post = get_mock_comparison_data("Flood")
        print(f"Loaded successfully! Image shape: {pre.shape}")
        print(f"Pre-calamity Mean NIR: {pre[:,:,1].mean():.4f}")
        print(f"Post-calamity Mean NIR: {post[:,:,1].mean():.4f}")
        print("Self-test completed successfully!")
    except Exception as e:
        print(f"Self-test failed: {e}")
