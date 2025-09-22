# app.py

import streamlit as st
import main  # Import your main script's functions
import config # Import your configuration

# --- Page Configuration ---
st.set_page_config(
    page_title="SA Flora ID Assistant",
    page_icon="🌿",
    layout="centered"
)

# --- App Title and Description ---
st.title("🌿 Botanical Identification Assistant")
st.markdown("An AI-powered tool for identifying plants of the Southern African flora, with a focus on e-Flora SA data.")

# --- Input Fields in a Form ---
with st.form(key='specimen_form'):
    st.subheader("1. Enter Specimen and Location Data")

    # Use columns for a cleaner layout
    col1, col2 = st.columns(2)
    with col1:
        taxon_name = st.text_input("Taxon", value=config.DEFAULT_TAXON_NAME)
        latitude = st.number_input("Latitude", value=config.DEFAULT_LATITUDE, format="%.6f")
    with col2:
        radius_km = st.number_input("Search Radius (km)", value=config.DEFAULT_RADIUS_KM)
        longitude = st.number_input("Longitude", value=config.DEFAULT_LONGITUDE, format="%.6f")

    st.subheader("2. Enter Morphological and Label Data")
    specimen_notes = st.text_area("Morphological Observations", "flowers in clusters of 6-10; leaves alternate, shorter than flowers. Flowers red outside, lobes cream inside, petaloid scales present")
    label_notes = st.text_area("Label Data", "none")

    # The button to start the analysis
    submit_button = st.form_submit_button(label='Analyze Specimen')

# --- Analysis Execution ---
if submit_button:
    st.subheader("3. Analysis Results")
    # Show a spinner while the analysis is running
    with st.spinner('Querying GBIF, scraping descriptions, and analyzing with Gemini... Please wait.'):
        # Call the main function from your script
        analysis_result, raw_data = main.run_identification_process(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            taxon_name=taxon_name,
            specimen_notes=specimen_notes,
            label_notes=label_notes
        )

    if analysis_result:
        st.markdown("---")
        # Display the Gemini analysis using markdown for nice formatting
        st.markdown(analysis_result)

        # Provide a download link for the full HTML report
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