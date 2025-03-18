from flask import Flask, request, render_template, jsonify,send_file,send_from_directory,abort
import os
import zipfile
import io
import re
import base64
import pandas as pd
from environment import refine_environment_data
from governance_matrix import refine_and_filter_governance
from social import refine_and_filter_social
import os
import base64
import os
import pandas as pd
from flask import Flask, render_template, request, jsonify
import shutil
import base64
import fitz  # PyMuPDF
from models import db_session, Company, Indicator
from dbqueries import fetch_all_companies
from sqlalchemy import text
from sqlalchemy.orm import joinedload

app = Flask(__name__)

def sanitize_filename(filename):
    """Sanitize the filename to avoid issues with special characters."""
    return re.sub(r'[<>:"/\\|?*\x00-\x1F\xa0]', "_", filename)


@app.route('/',methods=["GET","POST"])
def index():
    # companies = fetch_all_companies()
    companies = db_session.query(Company).options(joinedload(Company.indicators)).all()
    return render_template('index.html', companies=companies)


def find_sector_info(text):
    # Look for sector-related keywords
    sector_keywords = [
        "sector", "industry", "business segment", "market", "business division", 
        "industry classification", "primary sector", "economic sector", "business category",
        "commercial sector", "trade", "line of business", "operates in", "specializes in",
        "focuses on", "engaged in", "active in", "provides services in", "manufactures",
        "sells to", "clients in", "customers in", "target market", "market segment", 
        "industry sector", "core business", "market focus", "industry vertical", 
        "business area", "geographic segment", "customer segment", "operational segment",
        "NAICS code", "SIC code", "ISIC code", "GICS sector", "NACE classification",
        "listed under", "traded as", "investment category", "market capitalization sector",
        "portfolio sector", "revenue stream", "ESG sector", "sustainability focus", 
        "impact industry", "green economy sector", "peer group", "competes in",
        "market competition", "industry benchmark", "compares with", "segment", "vertical", 
        "domain", "field", "area of operation", "business unit", "division", 
        "product category", "service category", "operational focus"
    ]
    
    for keyword in sector_keywords:
        match = re.search(rf"{keyword}[:\s]+([\w\s,-]+)", text, re.IGNORECASE)
        if match:
            return match.group(1)  # Extract sector info
    
    return "Sector not found"


UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if os.path.exists(UPLOAD_FOLDER):
    shutil.rmtree(UPLOAD_FOLDER)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        responses = []
        files = request.files.getlist('files')
     
        for file in files:
            file_name = file.filename  # Extract filename 
            file_name = re.sub(r"^[^/]+/", "", file_name) # Remove folder name
            metadata = file_name.split('-')
            company_name = metadata[0].replace("_", " ")
            sector = metadata[1]
            region = metadata[2]
            country = metadata[3]
            year, file_extension = metadata[4].split(".")

            result_company = db_session.query(Company).filter_by(company_name=company_name).first()
            # if not result_company:
            #     result_company = Company(company_name, country, sector, region)
            #     db_session.add(result_company)
            #     db_session.commit()
    
            sanitized_file_name = sanitize_filename(file_name)

            if file_extension == "txt":
                try:
                     # Read and save the TXT file
                    txt_content = file.read().decode('utf-8')

                    txt_save_path = os.path.join(UPLOAD_FOLDER, sanitized_file_name)

                    # Ensure unique filename
                    unique_suffix = 1
                    while os.path.exists(txt_save_path):
                        txt_save_path = os.path.join(UPLOAD_FOLDER, f"{sanitized_file_name}_{unique_suffix}.txt")
                        unique_suffix += 1

                    with open(txt_save_path, 'w', encoding='utf-8') as txt_file:
                        txt_file.write(txt_content)

                    responses.append({
                         'message': f'Successfully saved {file_name}',
                        'txt_file_path': txt_save_path
                    })

                except Exception as e:
                    app.logger.error(f"Error saving .txt file {file_name}: {str(e)}")
                    responses.append({
                        'message': f'Failed to save {file_name}: {str(e)}',
                        'txt_file_path': None
                    })

            elif file_extension == "pdf":
                try:
                    # Save the uploaded PDF temporarily
                    pdf_save_path = os.path.join(UPLOAD_FOLDER, sanitized_file_name)
                    file.save(pdf_save_path)

                    # Extract text from the PDF
                    text = extract_text_from_pdf(pdf_save_path)

                    # Ensure a valid filename
                    txt_file_name = f"{os.path.splitext(sanitized_file_name)[0]}.txt"
                    txt_save_path = os.path.join(UPLOAD_FOLDER, txt_file_name)
                
                    # Ensure unique filename
                    unique_suffix = 1
                    while os.path.exists(txt_save_path):
                        txt_save_path = os.path.join(UPLOAD_FOLDER, f"{txt_file_name}_{unique_suffix}.txt")
                        unique_suffix += 1

                    # Save extracted text to the .txt file
                    with open(txt_save_path, 'w', encoding='utf-8') as txt_file:
                        txt_file.write(text)

                    # Remove the original PDF after extracting text
                    os.remove(pdf_save_path)

                    responses.append({
                        'message': f'Successfully converted {file_name} to {txt_file_name}',
                        'txt_file_path': txt_save_path
                    })
                    refine_environment_data()
                    refine_and_filter_governance()
                    refine_and_filter_social()
                except Exception as e:
                    app.logger.error(f"Error processing PDF {file_name}: {str(e)}")
                    responses.append({
                        'message': f'Failed to process {file_name}: {str(e)}',
                        'txt_file_path': None
                    })

            else:
                responses.append({
                    'message': f'Unsupported file format: {file_name}',
                    'txt_file_path': None
                })

        else:
            responses.append({
                'message': f'Failed to upload file: no data provided',
                'txt_file_path': None
            })
            refine_environment_data()
            refine_and_filter_governance()
            refine_and_filter_social()
        return jsonify({'responses': responses}), 200
    except Exception as e:
        app.logger.error(f"Error during file upload: {str(e)}")
        return jsonify({'error': 'An error occurred during upload processing.', 'details': str(e)}), 500


def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    text = ""
    try:
        with fitz.open(pdf_path) as pdf_document:
            for page in pdf_document:
                text += page.get_text("text") + "\n"
    except Exception as e:
        text = f"Error extracting text: {str(e)}"
    
    return text if text.strip() else "No readable text found."


@app.route('/download-uploads', methods=['GET'])
def download_uploads():
    # Create an in-memory ZIP file of the uploads folder
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Walk through the uploads directory and add files to the ZIP
        for root, _, files in os.walk(app.config['UPLOAD_FOLDER']):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, os.path.relpath(file_path, app.config['UPLOAD_FOLDER']))

    # Seek to the start of the BytesIO buffer for reading
    zip_buffer.seek(0)

    # Send the ZIP file as a downloadable response
    return send_file(zip_buffer, as_attachment=True, download_name='uploads.zip', mimetype='application/zip')




@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    ROOT_FOLDER = "./"
    app.config['UPLOAD_FOLDER'] = ROOT_FOLDER
    # Split filename into directory and file for safety
    subdirectory, file = os.path.split(filename)

    # Define allowed files with relative paths for security
    allowed_files = {
        "social_report.csv": "social",
        "governance_report.csv": "governance",
        "environment_data.csv": "environment"
    }

    # Check if the requested file is in the allowed files
    if file in allowed_files and allowed_files[file] == subdirectory:
        # Get the full directory path based on subdirectory
        directory = os.path.join(app.config['UPLOAD_FOLDER'], allowed_files[file])

        # Send the file from the correct directory
        return send_from_directory(directory, file, as_attachment=True)
    else:
        # Return 404 if file not allowed or not found
        return abort(404)
    
@app.route('/environment', methods=['GET'])       
def environment():

    sql = text("""
        SELECT c.company_id, c.company_name, c.country, c.region, c.sector, 
               i.indicator_id, i.year, i.indicator_type, i.indicator, 
               i.KPI, i.KPI_value, i.unit
        FROM companies c
        JOIN indicators i ON c.company_id = i.company_id
        WHERE i.indicator_type = 'Environmental'
    """)

    db_rows = db_session.execute(sql).fetchall()
    
    result_dict = format_api_output(db_rows) 

    return jsonify(list(result_dict.values()))

@app.route('/social', methods=['GET'])       
def social():
    # Query companies with indicators of type "Social"
    sql = text("""
            SELECT c.company_id, c.company_name, c.country, c.region, c.sector, 
                i.indicator_id, i.year, i.indicator_type, i.indicator, 
                i.KPI, i.KPI_value, i.unit
            FROM companies c
            JOIN indicators i ON c.company_id = i.company_id
            WHERE i.indicator_type = 'Social'
        """)

    db_rows = db_session.execute(sql).fetchall()
    
    result_dict = format_api_output(db_rows) 

    return jsonify(list(result_dict.values()))


@app.route('/governance', methods=['GET'])       
def governance():
    # Query companies with indicators of type "Governance"
    sql = text("""
            SELECT c.company_id, c.company_name, c.country, c.region, c.sector, 
                i.indicator_id, i.year, i.indicator_type, i.indicator, 
                i.KPI, i.KPI_value, i.unit
            FROM companies c
            JOIN indicators i ON c.company_id = i.company_id
            WHERE i.indicator_type = 'Governance'
        """)

    db_rows = db_session.execute(sql).fetchall()
    
    result_dict = format_api_output(db_rows) 

    return jsonify(list(result_dict.values()))


def format_api_output(db_rows):
    companies = {}
    for row in db_rows:
        company_id = row.company_id

        # Ensure company exists in dictionary
        if company_id not in companies:
            companies[company_id] = {
                "company_id": row.company_id,
                "company_name": row.company_name,
                "country": row.country,
                "region": row.region,
                "sector": row.sector,
                "indicators": []
            }

        # Append indicator to the company's list
        companies[company_id]["indicators"].append({
            "indicator_id": row.indicator_id,
            "year": int(row.year) if row.year is not None else None,
            "indicator_type": row.indicator_type,
            "indicator": row.indicator,
            "KPI": row.KPI,
            "KPI_value": float(row.KPI_value) if row.KPI_value is not None else None,
            "unit": row.unit
        })
    return companies

if __name__ == '__main__':
    app.run(debug=True)
