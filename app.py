import streamlit as st
import pandas as pd
import folium
from folium.plugins import MeasureControl, Fullscreen
from streamlit_folium import st_folium
import plotly.express as px

st.set_page_config(page_title="Sindh Contamination & GI Cancer Dashboard", layout="wide")

st.title(" Geospatial Analysis & GI Cancer Risk Dashboard")
st.caption("Interactive visualization based on Sindh Water Contamination & Cancer Registry data.")

# 1. Load Data
@st.cache_data
def load_integrated_data():
    file_path = "Sindh_Water_Contamination_GI_Cancer_Synthetic_v1.0_FYP_Ready.xlsx"
    df = pd.read_excel(file_path, sheet_name="Integrated_Model_Data")
    return df
df = load_integrated_data()

# 2. Sidebar Filters
st.sidebar.header(" Geographic & Parameter Filters")
districts = ["All"] + sorted(df["District"].dropna().unique().tolist())
selected_district = st.sidebar.selectbox("Select District", districts)

if selected_district != "All":
    filtered_df = df[df["District"] == selected_district]
else:
    filtered_df = df

# Quick Metrics Top Row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Sampled Locations", len(filtered_df))
col2.metric("Avg Contamination Index", f"{filtered_df['Contamination_Index'].mean():.2f}")
col3.metric("Avg Cancer Incidence / 100k", f"{filtered_df['Incidence_Rate_per_100k'].mean():.2f}")
col4.metric("Avg Arsenic Level", f"{filtered_df['Arsenic_ug_L'].mean():.2f} µg/L")
st.markdown("---")

# 3. Interactive GIS Map Layer Construction
st.subheader(" Interactive GIS Layer Map")

# Center Map around Sindh
m = folium.Map(location=[25.8943, 68.5247], zoom_start=7, tiles="OpenStreetMap")
Fullscreen().add_to(m)
m.add_child(MeasureControl())

# Layer 1: Contamination Index Overlay
contamination_group = folium.FeatureGroup(name="Contamination Index Map", show=True)
for _, row in filtered_df.iterrows():
    val = row['Contamination_Index']
    # Color logic matching your GIS map palette
    color = "#d73027" if val > 0.75 else "#f46d43" if val > 0.27 else "#fdae61" if val > -0.13 else "#1a9850"
    
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=6,
        color=color,
        fill=True,
        fill_opacity=0.8,
        popup=f"<b>{row['District']} ({row['Taluka']})</b><br>"
              f"Contamination Index: {val:.2f}<br>"
              f"Cancer Incidence/100k: {row['Incidence_Rate_per_100k']:.2f}<br>"
              f"Cancer Risk Level: {row['Cancer_Risk_Level']}"
    ).add_to(contamination_group)

# Layer 2: Arsenic Hotspots
arsenic_group = folium.FeatureGroup(name="Arsenic Contamination Layer", show=False)
for _, row in filtered_df.iterrows():
    val = row['Arsenic_ug_L']
    color = "#800026" if val > 60 else "#e31a1c" if val > 47 else "#fd8d3c" if val > 36 else "#fecc5c"
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=5,
        color=color,
        fill=True,
        popup=f"<b>{row['Taluka']}</b><br>Arsenic: {val:.2f} µg/L"
    ).add_to(arsenic_group)

# Layer 3: Cancer Incidence Overlay
cancer_group = folium.FeatureGroup(name="GI Cancer Incidence Overlay", show=False)
for _, row in filtered_df.iterrows():
    rate = row['Incidence_Rate_per_100k']
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        icon=folium.DivIcon(html=f'<div style="font-size: 10pt; color: #800000; font-weight: bold;">{rate:.1f}</div>'),
        popup=f"{row['Taluka']}: {rate:.2f} per 100k cases"
    ).add_to(cancer_group)

# Add all layers to map
contamination_group.add_to(m)
arsenic_group.add_to(m)
cancer_group.add_to(m)

# Add Layer Switcher Control
folium.LayerControl(collapsed=False).add_to(m)

# Display Map in Streamlit
st_folium(m, width="100%", height=550)

# 4. Analytics Section (Plots)
st.markdown("---")
st.subheader(" Contaminant Correlation & Environmental Analysis")

c1, c2 = st.columns(2)

with c1:
    fig_scatter = px.scatter(
        filtered_df, 
        x="Contamination_Index", 
        y="Incidence_Rate_per_100k",
        color="Cancer_Risk_Level",
        hover_data=["District", "Taluka", "Arsenic_ug_L"],
        title="Contamination Index vs. Cancer Incidence Rate"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col2:  # Line 117
    if "Distance_to_Canal_km" in filtered_df.columns:
        fig_canal = px.scatter(
            filtered_df,
            x="Distance_to_Canal_km",
            y="Contamination_Index",
            color="Cancer_Risk_Level" if "Cancer_Risk_Level" in filtered_df.columns else None,
            hover_data=[col for col in ["District", "Taluka", "Arsenic_ug_L"] if col in filtered_df.columns],
            title="Distance to Canal (km) vs. Contamination Index"
        )
        st.plotly_chart(fig_canal, use_container_width=True)