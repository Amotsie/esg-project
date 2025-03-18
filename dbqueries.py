from models import db_session, Company, Indicator
from sqlalchemy import text

def insert_company(company_name, sector, country, region):
    """Insert a new company record into the database and return its ID."""
    try:
        company = Company(
            company_name=company_name,
            country=country,
            region=region,
            sector=sector
        )
        db_session.add(company)
        db_session.commit()  # Commit to get the generated company_id

    except Exception as e:
        print(f"Error inserting company: {e}")
        return None

def fetch_all_companies():
    """Retrieve all company records including column names."""

    companies = db_session.query(Company).all() 

    result = [
        {
            "company_id": company.company_id,
            "company_name": company.company_name,
            "country": company.country,
            "region": company.region,
            "sector": company.sector
        }
        for company in companies
    ]
    return result


def fetch_all_environmental_data():
    """Retrieve all environmental records including column names."""

    sql = text("""
        SELECT c.company_id, c.company_name, c.country, c.region, c.sector, 
               i.indicator_id, i.year, i.indicator_type, i.indicator, 
               i.KPI, i.KPI_value, i.unit
        FROM companies c
        JOIN indicators i ON c.company_id = i.company_id
        WHERE i.indicator_type = 'Environmental'
    """)

    db_rows = db_session.execute(sql).fetchall()
    
    return db_rows


def insert_indicator(c_id, indicator, kpi, kpi_value, kpi_unit, i_type, year):
    """Insert a new company record into the database."""
    try:
        indicator = Indicator(
        company_id=c_id,
        indicator=indicator,
        KPI=kpi,
        KPI_value= kpi_value,
        unit=kpi_unit,
        indicator_type=i_type,
        year=year
        )
        db_session.add(indicator)
        db_session.commit()

    except Exception as e:
        print(f"Error inserting company: {e}")
