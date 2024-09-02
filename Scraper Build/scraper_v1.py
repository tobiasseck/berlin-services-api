import requests
from bs4 import BeautifulSoup
from sqlmodel import SQLModel, Field, create_engine, Session, select

class Service(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    service_name: str
    link: str

def create_db_and_tables(engine):
    SQLModel.metadata.create_all(engine)

def insert_data(session, service_id, service_name, service_link):
    service = Service(id=service_id, service_name=service_name, link=service_link)
    session.add(service)
    session.commit()

def scrape_services():
    url = 'https://service.berlin.de/dienstleistungen/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    engine = create_engine('sqlite:///services.db')
    create_db_and_tables(engine)
    
    with Session(engine) as session:
        for letter_section in soup.find_all('div', class_='azlist-letter'):
            for service in letter_section.find_next('ul').find_all('li'):
                service_link = service.find('a')['href']
                service_name = service.find('a').text.strip()
                service_id = int(service_link.split('/')[-2])

                insert_data(session, service_id, service_name, service_link)

if __name__ == "__main__":
    scrape_services()
    print("Data has been successfully scraped and stored in the database.")
