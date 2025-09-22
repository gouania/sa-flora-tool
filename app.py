# app.py

import streamlit as st
import folium
from streamlit_folium import st_folium
import main
import config

# --- Page Configuration ---
st.set_page_config(
    page_title="SA Flora ID Assistant",
    page_icon="🌿",
    layout="wide"
)

# --- App Title and Description ---
st.title("🌿 Botanical Identification Assistant")
st.markdown("An AI-powered tool for identifying plants of the Southern African flora.")

# --- Session State Initialization ---
if "center" not in st.session_state:
    st.session_state.center = [-29.0, 24.0]
if "location" not in st.session_state:
    st.session_state.location = [config.DEFAULT_LATITUDE, config.DEFAULT_LONGITUDE]

# --- Layout Configuration ---
map_col, input_col = st.columns([0.6, 0.4])

with map_col:
    st.subheader("1. Select Location on Map")
    m = folium.Map(location=st.session_state.center, zoom_start=5)
    folium.Marker(
        st.session_state.location,
        popup="Selected Location",
        tooltip="Selected Location"
    ).add_to(m)
    map_data = st_folium(m, width=700, height=500)
    if map_data and map_data["last_clicked"]:
        st.session_state.location = [
            map_data["last_clicked"]["lat"],
            map_data["last_clicked"]["lng"],
        ]

with input_col:
    # --- Input Form ---
    with st.form(key='specimen_form'):
        st.subheader("2. Describe the Specimen")

        latitude = st.number_input(
            "Latitude",
            value=st.session_state.location[0],
            format="%.6f"
        )
        longitude = st.number_input(
            "Longitude",
            value=st.session_state.location[1],
            format="%.6f"
        )
        
        # --- NEW WIDGET FOR SEARCH RADIUS ---
        radius_km = st.number_input(
            "Search Radius (km)",
            min_value=1,
            max_value=100, # Set a reasonable max to prevent very long queries
            value=config.DEFAULT_RADIUS_KM,
            step=1,
            help="The radius around the selected point to search for species records on GBIF."
        )
        
        taxon_name = st.text_input("Taxon", value=config.DEFAULT_TAXON_NAME)

        user_input = st.text_area(
            "Morphological Description & Locality Details",
            height=150,
            value="flowers in clusters of 6-10; leaves alternate, shorter than flowers. Flowers red outside, lobes cream inside, petaloid scales present.",
            help="Provide as much detail as possible (habit, leaves, flowers, fruits, etc.), and any habitat and elevational info."
        )

        submit_button = st.form_submit_button(label='Analyze Specimen')

# --- Analysis Execution ---
if submit_button:
    with input_col:
        st.subheader("3. Analysis Results")
        with st.spinner('Querying GBIF, scraping descriptions, and analyzing with Gemini... Please wait.'):
            # --- UPDATED FUNCTION CALL ---
            # The radius_km variable from the new widget is now passed to the function.
            analysis_result, raw_data = main.run_identification_process(
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km, # Pass the user-defined radius here
                taxon_name=taxon_name,
                user_input=user_input
            )

        if analysis_result:
            st.markdown("---")
            st.markdown(analysis_result)
            html_report = main.generate_html_report(analysis_result, raw_data)
            with open(html_report, "rb") as file:
                st.download_button(
                    label="Download Full HTML Report",
                    data=file,
                    file_name="taxonomic_analysis.html",
                    mime="text/html"
                )
        else:
            st.error("Analysis could not be completed. Please check the terminal for error messages.")