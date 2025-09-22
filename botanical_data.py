# botanical_data.py

import requests
from bs4 import BeautifulSoup
import re
import google.generativeai as genai
import time
import pygbif.species as gbif_species
import pygbif.occurrences as gbif_occ
import math
from functools import wraps

# Import constants from your config file
from config import HEADERS, MODEL_NAME

# --- Decorators and Helper Functions ---
def retry_request(max_attempts=3, delay=2):
    """Decorator to retry a function if a requests.RequestException occurs."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    print(f"--> Network attempt {attempt + 1} for '{func.__name__}' failed: {e}")
                    if attempt < max_attempts - 1:
                        print(f"--> Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        print(f"--> All network attempts failed for '{func.__name__}'.")
                        return None
        return wrapper
    return decorator

# --- GBIF Functions ---
def get_species_list_from_gbif(latitude, longitude, radius_km, taxon_name):
    """Queries GBIF for a list of species within a given radius of a coordinate."""
    print(f"Querying GBIF for '{taxon_name}' species within {radius_km}km of ({latitude}, {longitude})...")
    try:
        taxon_info = gbif_species.name_backbone(name=taxon_name)
        if 'usageKey' not in taxon_info:
            print(f"--> Could not find a taxon key for '{taxon_name}' on GBIF.")
            return []
        if 'rank' in taxon_info: print(f"--> GBIF identified '{taxon_name}' as a {taxon_info['rank'].lower()}.")
        taxon_key = taxon_info['usageKey']
        print(f"--> Found GBIF taxonKey for '{taxon_name}': {taxon_key}")
    except Exception as e:
        print(f"--> Error looking up taxon key on GBIF: {e}")
        return []

    lat_offset = radius_km / 111.32
    lon_offset = radius_km / (111.32 * abs(math.cos(math.radians(latitude))))
    min_lat, max_lat = latitude - lat_offset, latitude + lat_offset
    min_lon, max_lon = longitude - lon_offset, longitude + lon_offset

    try:
        occurrences = gbif_occ.search(
            taxonKey=taxon_key, decimalLatitude=f'{min_lat},{max_lat}', decimalLongitude=f'{min_lon},{max_lon}',
            hasCoordinate=True, hasGeospatialIssue=False, limit=1000
        )
        species_set = set(record['species'] for record in occurrences['results'] if 'species' in record)
        species_list = sorted(list(species_set))
        print(f"--> Found {len(species_list)} unique species on GBIF.")
        return species_list
    except Exception as e:
        print(f"--> An error occurred during the GBIF occurrence search: {e}")
        return []

# --- POWO Scraping Functions ---
@retry_request()
def find_powo_taxon_id(scientific_name):
    """Finds the POWO taxon ID for a given scientific name."""
    search_url = "https://powo.science.kew.org/api/2/search"
    params = {'q': scientific_name}
    headers = {'User-Agent': HEADERS['User-Agent'], 'Referer': 'https://powo.science.kew.org/'}
    response = requests.get(search_url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    if data and data.get('results'):
        first_result = data['results'][0]
        taxon_id = first_result.get('fqId')
        found_name = first_result.get('name')
        print(f"--> Found POWO match: '{found_name}' (ID: {taxon_id})")
        return taxon_id
    else:
        print(f"--> No POWO results found for '{scientific_name}'")
        return None

def scrape_powo_description_from_html(url):
    """Scrapes the morphological description from a POWO general information page."""
    @retry_request()
    def _fetch_html(target_url):
        headers = {'User-Agent': HEADERS['User-Agent'], 'Referer': 'https://powo.science.kew.org/'}
        response = requests.get(target_url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text

    html_content = _fetch_html(url)
    if not html_content: return (False, "Failed to fetch POWO page after multiple attempts.")

    soup = BeautifulSoup(html_content, 'html.parser')
    descriptions_section = soup.find('section', id='descriptions')
    if not descriptions_section: return (False, "No description section found on POWO page.")

    all_descriptions_text = []
    has_morphological_data = False
    morphological_keywords = ['morphology', 'habit', 'leaves', 'stem', 'flowers', 'fruit', 'inflorescence', 'bracts', 'perianth', 'style', 'ecology', 'note', 'type']
    description_blocks = descriptions_section.find_all('div', class_='description')
    if not description_blocks: return (False, "Description section exists but contains no description blocks.")

    for block in description_blocks:
        source_text = "Unknown Source"
        source_button = block.find('button', class_='collapser')
        if source_button and source_button.find('span', class_='text'):
            source_text = source_button.find('span', class_='text').get_text(strip=True)
        all_descriptions_text.append(f"--- {source_text} ---\n")
        dl = block.find('dl', class_='c-article-desc-table')
        if dl:
            for dt, dd in zip(dl.find_all('dt'), dl.find_all('dd')):
                term = ' '.join(span.get_text(strip=True) for span in dt.find_all('span'))
                if any(keyword in term.lower() for keyword in morphological_keywords): has_morphological_data = True
                definition = dd.get_text(strip=True)
                formatted_definition = re.sub(r"([a-z])([A-Z])", r"\1\n\2", definition)
                all_descriptions_text.append(f"{term}:\n{formatted_definition}\n")

    if not has_morphological_data:
        print("--> POWO page found, but it contains no useful morphological data.")
        return (False, "No morphological description found on POWO.")
    return (True, "\n".join(all_descriptions_text))

# --- e-Flora SA Scraping Functions ---
@retry_request()
def find_eflorasa_url(scientific_name):
    """Searches SANBI's internal API to find the e-Flora SA URL for a species."""
    search_url = "https://biodiversityadvisor.sanbi.org/search/ServersideSearch"
    params = {'q': scientific_name, 'index': 'bodatsa', 'filter': 'synonyms', 'sortBy': '_score', 'sortOrder': 'asc'}
    response = requests.get(search_url, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    data = response.json()
    if data and data.get('data') and len(data['data']) > 0:
        first_result = data['data'][0]
        source = first_result.get('_source', {})
        full_name = source.get('italicspeciesname', '')
        synonyms = str(source.get('synonyms', ''))
        if scientific_name.lower() in full_name.lower() or scientific_name.lower() in synonyms.lower():
            species_id = source.get('speciesid')
            if species_id:
                found_url = f"https://biodiversityadvisor.sanbi.org/search/detail/{species_id}"
                print(f"--> Found e-Flora SA match (via API): {found_url}")
                return found_url
    print(f"--> No e-Flora SA match found for '{scientific_name}'")
    return None

def scrape_eflorasa_description(url):
    """Scrapes description sections from a given e-Flora of South Africa URL."""
    @retry_request()
    def _fetch_html(target_url):
        response = requests.get(target_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.text

    html_content = _fetch_html(url)
    if not html_content:
        return (False, "Failed to fetch e-Flora SA page after multiple attempts.")

    soup = BeautifulSoup(html_content, 'html.parser')
    all_blocks = soup.find_all('div', class_='details-bordered')
    extracted_data = []

    for block in all_blocks:
        heading_tag = block.find('div', class_='details-bordered-heading')
        body_tag = block.find('div', class_='details-bordered-body')

        if heading_tag and body_tag:
            heading_text = heading_tag.get_text(strip=True)
            if heading_text in ["Morphological description", "Habitat", "Distribution", "Flowering time", "Altitude"]:
                paragraphs = body_tag.find_all('p')
                body_text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                if body_text:
                    extracted_data.append(f"--- {heading_text} ---\n{body_text}")

    if extracted_data:
        full_text = "\n\n".join(extracted_data)
        return (True, f"--- According to e-Flora of South Africa (SANBI) ---\n\n{full_text}")

    return (False, "e-Flora SA page found, but no relevant description sections could be parsed.")

# --- Gemini AI Analysis ---
def analyze_with_gemini(scraped_descriptions, specimen_details, label_data, failed_species_list):
    """Uses the Gemini model to analyze scraped data and specimen notes."""
    print("\nAnalyzing with Gemini...")
    prompt = f"""
    You are an expert botanist and taxonomist. Your task is to compare provided descriptions with observations from a herbarium specimen.
    **Collected Botanical Descriptions:**
    {scraped_descriptions if scraped_descriptions else "No descriptions were successfully scraped."}
    ---
    **Species Found on GBIF but Lacking a Scraped Description:**
    {failed_species_list if failed_species_list else "None"}
    ---
    **Specimen Observations:**
    {specimen_details if specimen_details else "No specific specimen observations provided."}
    ---
    **Specimen Label Data:**
    {label_data if label_data else "No specific label data provided."}
    ---
    **Your Task:**
    Provide your analysis with the following markdown headings:
    ### **Analysis of Potential Species**
    - For each species with a description, discuss how the specimen's features align with or contradict it.
    ### **Most Likely Candidates**
    - Identify the top 1-2 most likely candidate species from the ones with available descriptions.
    ### **Species Lacking Descriptions**
    - List the species recorded in the area that could not be automatically retrieved. Advise the user that these are still valid possibilities.
    ### **Further Steps for Confirmation**
    - Suggest concrete actions to confirm the identification.
    ### **Confidence Level**
    - State your confidence in the potential identification based ONLY on the available scraped data.
    """
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        # Handle cases where the response might be empty or blocked
        if not response.parts:
            return "Analysis was blocked by the safety filter or returned no content."
        return response.text
    except Exception as e:
        return f"An error occurred during Gemini analysis: {e}"