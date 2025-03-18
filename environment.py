import os
import spacy
import re
import pandas as pd
from clean_kip import extract_dynamic_associations
import os
# from grammar import check_and_correct_grammar 
# from country_names import extract_details_from_txt  
# from dbqueries import (insert_company,fetch_all_companies,insert_indicator,insert_kpi,insert_year)

# Download the model within your application's code during startup
model_name = "en_core_web_sm"
try:
    # Check if the model is already downloaded
    nlp = spacy.load(model_name)
except OSError:
    print(f"Downloading {model_name}...")
    try:
        spacy.cli.download(model_name)
        nlp = spacy.load(model_name)
    except Exception as e:
        print(f"Error downloading model: {e}")
        exit(1)  # Exit with an error code
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)

def create_directory_if_needed(directory_path):
    """Ensure the given directory exists; if not, create it."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

def identify_environmental_indicators(text, environmental_keywords):
    """Identify environmental indicators, their metrics, and associated units from text."""
    doc = nlp(text)
    
    environmental_indicators = []
    latest_year = None  # Initialize latest_year to None

    for sentence in doc.sents:
        for keyword in environmental_keywords:
            if keyword.lower() in sentence.text.lower():

                matches = re.findall(r'\b(\d+(\.\d+)?)(\s*(?:tonnes|tCO2e|kWh|MWh|m3|l|kg|kgCO2e|tons|t|%|metric tons|CO2 equivalent|CO2|hectare|number|mtCO2))\b', sentence.text, re.IGNORECASE)
                for match in matches:
                    metric_value, _, metric_unit = match
                    
                    # Extracting the latest year from the sentence
                    years = re.findall(r'\b(\d{4})\b', sentence.text)
                    
                    if years:
                        latest_year = max(int(year) for year in years)  # Get the latest year

                        # Append only if there are valid matches for the metric
                        environmental_indicators.append(
                            (keyword, sentence.text, metric_value, metric_unit if metric_unit else None, latest_year)
                        )

                        break  # Once a keyword is found, move to the next sentence
        
    return environmental_indicators


# Directory containing text files
folder_path ='./uploads'
create_directory_if_needed('./environment')  # Ensure the target directory exists

# Define environmental keywords
environmental_keywords = [
    "climate change", "water security", "pollution and waste", 
    "biodiversity and land use", "supply chain", "material", "CO2e",
    "climate", "waste", "water", "air quality", "operational emissions", 
    "circular economy", "energy", "emissions", "environmental disclosures", 
    "recycling", "environmental impact assessments", "carbon emissions",
    "paper", "energy consumption", "carbon footprint", "water consumption", 
    "renewable energy", "non-renewable", "natural resource", "hazardous material", 
    "operational footprint", "environmental compliance", "environment", "natural capital",
    "product lifecycle", "climate strategy", "water management", "waste management", "energy management",
    "tcfd", "TCFD disclosure", "energy usage", "water usage", "Carbon Disclosure Project (CDP)",
    "environmental management", "ghg", "climate strategy", "waste & pollution", "use of resources", "operational footprint",
    "net zero", "carbon neutral", "carbon intensity"
]

# Initialize an empty list to store environmental indicators
environmental_indicators = []

# Load spaCy model outside the loop to avoid reloading it for each file
nlp = spacy.load("en_core_web_sm")
nlp.max_length = 5000000 

# Extract environmental indicators from each document
def refine_environment_data():
    text_files = [file for file in os.listdir(folder_path) if file.endswith('.txt')]
    for text_file in text_files:
        text_path = os.path.join(folder_path, text_file)
   
       
        metadata=text_file.split("-")
        
        # counrty_output=extract_details_from_txt(text_path)
        with open(text_path, 'r', encoding='utf-8') as file:
            text = file.read()
            
        company_name=metadata[0].replace("_", " ")
        sector=metadata[1]
        region=metadata[2]
        country=metadata[3]
        year=metadata[4].split(".")[0]
       
        #company_name = os.path.splitext(text_file)[0]  # Assuming file name is company name
        
        extracted_indicators = identify_environmental_indicators(text, environmental_keywords)
        
        
            

        """counrty_output['Company Name'],counrty_output['Country'],counrty_output['Region'],"""
        environmental_indicators.extend([(company_name,sector,country,region, indicator[0], indicator[1], indicator[2], indicator[3], year) for indicator in extracted_indicators])
    
    # Create DataFrame from environmental indicators
    df_environmental_indicators = pd.DataFrame(environmental_indicators, columns=['Company Name','Sector', 'Country','Region', 'Indicator', 'Context', 'Metric', 'Metric Unit', 'Latest Year'])

    # Ensure the directory exists before saving
    create_directory_if_needed('./environment')

    filename = './environment/environmental_data_with_year.csv'
    # Saving DataFrame to CSV file
    df_environmental_indicators.to_csv(filename, index=False)
    reading_csv_file()

def reading_csv_file():
    # Read the CSV file
    df = pd.read_csv('./environment/environmental_data_with_year.csv')

    # Remove leading/trailing white spaces
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    df['Company Name']=df['Company Name'].str.capitalize()
    df['Sector']=df['Sector'].str.capitalize()
    df['Country']=df['Country'].str.capitalize()
    df['Region']=df['Region'].str.capitalize()
    #df['Company']=df['Company'].str.capitalize()
    # Split multiline text into separate lines
    df['Context'] = df['Context'].str.replace('\n', ' ')

    # Capitalize text in Indicator and Unit columns
    df['Indicator'] = df['Indicator'].str.capitalize()

    # Rename the 'Context' column to 'KPI' and 'Metric' to 'KPI value', and 'Metric Unit' to 'Unit'
    df.rename(columns={'Context': 'KPI'}, inplace=True)
    df.rename(columns={'Metric': 'KPI Value'}, inplace=True)
    df.rename(columns={'Metric Unit': 'Unit'}, inplace=True)
    df.rename(columns={'Latest Year': 'Year'}, inplace=True)

    # Writing cleaned data to a new CSV file
    df.to_csv('./environment/_london_environmental_metric.csv', index=False)

    df_1 = pd.read_csv('./environment/_london_environmental_metric.csv')

    # Identify rows associated with the environmental pillar
    environment_keywords = ['environment', 'carbon', 'emission', 'energy efficiency', 'ghg', 'scope', 'energy management', 'water', 'waste', 'natural capital']
    environment_mask = df_1['KPI'].str.contains('|'.join(environment_keywords), case=False)

    # Remove rows associated with the Governance or Social pillars
    governance_keywords = ['governance', 'board', 'regulation', 'compliance', 'tenure', 'management', 'tax', 'policy', 'transformation', 'workforce']
    social_keywords = ['social', 'community', 'labor', 'workforce', 'human rights', 'education', 'training', 'injury', 'rate', 'fatalities', 'bursaries']
    governance_mask = df_1['KPI'].str.contains('|'.join(governance_keywords), case=False)
    social_mask = df_1['KPI'].str.contains('|'.join(social_keywords), case=False)

    # Combine masks to remove rows associated with Governance or Social pillars and include rows associated with the Environmental pillar
    remove_mask = governance_mask | social_mask
    environment_df = df_1[environment_mask & ~remove_mask]
    
    for index, row in environment_df.iterrows():
        # Apply the extract_dynamic_associations function to the 'KPI' column
        detail = extract_dynamic_associations(row['KPI'], row['Indicator'])
    
        if isinstance(detail, list):
            # Join list items with a comma
            environment_df.at[index, 'KPI'] = ', '.join(detail)
        else:
            # If not a list, assign detail directly
            environment_df.at[index, 'KPI'] = detail
     

        # Convert list of dictionaries to a set of company names for quick lookup
        # if row['Company Name'] not in {company["company_name"] for company in c_name}:
        #     c_id=insert_company(row['Company Name'], row['Sector'], row['Country'], row['Region'])
        
        #     i_id=insert_indicator(c_id, environment_df['Indicator'],'ENVIRONMENT')
        #     kpi_id=insert_kpi(i_id, environment_df['KPI'],environment_df['Unit'],environment_df['KPI Value'])
        #     insert_year(kpi_id, environment_df['Year'])
            # Save the filtered DataFrame back to a CSV file
    environment_df.to_csv('./environment/environment_report.csv', index=False)
