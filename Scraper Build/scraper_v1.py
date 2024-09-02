import requests
from bs4 import BeautifulSoup
from sqlmodel import SQLModel, Field, create_engine, Session, select
from tqdm import tqdm

class Service(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    service_name: str
    link: str

def create_db_and_tables(engine):
    SQLModel.metadata.create_all(engine)

def upsert_data(session, service_id, service_name, service_link):
    existing_service = session.get(Service, service_id)
    if existing_service:
        existing_service.service_name = service_name
        existing_service.link = service_link
        session.add(existing_service)
    else:
        new_service = Service(id=service_id, service_name=service_name, link=service_link)
        session.add(new_service)
    session.commit()

def scrape_services():
    url = 'https://service.berlin.de/dienstleistungen/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    engine = create_engine('sqlite:///services.db')
    create_db_and_tables(engine)
    
    with Session(engine) as session:
        letter_sections = soup.find_all('div', class_='azlist-letter')
        
        for letter_section in tqdm(letter_sections, desc="Scraping Sections"):
            services = letter_section.find_next('ul').find_all('li')
            
            for service in tqdm(services, desc=f"Processing {letter_section.find('h2').text}", leave=False):
                service_link = service.find('a')['href']
                service_name = service.find('a').text.strip()
                service_id = int(service_link.split('/')[-2])

                upsert_data(session, service_id, service_name, service_link)

def fetch_all_services():
    engine = create_engine('sqlite:///services.db')
    
    with Session(engine) as session:
        services = session.exec(select(Service)).all()
        for service in services:
            print(service)
              
if __name__ == "__main__":
    scrape_services()
    print("Data has been successfully scraped and stored in the database.")
    # print("\n")
    # fetch_all_services()  
