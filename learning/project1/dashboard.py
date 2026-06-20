import streamlit as st
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

st.set_page_config(
    page_title="SatyadarshI — NDVI Pipeline",
    page_icon="icon.svg",
    layout="wide"
)
# Branded header — replace st.title() with this
st.markdown("""
<style>
    .satyadarshi-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0 1.5rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 1.5rem;
    }
    .satyadarshi-brand {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .satyadarshi-wordmark {
        font-family: monospace;
        font-size: 22px;
        font-weight: 600;
        letter-spacing: 0.04em;
        color: #1D9E75;
    }
    .satyadarshi-wordmark span {
        color: #9FE1CB;
    }
    .satyadarshi-sub {
        font-family: monospace;
        font-size: 11px;
        letter-spacing: 0.12em;
        color: #888780;
        text-transform: uppercase;
    }
    .satyadarshi-right {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .satyadarshi-tag {
        font-family: monospace;
        font-size: 11px;
        padding: 4px 10px;
        border: 1px solid #1D9E75;
        border-radius: 4px;
        color: #1D9E75;
        letter-spacing: 0.06em;
    }
    .satyadarshi-gh {
        font-family: monospace;
        font-size: 12px;
        color: #888780;
        text-decoration: none;
        display: flex;
        align-items: center;
        gap: 6px;
        transition: color 0.2s;
    }
    .satyadarshi-gh:hover { color: #1D9E75; }
    .satyadarshi-gh svg { width: 16px; height: 16px; fill: currentColor; }
</style>

<div class="satyadarshi-header">
    <div class="satyadarshi-brand">
        <div class="satyadarshi-wordmark">SatyadarshI<span> ◈</span></div>
        <div class="satyadarshi-sub">Sentinel-2 · Ahmedabad · Nov 2025</div>
    </div>
    <div class="satyadarshi-right">
        <div class="satyadarshi-tag">NDVI PIPELINE v0.1</div>
        <a class="satyadarshi-gh" href="https://github.com/the1onwrongway/SatyadarshI" target="_blank">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            the1onwrongway/SatyadarshI
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

PARQUET = "learning/project1/data/ahmedabad_nov2025.parquet"

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
    use_container_width=True,
    hide_index=True
)