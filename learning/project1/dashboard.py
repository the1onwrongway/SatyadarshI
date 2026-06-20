import streamlit as st
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

st.set_page_config(page_title="Ahmedabad NDVI Dashboard", layout="wide")
st.title("Ahmedabad — Sentinel-2 NDVI Analysis (Nov 2024)")

PARQUET = "data/ahmedabad_nov2024.parquet"

# --- Load data once, cache it ---
# @st.cache_data tells Streamlit: run this function once, store the result
# On every rerender (slider move, button click) it returns cached data
# Without this, it re-reads the Parquet file on every interaction
@st.cache_data
def load_data():
    con = duckdb.connect()
    df = con.execute(f"SELECT * FROM read_parquet('{PARQUET}')").df()
    con.close()
    return df

df = load_data()

# --- Sidebar filters ---
st.sidebar.header("Filters")

land_cover_options = ["All"] + sorted(df["land_cover"].unique().tolist())
selected_cover = st.sidebar.selectbox("Land Cover Type", land_cover_options)

ndvi_range = st.sidebar.slider(
    "NDVI Range",
    min_value=float(df["ndvi"].min()),
    max_value=float(df["ndvi"].max()),
    value=(float(df["ndvi"].min()), float(df["ndvi"].max())),
    step=0.01
)

# --- Apply filters ---
filtered = df[
    (df["ndvi"] >= ndvi_range[0]) &
    (df["ndvi"] <= ndvi_range[1])
]
if selected_cover != "All":
    filtered = filtered[filtered["land_cover"] == selected_cover]

# --- Top metrics ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Pixels", f"{len(filtered):,}")
col2.metric("Avg NDVI", f"{filtered['ndvi'].mean():.4f}")
col3.metric("Max NDVI", f"{filtered['ndvi'].max():.4f}")
col4.metric("Min NDVI", f"{filtered['ndvi'].min():.4f}")

st.divider()

# --- Two column layout ---
left, right = st.columns(2)

# Left: NDVI spatial map
with left:
    st.subheader("NDVI Spatial Map")

    # Rebuild grid from filtered data
    # For pixels not in filter, fill with NaN so they show as white
    height = int(df["row"].max()) + 1
    width  = int(df["col"].max()) + 1
    grid   = np.full((height, width), np.nan)

    for _, pixel in filtered.iterrows():
        grid[int(pixel["row"]), int(pixel["col"])] = pixel["ndvi"]

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(grid, cmap="RdYlGn", vmin=-0.3, vmax=0.7)
    plt.colorbar(im, ax=ax, label="NDVI")
    ax.set_title(f"Filter: {selected_cover}")
    ax.axis("off")
    st.pyplot(fig)
    plt.close()

# Right: Land cover distribution
with right:
    st.subheader("Land Cover Distribution")

    cover_counts = filtered["land_cover"].value_counts().reset_index()
    cover_counts.columns = ["land_cover", "count"]
    cover_counts["pct"] = (cover_counts["count"] / len(filtered) * 100).round(2)

    fig2, ax2 = plt.subplots(figsize=(6, 5))
    colors = ["#2d6a4f", "#74c69d", "#d9ed92", "#f4a261", "#e76f51"]
    ax2.barh(cover_counts["land_cover"], cover_counts["pct"], color=colors[:len(cover_counts)])
    ax2.set_xlabel("Percentage of filtered pixels (%)")
    ax2.set_title("Distribution")
    for i, (val, label) in enumerate(zip(cover_counts["pct"], cover_counts["land_cover"])):
        ax2.text(val + 0.3, i, f"{val}%", va="center")
    st.pyplot(fig2)
    plt.close()

st.divider()

# --- West-East NDVI profile ---
st.subheader("West → East NDVI Profile (city center slice, lat 22.98–23.02)")

profile = filtered[
    (filtered["latitude"] >= 22.98) &
    (filtered["latitude"] <= 23.02)
].groupby(filtered["longitude"].round(3))["ndvi"].mean().reset_index()
profile.columns = ["longitude", "avg_ndvi"]

fig3, ax3 = plt.subplots(figsize=(12, 3))
ax3.plot(profile["longitude"], profile["avg_ndvi"], color="#2d6a4f", linewidth=1.5)
ax3.axhline(0, color="red", linewidth=0.8, linestyle="--", label="NDVI = 0")
ax3.fill_between(profile["longitude"], profile["avg_ndvi"], 0,
                  where=(profile["avg_ndvi"] > 0), alpha=0.2, color="green")
ax3.fill_between(profile["longitude"], profile["avg_ndvi"], 0,
                  where=(profile["avg_ndvi"] < 0), alpha=0.2, color="red")
ax3.set_xlabel("Longitude (West → East)")
ax3.set_ylabel("Avg NDVI")
ax3.set_title("Urban Gradient — NDVI drops in city core, recovers at outskirts")
ax3.legend()
st.pyplot(fig3)
plt.close()

# --- Raw data table ---
st.subheader("Raw Pixel Data (sample)")
st.dataframe(
    filtered[["latitude", "longitude", "red", "nir", "blue", "ndvi", "land_cover"]]
    .sample(min(500, len(filtered)))
    .sort_values("ndvi", ascending=False)
    .reset_index(drop=True),
    use_container_width=True
)