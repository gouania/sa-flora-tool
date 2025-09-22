# config.py

# --- API and Model Configuration ---
# IMPORTANT: It is STRONGLY recommended to set your API key as an environment
# variable rather than pasting it directly into the code.
# We will handle loading this in the main.py script.
# Example: GOOGLE_API_KEY = "YOUR_API_KEY_HERE"

MODEL_NAME = "models/gemini-2.5-flash"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

# --- Default Search Parameters ---
# These can be easily changed here to alter the default search query.
DEFAULT_LATITUDE = -34.459745
DEFAULT_LONGITUDE = 20.4001533333
DEFAULT_RADIUS_KM = 4
DEFAULT_TAXON_NAME = "Thymelaeaceae"