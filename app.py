# app.py

import streamlit as st
import main
import config

# ... (page config and title are the same) ...
st.set_page_config(
    page_title="SA Flora ID Assistant",
    page_icon="🌿",
    layout="centered"
)
st.title("🌿 Botanical Identification Assistant")
st.markdown("An AI-powered tool for identifying plants of the Southern African flora, with a focus on e-Flora SA data.")

with st.form(key='specimen_form'):
    st.subheader("1. Define Search Area")
    col1, col2, col3 = st.columns(3)
    with col1:
        taxon_name = st.text_input("Taxon", value=config.DEFAULT_TAXON_NAME)
    with col2:
        latitude = st.number_input("Latitude", value=config.DEFAULT_LATITUDE, format="%.6f")
    with col3:
        longitude = st.number_input("Longitude", value=config.DEFAULT_LONGITUDE, format="%.6f")
    radius_km = config.DEFAULT_RADIUS_KM

    st.subheader("2. Describe the Specimen")
    user_input = st.text_area(
        "Morphological Description & Locality Details",
        height=200,
        value="flowers in clusters of 6-10; leaves alternate, shorter than flowers. Flowers red outside, lobes cream inside, petaloid scales present. Found on a sandy coastal slope.",
        help="Provide as much detail as possible. Include habit, leaf arrangement, flower color/shape, and any information from the label like habitat or specific location."
    )
    submit_button = st.form_submit_button(label='Analyze Specimen')

if submit_button:
    st.subheader("3. Analysis Results")
    with st.spinner('Querying GBIF, scraping descriptions, and analyzing with Gemini... Please wait.'):
        # --- FINALIZED FUNCTION CALL ---
        analysis_result, raw_data = main.run_identification_process(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            taxon_name=taxon_name,
            user_input=user_input # This now perfectly matches the function signature
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