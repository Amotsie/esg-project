import os
import spacy
import re
import pandas as pd
from clean_kip import extract_dynamic_associations
# from grammar import check_and_correct_grammar
from country_names import extract_details_from_txt
from dbqueries import (insert_company,fetch_all_companies,insert_indicator)



def identify_social_indicators(text, social_keywords):
    """Identify social indicators, their metrics, and associated units from text."""
    doc = nlp(text)
    
    social_indicators = []
    latest_year = None
    for sentence in doc.sents:
        for keyword in social_keywords:
            if keyword.lower() in sentence.text.lower():
                matches = re.findall(
                    r'\b(\d+(\.\d+)?)\s*(?:full time equivalent employees|employees|hours|days|years|per\s+capita|per\s+employee|per\s+annum|per\s+year|per\s+month|per\s+quarter|per\s+week|per\s+day)?\b',
                    sentence.text,
                    re.IGNORECASE
                )
                for match in matches:
                    metric_value, metric_unit = match
                    # Extracting the latest year from the sentence
                    years = re.findall(r'\b(\d{4})\b', sentence.text)
                    if years:
                        latest_year = max(int(year) for year in years)
                    social_indicators.append((keyword, sentence.text, metric_value, metric_unit, latest_year))
                    break  # Once a keyword is found, move to the next sentence
    return social_indicators

# Define social keywords
social_keywords = [
    "labour", "employee profile", "employee tenure", "employee diversity", "supplier", 
    "occupational health & safety", "employees", "customers", "training", "employment equity", 
    "community", "learning and development", "health and safety", "corporate social responsibility", 
    "social capital", "human capital", "our people", "human resource management", "social impact", 
    "labour standards", "human rights", "community development", "customer responsibility", 
    "employment", "training and education", "product safety", "quality assurance", 
    "employee training", "development programs", "diversity", "operations", "talent development",
    "community investment", "financial inclusion", "supplier development", "social reporting",
    "labour practice", "human capital development", "talent attraction & retention", "access to basic services",
    "supply chain", "discrimination", "community relations", "management details", "demographics", "education", 
    "housing", 
]

# Initialize an empty list to store social indicators
social_indicators = []

# Load spaCy model outside the loop to avoid reloading it for each file
nlp = spacy.load("en_core_web_sm")
nlp.max_length = 5000000 

def process():
    folder_path = "./uploads"
    text_files = [file for file in os.listdir(folder_path) if file.endswith('.txt')]
    
    # Ensure the directory exists before saving the file
    output_dir = './social'
    os.makedirs(output_dir, exist_ok=True)  # Create the directory if it does not exist
    
    # Extract social indicators from each document
    for text_file in text_files:
        text_path = os.path.join(folder_path, text_file)
        # counrty_output=extract_details_from_txt(text_path)
        # print("counrty_output ", counrty_output)
        metadata=text_file.split("-")
        with open(text_path, 'r', encoding='utf-8') as file:
            text = file.read()

        company_name=metadata[0]
        sector=metadata[1]
        region=metadata[2]
        country=metadata[3]
        year=metadata[4].split(".")[0]
        company_name = os.path.splitext(text_file)[0]  # Assuming file name is company name
        extracted_indicators = identify_social_indicators(text, social_keywords)
        social_indicators.extend([(company_name,sector,country,region,indicator[0], indicator[1], indicator[2], indicator[3], year) for indicator in extracted_indicators])

    # Create DataFrame from social indicators
    df_social_indicators = pd.DataFrame(social_indicators, columns=['Company Name','Sector','Country','Region', 'Indicator', 'Context', 'Metric', 'Metric Unit', 'year'])

    # Saving DataFrame to CSV file
    df_social_indicators.to_csv(os.path.join(output_dir, 'social_data_with_year.csv'), index=False)
    refine_matrix()

def refine_matrix():
    # Ensure the directory exists before saving the file
    output_dir = './social'
    os.makedirs(output_dir, exist_ok=True)

    # Read the CSV file
    df = pd.read_csv(os.path.join(output_dir, 'social_data_with_year.csv'))

    # Remove leading/trailing white spaces
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    df['Company Name']=df['Company Name'].str.capitalize()
    df['sector']=df['Sector'].str.capitalize()
    df['Country']=df['Country'].str.capitalize()
    df['Region']=df['Region'].str.capitalize()
    # Split multiline text into separate lines
    df['Context'] = df['Context'].str.replace('\n', ' ')

    # Capitalize text in Indicator columns
    df['Indicator'] = df['Indicator'].str.capitalize()

    # Rename columns
    df.rename(columns={'Context': 'KPI'}, inplace=True)
    df.rename(columns={'Metric': 'KPI Value'}, inplace=True)
    df.rename(columns={'Metric Unit': 'Unit'}, inplace=True)
    df.rename(columns={'Latest year': 'Year'}, inplace=True)

    # Writing cleaned data to a new CSV file
    df.to_csv(os.path.join(output_dir, 'london_social_metric.csv'), index=False)
    social_last_matrix()

def social_last_matrix():
    # Ensure the directory exists before saving the file
    output_dir = './social'
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Read the CSV file into a DataFrame
    df = pd.read_csv(os.path.join(output_dir, 'london_social_metric.csv'))

    # Step 2: Identify rows associated with the Social pillar
    social_keywords = ['males', 'females', 'social', 'community', 'labor', 'workforce', 'human rights', 'employee', 'policy', 'education', 'training', 'spend', 'injury', 'rate', 'fatalities']
    social_mask = df['KPI'].str.contains('|'.join(social_keywords), case=False)

    # Step 3: Remove rows associated with the Environment or Governance pillars
    environment_keywords = ['environment', 'carbon', 'emission', 'energy efficiency']
    governance_keywords = ['governance', 'board', 'regulation', 'compliance']
    environment_mask = df['KPI'].str.contains('|'.join(environment_keywords), case=False)
    governance_mask = df['KPI'].str.contains('|'.join(governance_keywords), case=False)

    # Combine masks to remove rows associated with Environment or Governance pillars
    remove_mask = environment_mask | governance_mask
    social_df = df[social_mask & ~remove_mask]
    
    for index, row in social_df.iterrows():
        # Apply the extract_dynamic_associations function to the 'KPI' column
        detail = extract_dynamic_associations(row['KPI'], row['Indicator'])
    
        if isinstance(detail, list):
            # Join list items with a comma
            social_df.at[index, 'KPI'] = ', '.join(detail)
        else:
            # If not a list, assign detail directly
            social_df.at[index, 'KPI'] = detail
    c_name=fetch_all_companies()
    # print(c_name)

    # Convert list of dictionaries to a set of company names for quick lookup
    # if row['Company Name'] not in {company["company_name"] for company in c_name}:
    #     c_id=insert_company(row['Company Name'], row['Sector'], row['Country'], row['Region'])
    #     i_id=insert_indicator(c_id, social_df['Indicator'],'SOCIAL')
    #     kpi_id=insert_kpi(i_id, social_df['KPI'],social_df['Unit'],social_df['KPI Value'])
    #     insert_year(kpi_id, social_df['Year'])
    # Save the final report to CSV
    social_df.to_csv(os.path.join(output_dir, 'social_report.csv'), index=False)

def refine_and_filter_social():
    process()
