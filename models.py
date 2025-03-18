from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean,DECIMAL
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import uuid

sqlite_string = "sqlite+pysqlite:///esg.db"

engine = create_engine(sqlite_string, echo=True)

Session = sessionmaker(bind=engine)
db_session = Session()

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class Company(Base):
    __tablename__ = 'companies'
    
    company_id = Column(String, primary_key=True, default=generate_uuid)
    company_name = Column(String(255), nullable=False)
    country = Column(String(255), nullable=False)
    region = Column(String(255))
    sector = Column(String(255))
    
    indicators = relationship('Indicator', back_populates='company', cascade="all, delete-orphan")
    
    def __init__(self, company_name, country, sector, region):
        self.company_name = company_name
        self.country = country
        self.sector = sector
        self.region = region


class Indicator(Base):
    __tablename__ = 'indicators'
    
    indicator_id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey('companies.company_id', ondelete="CASCADE"), nullable=False)
    indicator_type = Column(String(255), nullable=False) # Environmental Social or Governance
    indicator = Column(String(255), nullable=False)
    KPI = Column(String(255), nullable=False)
    KPI_value = Column(DECIMAL(10, 2), nullable=True)
    unit = Column(String(255))
    year = Column(Integer)
    
    company = relationship('Company', back_populates='indicators')
    
    def __init__(self, company_id, indicator_type, indicator, KPI, KPI_value, unit, year):
        self.company_id = company_id
        self.indicator_type = indicator_type
        self.indicator = indicator
        self.KPI = KPI
        self.KPI_value = KPI_value
        self.unit = unit
        self.year = year


Base.metadata.create_all(engine)

#Populate database from CSV files

"""
import pandas as pd

df = pd.read_csv('social.csv')

i_type = "Social"
yyy = '2021'

# Iterate over the DataFrame and insert data into the database
for index, row in df.iterrows():
    print("===================================================================")
    print(row)
    print("===================================================================")

    string_number = row[yyy]
    float_number = None

    if not string_number:
        float_number = None
    else:
        try:
            float_number = float(string_number)
        except:
            float_number = None

    company = db_session.query(Company).filter(Company.company_name == row['Company']).first()
    if not company:
        company = Company(
            company_name=row['Company'],
            country=row['Country'],
            region=row['Region'],
            sector=row['Sector']
        )
        db_session.add(company)
        db_session.commit()  # Commit to get the generated company_id

    indicator = Indicator(
        company_id=company.company_id,
        indicator=row['Indicator'],
        KPI=row['KPI'],
        KPI_value= float_number,
        unit=row['Unit'],
        indicator_type=i_type,
        year=yyy
    )
    db_session.add(indicator)
    if index == 150:
        print("=================== 150 Records inserted ===============")
        break  # Exit the loop when number is 3

# Commit the session to save all changes
db_session.commit()

"""

arr = [(
        'f6c67444-24d0-4cb2-9ae4-e5fd78684b3c',
        'ABInBev', 'South Africa', 'Africa', 
        'Consumer Defensive',
        '7b181fda-36da-4648-88e6-c20ff000366a',
        2023,
        'Environmental', 
        'Emissions',
        'Total Scope 1 and 2 emissions', 
        3390000,
        'tCO2e'
        ), ('f6c67444-24d0-4cb2-9ae4-e5fd78684b3c', 'ABInBev', 'South Africa', 'Africa', 'Consumer Defensive', '02a819e5-e23b-4d4b-91d0-c2c142612a76', 2023, 'Environmental', 'Emissions', 'Total carbon emissions', 25770000, 'tCO2e'), ('f6c67444-24d0-4cb2-9ae4-e5fd78684b3c', 'ABInBev', 'South Africa', 'Africa', 'Consumer Defensive', '418c2de2-eb97-485a-bc5e-c06c426a4cb8', 2023, 'Environmental', 'Emissions', 'Scope 3 emissions', 22.38, 'tCO2e'), ('f6c67444-24d0-4cb2-9ae4-e5fd78684b3c', 'ABInBev', 'South Africa', 'Africa', 'Consumer Defensive', '5049d658-b19b-4dac-85c5-dbbc12e4643a', 2023, 'Environmental', 'Emissions', 'Scopes 1 and GHG emissions per hectoliter of production', 4.46, 'kg CO2e/hl')]