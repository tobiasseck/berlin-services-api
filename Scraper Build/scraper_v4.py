import requests
from bs4 import BeautifulSoup
from sqlmodel import SQLModel, Field, create_engine, Session, select, Relationship
from tqdm import tqdm
from typing import List, Optional

class StandorteServices(SQLModel, table=True):
    standort_id: int = Field(foreign_key="standorte.id", primary_key=True)
    service_id: int = Field(foreign_key="service.id", primary_key=True)

class Service(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    service_name: str
    link: str
    can_be_done_online: bool = Field(default=False)  # New field for online processing
    standorte: List["Standorte"] = Relationship(back_populates="services", link_model=StandorteServices)

class ServiceDetail(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    service_id: int = Field(foreign_key="service.id")
    title: str
    description: str

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

class Formular(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    service_id: int = Field(foreign_key="service.id")
    title: str
    url: str


def create_db_and_tables(engine):
    SQLModel.metadata.create_all(engine)

def upsert_data(session, service_id, service_name, service_link, can_be_done_online):
    existing_service = session.get(Service, service_id)
    if existing_service:
        existing_service.service_name = service_name
        existing_service.link = service_link
        existing_service.can_be_done_online = can_be_done_online
        session.add(existing_service)
    else:
        new_service = Service(
            id=service_id,
            service_name=service_name,
            link=service_link,
            can_be_done_online=can_be_done_online
        )
        session.add(new_service)
    session.commit()

def upsert_service_detail(session, service_id, detail):
    existing_detail = session.exec(select(ServiceDetail).where(ServiceDetail.service_id == service_id)).first()
    if existing_detail:
        existing_detail.title = detail['title']
        existing_detail.description = detail['description']
        session.add(existing_detail)
    else:
        new_detail = ServiceDetail(
            service_id=service_id,
            title=detail['title'],
            description=detail['description']
        )
        session.add(new_detail)
    session.commit()

def upsert_formular(session, service_id, title, url):
    # Insert new formular record
    new_formular = Formular(service_id=service_id, title=title, url=url)
    session.add(new_formular)
    session.commit()

def scrape_service_detail(service_link):
    detail_url = f"{service_link}"
    
    response = requests.get(detail_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    title = soup.find('h1', class_='title').text.strip()

    # Capture content from the specific div until the "Für Sie zuständig" section
    content_div = soup.find('div', id='layout-grid__area--maincontent', class_='servicedetail-view')
    if content_div:
        description_parts = []
        for elem in content_div.children:
            if elem.name == 'h2' and 'Für Sie zuständig' in elem.text:
                break
            description_parts.append(str(elem))
        description = ''.join(description_parts)
    else:
        description = ""

    # Check if the service can be done online
    can_be_done_online = bool(soup.find('h2', id='Online-Abwicklung'))

    # Extract forms if present
    formular_section = soup.find('h2', class_='title', string='Formulare')
    if formular_section:
        formular_list = formular_section.find_next('ul', class_='list-clean')
        if formular_list:
            formular_links = formular_list.find_all('a')
            formulars = [{'title': link.text.strip(), 'url': link['href']} for link in formular_links]
        else:
            formulars = []
    else:
        formulars = []

    details = {
        'title': title,
        'description': description,
    }

    return details, can_be_done_online, formulars

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

                # Scrape service details and online status
                service_detail, can_be_done_online, formulars = scrape_service_detail(service_link)
                
                upsert_data(session, service_id, service_name, service_link, can_be_done_online)
                upsert_service_detail(session, service_id, service_detail)

                # Insert any found forms into the database
                for formular in formulars:
                    upsert_formular(session, service_id, formular['title'], formular['url'])

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

    # Extract the offered services and link them
    service_relations = []
    services_section = soup.find('form', class_='location_servicelist_checkboxgroup')
    if services_section:
        service_inputs = services_section.find_all('input', {'name': 'anliegen[]'})
        for service_input in service_inputs:
            try:
                service_id = int(service_input['value'])
                service_relations.append(service_id)
            except ValueError:
                continue  # Skip this input if it doesn't contain a valid service ID
    
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

if __name__ == "__main__":
    scrape_services()
    print("Data has been successfully scraped and stored in the database.")
    scrape_standorte()
    print("Standorte data has been successfully scraped and stored in the database.")