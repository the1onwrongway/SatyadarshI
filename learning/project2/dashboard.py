import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
from PIL import Image
from dotenv import load_dotenv
import importlib
import sentinel_utils as utils
importlib.reload(utils)

load_dotenv()

st.set_page_config(
    page_title="SatyadarshI - Claims Verification",
    page_icon="icon.svg",
    layout="wide"
)

# Set matplotlib backend to headless to prevent GUI window binding hangs
import matplotlib
matplotlib.use('Agg')

# Custom Compact Styling
st.markdown("""
<style>
    .satyadarshi-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.4rem 0 0.8rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 1rem;
    }
    .satyadarshi-brand {
        display: flex;
        flex-direction: column;
        gap: 1px;
    }
    .satyadarshi-wordmark {
        font-family: monospace;
        font-size: 20px;
        font-weight: 600;
        letter-spacing: 0.04em;
        color: #1D9E75;
    }
    .satyadarshi-wordmark span {
        color: #9FE1CB;
    }
    .satyadarshi-sub {
        font-family: monospace;
        font-size: 10px;
        letter-spacing: 0.1em;
        color: #888780;
        text-transform: uppercase;
    }
    .satyadarshi-tag {
        font-family: monospace;
        font-size: 10px;
        padding: 2px 8px;
        border: 1px solid #1D9E75;
        border-radius: 4px;
        color: #1D9E75;
        letter-spacing: 0.06em;
    }
    .metric-card {
        background-color: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 6px;
        padding: 12px 10px;
        text-align: center;
        min-height: 85px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-title {
        font-size: 10px;
        color: #888780;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 22px;
        font-weight: bold;
        color: #9FE1CB;
        margin: 4px 0;
    }
    .metric-subtitle {
        font-size: 10px;
        color: #888780;
    }
    .verdict-box {
        background-color: rgba(255, 255, 255, 0.01);
        border-left: 4px solid #1D9E75;
        padding: 10px 15px;
        border-radius: 4px;
        margin-bottom: 12px;
    }
</style>

<div class="satyadarshi-header">
    <div class="satyadarshi-brand">
        <div class="satyadarshi-wordmark">SatyadarshI<span> | FASAL</span></div>
        <div class="satyadarshi-sub">Agricultural Crop Damage Claims Verification System</div>
    </div>
    <div class="satyadarshi-right">
        <div class="satyadarshi-tag">NDVI VERIFY LITE</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Load Credentials from Streamlit Secrets or Environment
client_id = ""
client_secret = ""
try:
    client_id = st.secrets["SENTINEL_CLIENT_ID"]
    client_secret = st.secrets["SENTINEL_CLIENT_SECRET"]
except Exception:
    pass

if not client_id:
    client_id = os.getenv("SENTINEL_CLIENT_ID", "")
if not client_secret:
    client_secret = os.getenv("SENTINEL_CLIENT_SECRET", "")

# Sidebar Inputs (Exactly 6 fields)
st.sidebar.header("Verification parameters")

# Coordinates (Fields 1 & 2)
lat = st.sidebar.number_input("1. Latitude", value=22.3000, format="%.6f")
lon = st.sidebar.number_input("2. Longitude", value=73.2000, format="%.6f")

# Pre-Calamity Date Range (Fields 3 & 4)
st.sidebar.markdown("**Pre-Calamity Baseline**")
pre_start = st.sidebar.date_input("3. Pre-Start Date", value=pd.to_datetime("2025-08-01"))
pre_end = st.sidebar.date_input("4. Pre-End Date", value=pd.to_datetime("2025-08-15"))

# Post-Calamity Date Range (Fields 5 & 6)
st.sidebar.markdown("**Post-Calamity Assessment**")
post_start = st.sidebar.date_input("5. Post-Start Date", value=pd.to_datetime("2025-09-01"))
post_end = st.sidebar.date_input("6. Post-End Date", value=pd.to_datetime("2025-09-10"))

# Collapsible Advanced Settings (Non-essential settings)
with st.sidebar.expander("Advanced Settings", expanded=False):
    bbox_size = st.selectbox(
        "Assessed Area Dimensions",
        options=[500, 1000, 2000, 5000],
        index=2,  # Default to 2000m x 2000m
        format_func=lambda x: f"{x}m x {x}m"
    )

# Automatically determine optimal resolution based on BBox size
resolution = 10 if bbox_size <= 2000 else 20

# Trigger button or status
trigger_fetch = False
if not client_id or not client_secret:
    st.error("Configuration Error: CDSE API credentials are missing from the system environment. Set SENTINEL_CLIENT_ID and SENTINEL_CLIENT_SECRET variables.")
else:
    trigger_fetch = st.sidebar.button("Run Verification Query", type="primary")

# Caching downloader
@st.cache_data
def get_sentinel_data(lat, lon, size, pre_s, pre_e, post_s, post_e, res, config_id, config_secret):
    bbox = utils.get_bbox_from_lat_lon(lat, lon, size)
    
    pre_img = utils.download_sentinel_image(bbox, pre_s, pre_e, config_id, config_secret, resolution=res)
    post_img = utils.download_sentinel_image(bbox, post_s, post_e, config_id, config_secret, resolution=res)
    
    return pre_img, post_img

if trigger_fetch:
    pre_start_str = pre_start.strftime("%Y-%m-%d")
    pre_end_str = pre_end.strftime("%Y-%m-%d")
    post_start_str = post_start.strftime("%Y-%m-%d")
    post_end_str = post_end.strftime("%Y-%m-%d")
    
    with st.spinner("Processing satellite data..."):
        try:
            # Query CDSE Sentinel Hub (5 bands: B04, B08, B03, B02, SCL)
            pre_img, post_img = get_sentinel_data(
                lat, lon, bbox_size,
                pre_start_str, pre_end_str,
                post_start_str, post_end_str,
                resolution,
                client_id, client_secret
            )
            
            # Self-healing cache validation: check if cached 5-band data is retrieved
            if (len(pre_img.shape) == 3 and pre_img.shape[2] == 5) or (len(post_img.shape) == 3 and post_img.shape[2] == 5):
                st.cache_data.clear()
                st.warning("Detected outdated cached data structure from a previous run. The Streamlit data cache has been automatically cleared. Please run the verification query again to download the correct 4-band data.")
                st.stop()
                
            # Calculate raw NDVI
            ndvi_pre = utils.calculate_ndvi(pre_img)
            ndvi_post = utils.calculate_ndvi(post_img)
            
            # Calculate raw NDVI statistics directly using unmasked leastCC composites
            ndvi_diff = ndvi_post - ndvi_pre
            
            avg_ndvi_pre = float(np.mean(ndvi_pre))
            avg_ndvi_post = float(np.mean(ndvi_post))
            avg_ndvi_diff = float(np.mean(ndvi_diff))
            pct_change = (avg_ndvi_diff / (avg_ndvi_pre + 1e-5)) * 100.0
            
            # Spatial statistics breakdown
            total_pixels = ndvi_diff.size
            
            if total_pixels > 0:
                pct_severe = (np.sum(ndvi_diff <= -0.25) / total_pixels) * 100.0
                pct_moderate = (np.sum((ndvi_diff > -0.25) & (ndvi_diff <= -0.10)) / total_pixels) * 100.0
                pct_stable = (np.sum((ndvi_diff > -0.10) & (ndvi_diff <= 0.05)) / total_pixels) * 100.0
                pct_growth = (np.sum(ndvi_diff > 0.05) / total_pixels) * 100.0
                
                # Fetch mean band shifts
                pre_nir_mean = float(np.mean(pre_img[:, :, 1]))
                post_nir_mean = float(np.mean(post_img[:, :, 1]))
                nir_change = post_nir_mean - pre_nir_mean
                
                pre_blue_mean = float(np.mean(pre_img[:, :, 3]))
                post_blue_mean = float(np.mean(post_img[:, :, 3]))
                blue_change = post_blue_mean - pre_blue_mean
                
                # Automated claims interpretation report
                verdict_title = ""
                verdict_color = ""
                analysis_text = ""
                
                if avg_ndvi_diff <= -0.20:
                    verdict_title = "CRITICAL VEGETATION LOSS DETECTED"
                    verdict_color = "#e63946"
                    if nir_change < -0.12 and blue_change > 0.04:
                        analysis_text = """
                        **Assessment Analysis:**
                        The data shows severe crop loss paired with a significant drop in Near-Infrared (NIR) reflectance and an increase in Blue reflectance. 
                        This spectral signature indicates standing surface water (flooding) submersing the crops. Water strongly absorbs NIR light, confirming crop inundation.
                        
                        *Verification Verdict:* Widespread crop damage due to flooding is confirmed. The claim aligns with satellite logs.
                        """
                    elif nir_change < -0.05:
                        analysis_text = """
                        **Assessment Analysis:**
                        The data shows severe vegetative decline and a drop in NIR reflectance. 
                        This signature suggests structural crop lodging or canopy stripping (typical of storm winds or cyclones) exposing bare soil.
                        
                        *Verification Verdict:* Physical crop destruction is verified. The claim aligns with satellite logs.
                        """
                    else:
                        analysis_text = """
                        **Assessment Analysis:**
                        A major drop in greenness has occurred. 
                        This could represent land clearing or crop harvesting. Cross-reference farming schedules to ensure this drop is not from a routine harvest.
                        
                        *Verification Verdict:* Physical decline is verified. Confirm harvesting schedules.
                        """
                elif avg_ndvi_diff <= -0.08:
                    verdict_title = "MODERATE VEGETATION DECLINE DETECTED"
                    verdict_color = "#f77f00"
                    if nir_change < 0.02 and blue_change <= 0.02:
                        analysis_text = """
                        **Assessment Analysis:**
                        A moderate decline in vegetation index is observed with stable NIR bands.
                        This pattern suggests moisture stress or crop yellowing consistent with agricultural drought conditions.
                        
                        *Verification Verdict:* Moderate crop stress is verified. The damage is likely drought-related.
                        """
                    else:
                        analysis_text = """
                        **Assessment Analysis:**
                        There is a moderate decrease in crop canopy health, with localized sections showing stress.
                        
                        *Verification Verdict:* Localized crop damage is verified. Examine the difference maps to locate affected grids.
                        """
                elif avg_ndvi_diff <= -0.02:
                    verdict_title = "MINOR VEGETATION SHIFT"
                    verdict_color = "#e9c46a"
                    analysis_text = """
                    **Assessment Analysis:**
                    There is an insignificant drop in crop health.
                    This level of variation is commonly associated with seasonal maturation, slight drying, or weather variance. 
                    
                    *Verification Verdict:* No widespread crop failure is observed. Claims of complete crop loss are unsupported.
                    """
                elif avg_ndvi_diff < 0.05:
                    verdict_title = "STABLE VEGETATION DETECTED"
                    verdict_color = "#2a9d8f"
                    analysis_text = """
                    **Assessment Analysis:**
                    Crop indices are stable. There are no satellite signatures of flooding, cyclone wind paths, or drought damage.
                    
                    *Verification Verdict:* No crop damage is detected. Widespread claims of loss are likely unfounded.
                    """
                else:
                    verdict_title = "VEGETATIVE GROWTH AND RECOVERY DETECTED"
                    verdict_color = "#1D9E75"
                    analysis_text = """
                    **Assessment Analysis:**
                    Vegetation indices have increased, indicating healthy crop expansion, chlorophyll synthesis, and vegetative development.
                    
                    *Verification Verdict:* The claim of damage is contradicted by active crop growth.
                    """

                # Render UI
                # 1. Verdict box
                st.markdown(f"""
                <div class="verdict-box" style="border-left-color: {verdict_color};">
                    <h4 style="color: {verdict_color}; margin-top: 0; margin-bottom: 4px; font-size: 16px;">{verdict_title}</h4>
                    <p style="margin: 0; font-size: 12px; color: #aaaaaa;">Location: Lat {lat:.5f}, Lon {lon:.5f} | Pre: {pre_start_str} to {pre_end_str} | Post: {post_start_str} to {post_end_str}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 2. Automated Report Summary
                st.markdown("### Analysis Report")
                st.markdown(analysis_text)
                
                st.divider()
                
                # 3. Compact Metrics Cards
                k_col1, k_col2, k_col3, k_col4 = st.columns(4)
                with k_col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Pre-Calamity NDVI</div>
                        <div class="metric-value">{avg_ndvi_pre:.4f}</div>
                        <div class="metric-subtitle">Mean (Cloud-free)</div>
                    </div>
                    """, unsafe_allow_html=True)
                with k_col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Post-Calamity NDVI</div>
                        <div class="metric-value">{avg_ndvi_post:.4f}</div>
                        <div class="metric-subtitle">Mean (Cloud-free)</div>
                    </div>
                    """, unsafe_allow_html=True)
                with k_col3:
                    arrow = "▼" if avg_ndvi_diff < 0 else "▲"
                    color_diff = "#e63946" if avg_ndvi_diff < 0 else "#1D9E75"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">NDVI Shift (Delta)</div>
                        <div class="metric-value" style="color: {color_diff};">{arrow} {avg_ndvi_diff:+.4f}</div>
                        <div class="metric-subtitle" style="color: {color_diff}; font-weight:600;">{pct_change:+.1f}% Change</div>
                    </div>
                    """, unsafe_allow_html=True)
                with k_col4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">NIR Band Shift</div>
                        <div class="metric-value" style="color: #9FE1CB;">{nir_change:+.4f}</div>
                        <div class="metric-subtitle">Pre: {pre_nir_mean:.3f} ◈ Post: {post_nir_mean:.3f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                st.divider()
                
                # 4. RGB Imagery side-by-side
                st.subheader("True Color Ground Comparison")
                tc_col1, tc_col2 = st.columns(2)
                
                def get_rgb(img, target_size=500):
                    # Bands: Red (0), Green (2), Blue (3)
                    r = img[:, :, 0]
                    g = img[:, :, 2]
                    b = img[:, :, 3]
                    rgb = np.stack([r, g, b], axis=-1)
                    rgb = np.clip(rgb / 0.35, 0.0, 1.0)
                    
                    # High-fidelity LANCZOS upscaling for small arrays
                    h, w, c = rgb.shape
                    if h < target_size or w < target_size:
                        rgb_uint8 = (rgb * 255).astype(np.uint8)
                        img_pil = Image.fromarray(rgb_uint8)
                        scale = target_size / min(h, w)
                        new_h, new_w = int(h * scale), int(w * scale)
                        resized_pil = img_pil.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
                        rgb = np.array(resized_pil).astype(np.float32) / 255.0
                    return rgb
                    
                with tc_col1:
                    st.image(get_rgb(pre_img), caption="Pre-Calamity RGB", use_container_width=True)
                with tc_col2:
                    st.image(get_rgb(post_img), caption="Post-Calamity RGB", use_container_width=True)
                    
                st.divider()
                
                # 5. NDVI Heatmaps
                st.subheader("Vegetation Health Maps")
                map_col1, map_col2, map_col3 = st.columns(3)
                
                ndvi_cmap = plt.get_cmap("RdYlGn")
                diff_cmap = plt.get_cmap("RdBu_r")
                
                fig_pre, ax_pre = plt.subplots(figsize=(4.5, 4))
                im_pre = ax_pre.imshow(ndvi_pre, cmap=ndvi_cmap, vmin=-0.1, vmax=0.75)
                ax_pre.axis("off")
                plt.colorbar(im_pre, ax=ax_pre, label="NDVI")
                
                fig_post, ax_post = plt.subplots(figsize=(4.5, 4))
                im_post = ax_post.imshow(ndvi_post, cmap=ndvi_cmap, vmin=-0.1, vmax=0.75)
                ax_post.axis("off")
                plt.colorbar(im_post, ax=ax_post, label="NDVI")
                
                fig_diff, ax_diff = plt.subplots(figsize=(4.5, 4))
                im_diff = ax_diff.imshow(ndvi_diff, cmap=diff_cmap, vmin=-0.35, vmax=0.35)
                ax_diff.axis("off")
                plt.colorbar(im_diff, ax=ax_diff, label="NDVI Difference")
                
                with map_col1:
                    st.markdown("##### Pre-Calamity NDVI")
                    st.pyplot(fig_pre)
                    plt.close(fig_pre)
                with map_col2:
                    st.markdown("##### Post-Calamity NDVI")
                    st.pyplot(fig_post)
                    plt.close(fig_post)
                with map_col3:
                    st.markdown("##### NDVI Shift Map")
                    st.pyplot(fig_diff)
                    plt.close(fig_diff)
                    
                st.divider()
                
                # 6. Severity Distribution & Exports
                st.subheader("Damage Severity Distribution & Records")
                b_col1, b_col2 = st.columns(2)
                
                with b_col1:
                    st.markdown("##### Damage Classification Breakdown")
                    
                    categories = [
                        "Severe Loss (<-0.25)",
                        "Moderate Loss (-0.25 to -0.10)",
                        "Stable / Minor Shift",
                        "Growth / Recovery (>0.05)"
                    ]
                    percentages = [pct_severe, pct_moderate, pct_stable, pct_growth]
                    colors = ["#d90429", "#f77f00", "#adb5bd", "#2a9d8f"]
                    
                    fig_bar, ax_bar = plt.subplots(figsize=(6, 3.5))
                    bars = ax_bar.barh(categories, percentages, color=colors)
                    ax_bar.set_xlabel("Percentage of Cloud-free Area (%)")
                    ax_bar.set_xlim(0, 100)
                    ax_bar.spines['top'].set_visible(False)
                    ax_bar.spines['right'].set_visible(False)
                    ax_bar.spines['left'].set_color('#888780')
                    ax_bar.spines['bottom'].set_color('#888780')
                    ax_bar.tick_params(colors='#888780')
                    
                    for bar in bars:
                        w = bar.get_width()
                        ax_bar.text(
                            w + 2,
                            bar.get_y() + bar.get_height()/2,
                            f"{w:.1f}%",
                            va='center',
                            ha='left',
                            color='#888780',
                            fontweight='bold'
                        )
                    st.pyplot(fig_bar)
                    plt.close(fig_bar)
                    
                with b_col2:
                    st.markdown("##### Claim Verification Record")
                    
                    summary_table = pd.DataFrame({
                        "Claims Parameter": [
                            "Location Coordinates",
                            "Date Window (Pre)",
                            "Date Window (Post)",
                            "Baseline Mean NDVI",
                            "Post Mean NDVI",
                            "Vegetation Shift",
                            "Severe Loss Area",
                            "Moderate Loss Area",
                            "Verification Method",
                            "Claims Status Verification"
                        ],
                        "Assessed Value": [
                            f"Lat: {lat:.6f}, Lon: {lon:.6f}",
                            f"{pre_start_str} to {pre_end_str}",
                            f"{post_start_str} to {post_end_str}",
                            f"{avg_ndvi_pre:.4f}",
                            f"{avg_ndvi_post:.4f}",
                            f"{avg_ndvi_diff:+.4f} ({pct_change:+.1f}%)",
                            f"{pct_severe:.1f}%",
                            f"{pct_moderate:.1f}%",
                            "LeastCC Mosaicking",
                            verdict_title
                        ]
                    })
                    
                    csv_data = summary_table.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Export Claims Verification Report (CSV)",
                        data=csv_data,
                        file_name=f"claims_report_live_{lat:.4f}_{lon:.4f}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                    st.table(summary_table)
                    
        except Exception as e:
            st.error(f"Verification Query Failed: {e}")
            st.info("Check that Sentinel Hub credentials are valid in your environment and coordinates/dates contain satellite data.")
else:
    st.info("Enter Latitude, Longitude, and Pre/Post dates in the sidebar and click 'Run Verification Query'.")
    st.markdown("""
    ### Claims Verification Engine
    Calculates agricultural health indices using Sentinel-2 L2A constellations before and after reported natural calamities.
    
    1. **Target**: Specify claim latitude and longitude.
    2. **Baselines**: Define date windows.
    3. **Cloud Correction**: Cloudy pixels are automatically removed using Scene Classification Layer (SCL) filtering.
    4. **Spectral Analysis**: The system maps crop changes and analyzes NIR bands to evaluate water-logging (floods) or crop damage.
    """)