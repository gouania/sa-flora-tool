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
    layout="wide" # Use wide layout to give the map more space
)

# --- App Title and Description ---
st.title("🌿 Botanical Identification Assistant")
st.markdown("An AI-powered tool for identifying plants of the Southern African flora.")

# --- Session State Initialization ---
# We use session_state to remember the last clicked coordinates.
if "center" not in st.session_state:
    # Default center is roughly the center of South Africa
    st.session_state.center = [-29.0, 24.0]
if "location" not in st.session_state:
    st.session_state.location = [config.DEFAULT_LATITUDE, config.DEFAULT_LONGITUDE]

# --- Layout Configuration ---
# Create two columns: one for the map, one for the inputs/results
map_col, input_col = st.columns([0.6, 0.4]) # Give map 60% of the width

with map_col:
    st.subheader("1. Select Location on Map")
    
    # Create a Folium map
    m = folium.Map(location=st.session_state.center, zoom_start=5)
    
    # Add a marker for the last clicked location
    folium.Marker(
        st.session_state.location,
        popup="Selected Location",
        tooltip="Selected Location"
    ).add_to(m)

    # Render the map in Streamlit
    map_data = st_folium(m, width=700, height=500)

    # Update the location in session state when the map is clicked
    if map_data and map_data["last_clicked"]:
        st.session_state.location = [
            map_data["last_clicked"]["lat"],
            map_data["last_clicked"]["lng"],
        ]

with input_col:
    # --- Input Form ---
    with st.form(key='specimen_form'):
        st.subheader("2. Describe the Specimen")

        # The latitude and longitude fields are now automatically populated by map clicks
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
        
        taxon_name = st.text_input("Taxon", value=config.DEFAULT_TAXON_NAME)

        user_input = st.text_area(
            "Morphological Description & Locality Details",
            height=150,
            value="flowers in clusters of 6-10; leaves alternate, shorter than flowers. Flowers red outside, lobes cream inside, petaloid scales present.",
            help="Provide as much detail as possible: habit, leaves, flowers, and any label info."
        )

        submit_button = st.form_submit_button(label='Analyze Specimen')

# --- Analysis Execution ---
if submit_button:
    with input_col: # Display results in the second column
        st.subheader("3. Analysis Results")
        with st.spinner('Querying GBIF, scraping descriptions, and analyzing with Gemini... Please wait.'):
            analysis_result, raw_data = main.run_identification_process(
                latitude=latitude,
                longitude=longitude,
                radius_km=config.DEFAULT_RADIUS_KM,
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