# Botanical Identification Assistant for Southern African Flora

## 1. Overview

This tool is a Python-based assistant for botanists and plant enthusiasts working with Southern African flora. It automates the process of identifying a plant specimen by:

1.  Querying the Global Biodiversity Information Facility (GBIF) for a list of all species within a specific family (e.g., *Thymelaeaceae*) that have been recorded in a given GPS coordinate and radius.
2.  Scraping detailed morphological descriptions for each of those species, prioritizing the high-quality data from the **e-Flora of South Africa (SANBI)**.
3.  Falling back to **Plants of the World Online (POWO)** if a SANBI description is unavailable.
4.  Using Google's Gemini AI model to perform a taxonomic analysis, comparing user-provided specimen notes against the scraped descriptions to identify the most likely candidates.
5.  Generating a clean, portable HTML report with the full analysis.

This project was created by a plant taxonomist at RBG Kew to streamline the identification workflow and leverage modern AI for botanical research.

## 2. Features

-   **Hyper-local Species Lists:** Get a checklist of potential species for your specific collection site.
-   **Prioritized South African Data:** Uses e-Flora SA as the primary data source for the highest relevance.
-   **AI-Powered Taxonomic Analysis:** Moves beyond simple keyword matching to perform a reasoned, comparative analysis.
-   **Detailed Reporting:** Generates a comprehensive HTML report including the AI's reasoning, further steps for confirmation, and the verbatim data for manual review.
-   **Command-Line Interface:** Simple, interactive prompts for entering specimen and label data.

## 3. Installation and Setup

Follow these steps to get the tool running on your local machine.

### Prerequisites

-   Python 3.8 or newer.
-   A Google API Key for using the Gemini model. You can get one from [Google AI Studio](https://aistudio.google.com/app/apikey).

### Step-by-Step Guide

1.  **Clone the Repository:**
    Open your terminal or command prompt and clone this repository to your local machine.
    ```bash
    git clone https://github.com/gouania/sa-flora-tool
    cd YOUR_REPOSITORY_NAME
    ```

2.  **Install Dependencies:**
    This project uses a number of Python libraries. Install them all with a single command using the `requirements.txt` file.
    ```bash
    # For Windows
    py -m pip install -r requirements.txt

    # For macOS/Linux
    python3 -m pip install -r requirements.txt
    ```

3.  **Set Your API Key:**
    You must set your Google API Key as an environment variable for the script to access it securely.

    -   **On Windows (in Command Prompt):**
        ```cmd
        setx GOOGLE_API_KEY "PASTE_YOUR_API_KEY_HERE"
        ```
    -   **On macOS/Linux (add to `~/.zshrc` or `~/.bash_profile`):**
        ```bash
        export GOOGLE_API_KEY="PASTE_YOUR_API_KEY_HERE"
        ```
    **Important:** You must close and re-open your terminal/VS Code for this change to take effect.

## 4. How to Use

1.  **Navigate to the Directory:**
    Make sure your terminal is in the project's root directory.

2.  **Run the Main Script:**
    ```bash
    # For Windows
    py main.py

    # For macOS/Linux
    python3 main.py
    ```

3.  **Follow the Prompts:**
    The script will ask you to enter your morphological observations and any data from the specimen label.

4.  **Check the Output:**
    The script will print its progress and the final AI analysis to the terminal. A detailed file named `taxonomic_analysis.html` will be saved in the project folder.

## 5. Future Development

-   [ ] Develop a simple web-based user interface (e.g., using Streamlit or Flask).
-   [ ] Add the ability to upload and analyze specimen images.
-   [ ] 