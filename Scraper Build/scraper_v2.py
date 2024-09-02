import requests
from bs4 import BeautifulSoup
from sqlmodel import SQLModel, Field, create_engine, Session, select, Relationship
from tqdm import tqdm
from typing import List, Optional

class Behoerde(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    address: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    services: List["ServiceDetail"] = Relationship(back_populates="behoerde")

class Service(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    service_name: str
    link: str

class ServiceDetail(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    service_id: int = Field(foreign_key="service.id")
    title: str
    description: Optional[str] = None
    voraussetzungen: Optional[str] = None
    unterlagen: Optional[str] = None
    behoerde_id: Optional[int] = Field(default=None, foreign_key="behoerde.id")
    behoerde: Optional[Behoerde] = Relationship(back_populates="services")

class Standorte(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
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

def upsert_service_detail(session, service_id, detail):
    existing_detail = session.exec(select(ServiceDetail).where(ServiceDetail.service_id == service_id)).first()
    if existing_detail:
        existing_detail.title = detail['title']
        existing_detail.description = detail['description']
        existing_detail.voraussetzungen = detail.get('Voraussetzungen')
        existing_detail.unterlagen = detail.get('Erforderliche Unterlagen')
        session.add(existing_detail)
    else:
        new_detail = ServiceDetail(
            service_id=service_id,
            title=detail['title'],
            description=detail['description'],
            voraussetzungen=detail.get('Voraussetzungen'),
            unterlagen=detail.get('Erforderliche Unterlagen'),
            behoerde_id=detail.get('behoerde_id')
        )
        session.add(new_detail)
    session.commit()

def scrape_service_detail(service_link):
    # Ensure the URL is correctly formed
    detail_url = f"{service_link}"
    
    response = requests.get(detail_url)
    response.raise_for_status()  # This will raise an HTTPError for bad responses

    soup = BeautifulSoup(response.text, 'html.parser')

    title = soup.find('h1', class_='title').text.strip()
    description = soup.find('div', class_='block').text.strip()

    details = {
        'title': title,
        'description': description,
    }

    for block in soup.find_all('div', class_='block'):
        header = block.find('h2')
        if header:
            header_text = header.text.strip()
            content = block.get_text(strip=True)
            if header_text in ["Voraussetzungen", "Erforderliche Unterlagen"]:
                details[header_text] = content

    return details


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

                # Scrape service details and save them
                service_detail = scrape_service_detail(service_link)
                upsert_service_detail(session, service_id, service_detail)

def upsert_standorte_data(session, standort_id, name, link):
    existing_standort = session.get(Standorte, standort_id)
    if existing_standort:
        existing_standort.name = name
        existing_standort.link = link
        session.add(existing_standort)
    else:
        new_standort = Standorte(id=standort_id, name=name, link=link)
        session.add(new_standort)
    session.commit()

def scrape_standorte():
    url = 'https://service.berlin.de/standorte/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    engine = create_engine('sqlite:///services.db')
    create_db_and_tables(engine)
    
    with Session(engine) as session:
        standorte_sections = soup.find_all('div', class_='azlist-letter')
        
        for section in tqdm(standorte_sections, desc="Scraping Standorte Sections"):
            h2_tag = section.find('h2', class_='letter')
            if h2_tag:
                h2_text = h2_tag.text.strip()
                standorte_items = section.find_next('ul').find_all('li')
                
                for item in tqdm(standorte_items, desc=f"Processing {h2_text}", leave=False):
                    link_tag = item.find('a')
                    if link_tag:
                        standort_link = link_tag['href']
                        standort_name = link_tag.text.strip()
                        standort_id = int(standort_link.split('/')[-2])
                        full_link = f"https://service.berlin.de{standort_link}"
                        
                        upsert_standorte_data(session, standort_id, standort_name, full_link)

def fetch_all_services():
    engine = create_engine('sqlite:///services.db')
    
    with Session(engine) as session:
        services = session.exec(select(Service)).all()
        for service in services:
            print(service)

if __name__ == "__main__":
    scrape_services()
    print("Data has been successfully scraped and stored in the database.")
    scrape_standorte()
    print("Standorte data has been successfully scraped and stored in the database.") 
