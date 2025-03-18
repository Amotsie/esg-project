import os
import spacy
import re
import pandas as pd
from clean_kip import extract_dynamic_associations
# from grammar import check_and_correct_grammar
from country_names import extract_details_from_txt
from dbqueries import (insert_company,fetch_all_companies,insert_indicator)


# Ensure the directory exists before saving the file
def create_directory(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

def identify_governance_indicators(text, governance_keywords):
    """Identify governance indicators, their metrics, and associated units from text."""
    doc = nlp(text)
    
    governance_indicators = []
    latest_year = None
    for sentence in doc.sents:
        for keyword in governance_keywords:
            if keyword.lower() in sentence.text.lower():
                matches = re.findall(
                    r'\b(\d+(?:\.\d+)?)(\s*(?:director|directors|employees|Statement of compliance|hours|days|years|%|level|No|Yes|ZAR|thousand|million|billion|number|score|rand))?\b',
                    sentence.text,
                    re.IGNORECASE
                )
                for match in matches:
                    metric_value, metric_unit = match
                    # Extracting the latest year from the sentence
                    years = re.findall(r'\b(\d{4})\b', sentence.text)
                    if years:
                        latest_year = max(int(year) for year in years)
                    governance_indicators.append((keyword, sentence.text, metric_value, metric_unit, latest_year))
                break  # Once a keyword is found, move to the next sentence
    return governance_indicators

# Define governance keywords
governance_keywords = [
    "board composition", "ethical behavior", "compliance", 
    "risk management", "tax transparency", "anti-corruption", 
    "stakeholder engagement", "public policy", "ethics and integrity", 
    "customer privacy", "executive remuneration", "corporate governance regulations", 
    "corporate governance", "board diversity", "board structure", 
    "regulations", "executive", "gender", "board", "whistleblower", "code of conduct",
    "internal controls", "privacy policies", "employee age", "board meeting", "number of employees",
    "workforce", "employees", "full time equivalent employees", "incentives", "diversity", "B-BBEE level", 
    "equality", "employment equity", "leadership", "staff turnover", "representation", "transformation", "ethics & integrity", 
    "total number of employees", "occupational levels", "woman in management", "employment equity demographics",
    "gender breakdown", "ombudsman resolutions", "political party funding", "board meeting attendance",
    "business ethics", "policy influence", "tax strategy", "organizational structure",
    "ownership & shareholder rights", "budget management", "quality & integrity", "corporate behaviour"
]

# Initialize an empty list to store governance indicators
governance_indicators = []

# Load spaCy model outside the loop to avoid reloading it for each file
nlp = spacy.load("en_core_web_sm")
nlp.max_length = 5000000 

def process():
    folder_path = "./uploads"
    text_files = [file for file in os.listdir(folder_path) if file.endswith('.txt')]
    # Create the governance directory if it doesn't exist
    create_directory('./governance')

    # Extract governance indicators from each document
    for text_file in text_files:
        
        text_path = os.path.join(folder_path, text_file)
        counrty_output=extract_details_from_txt(text_path)
        metadata=text_file.split("-")
        with open(text_path, 'r', encoding='utf-8') as file:
            text = file.read()
        company_name=metadata[0]
        sector=metadata[1]
        region=metadata[2]
        country=metadata[3]
        year=metadata[4].split(".")[0]
        print("year ", year )
            
            
        #company_name = os.path.splitext(text_file)[0]  # Assuming file name is company name
        extracted_indicators = identify_governance_indicators(text, governance_keywords)
        governance_indicators.extend([(company_name,sector,country,region, indicator[0], indicator[1], indicator[2], indicator[3], year) for indicator in extracted_indicators])

    # Create DataFrame from governance indicators
    df_governance_indicators = pd.DataFrame(governance_indicators, columns=['Company Name','Sector', 'Country','Region', 'Indicator', 'Context', 'Metric', 'Metric Unit', 'Year'])
    filename = './governance/governance_data_with_year.csv'
    # Saving DataFrame to CSV file
    df_governance_indicators.to_csv(filename, index=False)
    refine_matrix()

def refine_matrix():
    matrix_filename = './governance/governance_data_with_year.csv'
    new_matrix_filename = './governance/new_governance_metric.csv'
    df = pd.read_csv(matrix_filename)

    # Remove leading/trailing white spaces
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

    df['Company Name']=df['Company Name'].str.capitalize()
    df['Sector']=df['Sector'].str.capitalize()
    df['Country']=df['Country'].str.capitalize()
    df['Region']=df['Region'].str.capitalize()

    # Split multiline text into separate lines
    df['Context'] = df['Context'].str.replace('\n', ' ')

    # Capitalize text in Indicator and Unit columns
    df['Indicator'] = df['Indicator'].str.capitalize()

    # Rename the 'Context' column to 'KPI' and 'Metric' to 'KPI value', and 'Metric Unit' to 'Unit'
    df.rename(columns={'Context': 'KPI'}, inplace=True)
    df.rename(columns={'Metric': 'KPI Value'}, inplace=True)
    df.rename(columns={'Metric Unit': 'Unit'}, inplace=True)
    df.rename(columns={'Latest year': 'Year'}, inplace=True)

    # Writing cleaned data to a new CSV file
    df.to_csv(new_matrix_filename, index=False)
    governance_last_matrix()

def governance_last_matrix():
    refined_filename = './governance/governance_report.csv'
    new_matrix_filename = './governance/new_governance_metric.csv'
    # Step 1: Read the CSV file into a DataFrame
    df = pd.read_csv(new_matrix_filename)

    # Step 2: Identify rows associated with the governance pillar
    governance_keywords = ['governance', 'board', 'regulation', 'compliance', 'tenure', 'management', 'tax', 'policy', 'transformation', 'workforce', 'employee', 'age', 'level', 'years', 'executive']
    governance_mask = df['KPI'].str.contains('|'.join(governance_keywords), case=False)

    # Step 3: Remove rows associated with the Environmental or Social pillars
    environment_keywords = ['environment', 'carbon', 'emission', 'energy efficiency']  # Add more keywords as needed
    social_keywords = ['social', 'community', 'labor', 'workforce', 'human rights', 'education', 'training', 'injury', 'rate', 'fatalities', 'bursaries']  # Add more keywords as needed
    environment_mask = df['KPI'].str.contains('|'.join(environment_keywords), case=False)
    social_mask = df['KPI'].str.contains('|'.join(social_keywords), case=False)

    # Combine masks to remove rows associated with Environmental or Social pillars and include rows associated with the governance pillar
    remove_mask = environment_mask | social_mask
    governance_df = df[governance_mask & ~remove_mask]
    
    for index, row in governance_df.iterrows():
        # Apply the extract_dynamic_associations function to the 'KPI' column
        detail = extract_dynamic_associations(row['KPI'], row['Indicator'])
    
        if isinstance(detail, list):
            # Join list items with a comma
            governance_df.at[index, 'KPI'] = ', '.join(detail)
        else:
            # If not a list, assign detail directly
            governance_df.at[index, 'KPI'] = detail
        # c_name=fetch_all_companies()
        # print(c_name)

        # Convert list of dictionaries to a set of company names for quick lookup
        # if row['Company Name'] not in {company["company_name"] for company in c_name}:
        #     c_id=insert_company(row['Company Name'], row['Sector'], row['Country'], row['Region'])
        #     i_id=insert_indicator(c_id, governance_df['Indicator'],'GOVERNANCE')
        #     kpi_id=insert_kpi(i_id, governance_df['KPI'],governance_df['Unit'],governance_df['KPI Value'])
        #     insert_year(kpi_id, governance_df['Year'])
    # Step 4: Save the filtered DataFrame back to a CSV file
    governance_df.to_csv(refined_filename, index=False)

def refine_and_filter_governance():
    process()
