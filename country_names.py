import os
import re
import spacy
import geonamescache
import pycountry
# Load NLP model for entity recognition
nlp = spacy.load("en_core_web_sm")

# Load Geonames cache (for dynamic country/region detection)
gc = geonamescache.GeonamesCache()
all_countries = [country["name"] for country in gc.get_countries().values()]
all_regions = [region["name"] for region in gc.get_continents().values()]

def extract_text_from_txt(file_path):
    """Reads and extracts text from a given .txt file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def extract_company_name(text):
    """Extracts the company name using Named Entity Recognition (NER)."""
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "ORG":  # ORG = Organization (Company Name)
            return ent.text
    return "Unknown Company"

def extract_country(text):
    """Extracts country name dynamically from the text."""
    for country in all_countries:
        if re.search(rf"\b{re.escape(country)}\b", text, re.IGNORECASE):
            return country
    return "Unknown Country"

def extract_region(text):
    """Extracts region/state/province dynamically from the text."""
    for region in all_regions:
        if re.search(rf"\b{re.escape(region)}\b", text, re.IGNORECASE):
            return region
    return "Unknown Region"


country_to_continent = {}
for continent_code, continent_info in gc.get_continents().items():
    country_codes = continent_info.get("cc2", "").split(",")  # Get country codes in that continent
    for country_code in country_codes:
        country_to_continent[country_code] = continent_code 

def get_continent_by_country(country_name):
    """Returns the continent of a given country name using geonamescache."""
    
    country = pycountry.countries.get(name=country_name)
    if country and country.alpha_2 in country_to_continent:
        return country_to_continent[country.alpha_2]
    return "Unknown Continent"




def extract_details_from_txt(file_path):
    """Extracts company name, country, and region from a .txt file."""
    text = extract_text_from_txt(file_path)
    
    company_name = extract_company_name(text)
    country = extract_country(text)
    region = get_continent_by_country(country)

    return {
        "File": os.path.basename(file_path),
        "Company Name": company_name,
        "Country": country,
        "Region": region
    }

# Process all .txt files in "./uploads" folder
# upload_dir = "./uploads"

# if not os.path.exists(upload_dir):
#     print("Error: The './uploads' directory does not exist.")
# else:
#     txt_files = [f for f in os.listdir(upload_dir) if f.endswith(".txt")]

#     if not txt_files:
#         print("No .txt files found in './uploads'.")
#     else:
#         for txt_file in txt_files:
#             file_path = os.path.join(upload_dir, txt_file)
#             extracted_info = extract_details_from_txt(file_path)
            #print(extracted_info)
