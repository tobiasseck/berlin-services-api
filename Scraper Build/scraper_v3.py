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

class ServiceDetail(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    service_id: int = Field(foreign_key="service.id")
    title: str
    description: Optional[str] = None
    voraussetzungen: Optional[str] = None
    unterlagen: Optional[str] = None
    behoerde_id: Optional[int] = Field(default=None, foreign_key="behoerde.id")
    behoerde: Optional[Behoerde] = Relationship(back_populates="services")

class StandorteServices(SQLModel, table=True):
    standort_id: int = Field(foreign_key="standorte.id", primary_key=True)
    service_id: int = Field(foreign_key="service.id", primary_key=True)

class Service(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    service_name: str
    link: str
    standorte: List["Standorte"] = Relationship(back_populates="services", link_model=StandorteServices)

class Standorte(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    link: str
    address: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    homepage: Optional[str] = None
    services: List[Service] = Relationship(back_populates="standorte", link_model=StandorteServices)


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

def upsert_standorte_data(session, standort_id, name, link, address=None, phone=None, fax=None, email=None, homepage=None):
    existing_standort = session.get(Standorte, standort_id)
    if existing_standort:
        existing_standort.name = name
        existing_standort.link = link
        existing_standort.address = address
        existing_standort.phone = phone
        existing_standort.fax = fax
        existing_standort.email = email
        existing_standort.homepage = homepage
        session.add(existing_standort)
    else:
        new_standort = Standorte(
            id=standort_id,
            name=name,
            link=link,
            address=address,
            phone=phone,
            fax=fax,
            email=email,
            homepage=homepage
        )
        session.add(new_standort)
    session.commit()

def scrape_standorte_details(standort_link, standort_id):
    detail_url = f"https://service.berlin.de{standort_link}"
    response = requests.get(detail_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the contact details
    contact_info = soup.find('div', class_='modul-contact')
    address, phone, fax, email, homepage = None, None, None, None, None
    
    if contact_info:
        address_tag = contact_info.find('li', class_='address loc')
        if address_tag:
            address = address_tag.get_text(strip=True)
        
        phone_tag = contact_info.find('li', class_='tel')
        if phone_tag:
            phone = phone_tag.get_text(strip=True).replace('Tel.:', '').strip()
        
        fax_tag = contact_info.find('li', class_='fax')
        if fax_tag:
            fax = fax_tag.get_text(strip=True).replace('Fax:', '').strip()

        email_tag = contact_info.find('li', class_='email')
        if email_tag:
            email = email_tag.find('a').get('href').replace('mailto:', '').strip()

        homepage_tag = contact_info.find('li', class_='homepage')
        if homepage_tag:
            homepage = homepage_tag.find('a').get('href').strip()

    # Extract the offered services
    service_relations = []
    services_section = soup.find('div', class_='modul-azlist')
    if services_section:
        service_links = services_section.find_all('a')
        for service_link in service_links:
            parts = service_link['href'].split('/')
            if len(parts) >= 3:
                try:
                    service_id = int(parts[-3])
                    service_relations.append(service_id)
                except ValueError:
                    continue  # Skip this link if it doesn't contain a valid service ID
    
    return address, phone, fax, email, homepage, service_relations

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

                        address, phone, fax, email, homepage, service_relations = scrape_standorte_details(standort_link, standort_id)
                        upsert_standorte_data(session, standort_id, standort_name, standort_link, address, phone, fax, email, homepage)

                        # Link services to this Standort
                        for service_id in service_relations:
                            link_service_to_standort(session, standort_id, service_id)


def link_service_to_standort(session, standort_id, service_id):
    # Check if the relationship already exists
    existing_link = session.exec(
        select(StandorteServices).where(
            StandorteServices.standort_id == standort_id,
            StandorteServices.service_id == service_id
        )
    ).first()

    if not existing_link:
        session.add(StandorteServices(standort_id=standort_id, service_id=service_id))
        session.commit()

if __name__ == "__main__":
    scrape_services()
    print("Data has been successfully scraped and stored in the database.")
    scrape_standorte()
    print("Standorte data has been successfully scraped and stored in the database.")