import os
from dotenv import load_dotenv
from sentinelhub import (
    SHConfig,
    SentinelHubRequest,
    DataCollection,
    MimeType,
    BBox,
    CRS,
    bbox_to_dimensions,
)


load_dotenv()

config = SHConfig()
config.sh_client_id = os.getenv("SENTINEL_CLIENT_ID")
config.sh_client_secret = os.getenv("SENTINEL_CLIENT_SECRET")
config.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
config.sh_base_url = "https://sh.dataspace.copernicus.eu"


# Ahmedabad bounding box
# Format: (min_longitude, min_latitude, max_longitude, max_latitude)
ahmedabad_bbox = BBox(
    bbox=(72.45, 22.90, 72.70, 23.10),
    crs=CRS.WGS84
)

resolution = 60  # meters per pixel

image_size = bbox_to_dimensions(ahmedabad_bbox, resolution=resolution)
print(f"Image size: {image_size} pixels")


evalscript = """
//VERSION=3
function setup() {
    return {
        input: [{ bands: ["B04", "B08", "B02"], units: "REFLECTANCE" }],
        output: { bands: 3, sampleType: "FLOAT32" }
    };
}

function evaluatePixel(sample) {
    return [sample.B04, sample.B08, sample.B02];
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
            time_interval=("2025-11-01", "2025-11-30"),
            other_args={"dataFilter": {"mosaickingOrder": "leastCC"}}
        )
    ],
    responses=[
        SentinelHubRequest.output_response("default", MimeType.TIFF)
    ],
    bbox=ahmedabad_bbox,
    size=image_size,
    config=config,
    data_folder="data"
)

print("Sending request to Sentinel Hub...")
data = request.get_data(save_data=True)
print(f"Downloaded {len(data)} image(s)")
print(f"Image array shape: {data[0].shape}")