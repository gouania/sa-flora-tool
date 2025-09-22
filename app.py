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
    st.subheader("1. Define Search Area")

    # Use columns for a cleaner layout
    col1, col2, col3 = st.columns(3)
    with col1:
        taxon_name = st.text_input("Taxon", value=config.DEFAULT_TAXON_NAME)
    with col2:
        latitude = st.number_input("Latitude", value=config.DEFAULT_LATITUDE, format="%.6f")
    with col3:
        longitude = st.number_input("Longitude", value=config.DEFAULT_LONGITUDE, format="%.6f")
    
    # Let's hide the radius for now to keep it simple, but it can be added back easily.
    radius_km = config.DEFAULT_RADIUS_KM 

    st.subheader("2. Describe the Specimen")

    # --- CONSOLIDATED INPUT FIELD ---
    # We've replaced the two separate text areas with this single one.
    user_input = st.text_area(
        "Morphological Description & Locality Details",
        height=200,
        value="flowers in clusters of 6-10; leaves alternate, shorter than flowers. Flowers red outside, lobes cream inside, petaloid scales present. Found on a sandy coastal slope.",
        help="Provide as much detail as possible. Include habit, leaf arrangement, flower color/shape, and any information from the label like habitat or specific location."
    )

    # The button to start the analysis
    submit_button = st.form_submit_button(label='Analyze Specimen')

# --- Analysis Execution ---
if submit_button:
    st.subheader("3. Analysis Results")
    # Show a spinner while the analysis is running
    with st.spinner('Querying GBIF, scraping descriptions, and analyzing with Gemini... Please wait.'):
        # --- UPDATED FUNCTION CALL ---
        # We now pass the consolidated `user_input` to the `specimen_notes` parameter.
        # We pass an empty string to `label_notes` as it's now combined.
        analysis_result, raw_data = main.run_identification_process(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            taxon_name=taxon_name,
            specimen_notes=user_input, # Pass the combined input here
            label_notes=""             # Pass an empty string here
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