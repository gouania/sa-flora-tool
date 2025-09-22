# main.py

import os
import time
import markdown
import google.generativeai as genai

# Import our custom modules
import botanical_data as bd
import config

# --- MODIFIED FUNCTION SIGNATURE ---
def run_identification_process(latitude, longitude, radius_km, taxon_name, user_input):
    """The main workflow for the botanical identification tool."""
    # 1. Get species list from GBIF.
    scientific_names = bd.get_species_list_from_gbif(latitude, longitude, radius_km, taxon_name)

    if not scientific_names:
        print("\nNo species found in the specified area. Halting process.")
        return None, None

    print("\nProceeding to scrape descriptions for the following species:")
    for name in scientific_names:
        print(f"- {name}")

    species_data = []

    # 2. Loop through each species to scrape its data.
    for name in scientific_names:
        print(f"\n{'='*60}\nProcessing: {name}\n{'='*60}")
        # ... (scraping logic remains the same) ...
        description_found = False
        clean_name = " ".join(name.split()[:2])
        print("--- Attempting to scrape from e-Flora of South Africa (SANBI) ---")
        eflora_url = bd.find_eflorasa_url(clean_name)
        if eflora_url:
            success, description = bd.scrape_eflorasa_description(eflora_url)
            if success:
                print("--> SUCCESS: Found and scraped a valid description from e-Flora SA.")
                species_data.append({'name': name, 'success': True, 'description': description})
                description_found = True
            else:
                print(f"--> e-Flora SA scrape failed: {description}")
        if not description_found:
            print("\n--> e-Flora SA data not found or failed. Trying POWO as a fallback...")
            taxon_id = bd.find_powo_taxon_id(clean_name)
            if taxon_id:
                target_url = f"https://powo.science.kew.org/taxon/{taxon_id}/general-information"
                print(f"--> Scraping POWO URL: {target_url}")
                success, description = bd.scrape_powo_description_from_html(target_url)
                if success:
                    print("--> SUCCESS: Found and scraped a valid description from POWO.")
                    species_data.append({'name': name, 'success': True, 'description': description})
                    description_found = True
                else:
                    print(f"--> POWO scrape failed: {description}")
        if not description_found:
            reason = "No valid description found on e-Flora SA or POWO."
            print(f"--> FINAL RESULT: {reason}")
            species_data.append({'name': name, 'success': False, 'reason': reason})
        print("\n--> Processing complete for this species. Pausing for 2 seconds...")
        time.sleep(2)

    # 3. Prepare data for AI analysis.
    successful_scrapes = [s for s in species_data if s['success']]
    failed_species = [s for s in species_data if not s['success']]
    combined_descriptions = "\n\n".join([f"--- Data for {s['name']} ---\n{s['description']}" for s in successful_scrapes])
    failed_species_list_str = "\n".join([f"- {s['name']}" for s in failed_species])

    if not successful_scrapes and not failed_species:
        print("No species data was found or scraped for this query.")
        return None, None

    # --- MODIFIED FUNCTION CALL ---
    analysis_result = bd.analyze_with_gemini(combined_descriptions, user_input, failed_species_list_str)
    return analysis_result, combined_descriptions

def generate_html_report(analysis_content, verbatim_data):
    # ... (this function remains exactly the same) ...
    html_body = markdown.markdown(analysis_content, extensions=['tables'])
    appendix_html = ""
    if verbatim_data:
        appendix_html = f"""
        <hr><h2>Verbatim Scraped Data for Manual Analysis</h2>
        <details><summary>Click to expand/collapse raw data</summary>
        <pre style="white-space: pre-wrap; word-wrap: break-word; background-color: #f6f8fa; padding: 15px; border-radius: 5px; border: 1px solid #ddd;"><code>{verbatim_data}</code></pre>
        </details>"""
    html_template = f"""
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Taxonomic Analysis Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 20px auto; padding: 25px; border: 1px solid #e1e1e1; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 1em; margin-bottom: 1em; }}
        th, td {{ text-align: left; padding: 12px; border: 1px solid #ddd; vertical-align: top; }}
        th {{ background-color: #f7f7f7; font-weight: 600; }}
        h1, h2, h3 {{ color: #2d3748; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.3em; }}
        details {{ margin-top: 1.5em; border: 1px solid #ddd; border-radius: 5px; padding: 10px; }}
        summary {{ font-weight: bold; cursor: pointer; }}
    </style></head><body><h1>Taxonomic Analysis Report</h1>{html_body}{appendix_html}</body></html>"""
    filename = "taxonomic_analysis.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    return filename

if __name__ == "__main__":
    # --- 1. Configure API Key ---
    try:
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)
        print("✅ Google API Key configured successfully from environment variable.")
    except (ValueError, KeyError) as e:
        print(f"Error: {e}")
        print("Please set the GOOGLE_API_KEY environment variable before running.")
        exit()

    # --- 2. Get User Input (MODIFIED) ---
    print(f"\n{'='*60}\nSPECIMEN DATA ENTRY\n{'='*60}")
    user_input_cli = input("Enter morphological description and locality details: ")

    # --- 3. Run the main process (MODIFIED) ---
    analysis, raw_data = run_identification_process(
        latitude=config.DEFAULT_LATITUDE,
        longitude=config.DEFAULT_LONGITUDE,
        radius_km=config.DEFAULT_RADIUS_KM,
        taxon_name=config.DEFAULT_TAXON_NAME,
        user_input=user_input_cli
    )

    # --- 4. Generate and save the report ---
    if analysis:
        print(f"\n\n{'='*60}\nGEMINI TAXONOMIC ANALYSIS\n{'='*60}")
        print(analysis)
        report_filename = generate_html_report(analysis, raw_data)
        print("\n" + "="*60)
        print(f"✅ Analysis complete. Report saved as '{report_filename}'.")
    else:
        print("Could not complete analysis.")

    print(f"\n{'='*60}\nReady for next query.\n{'='*60}")