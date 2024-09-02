import pandas as pd
from sqlmodel import create_engine, Session, select
from scraper_v2 import Service, ServiceDetail, Standorte

def display_services():
    engine = create_engine('sqlite:///services.db')
    
    with Session(engine) as session:
        services = session.exec(select(Service)).all()
        service_details = session.exec(select(ServiceDetail)).all()
        standorte = session.exec(select(Standorte)).all()
        
        services_df = pd.DataFrame([service.dict() for service in services])
        service_details_df = pd.DataFrame([detail.dict() for detail in service_details])
        standorte_df = pd.DataFrame([standort.dict() for standort in standorte])
        
        print("Services:")
        print(services_df)
        print("\nService Details:")
        print(service_details_df)
        print("\nStandorte:")
        print(standorte_df)

if __name__ == "__main__":
    display_services()