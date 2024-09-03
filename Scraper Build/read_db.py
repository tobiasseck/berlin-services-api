import pandas as pd
from sqlmodel import create_engine, Session, select
from scraper_v4 import Service, ServiceDetail, Standorte, StandorteServices, Formular

def display_services():
    engine = create_engine('sqlite:///services.db')
    
    with Session(engine) as session:
        # Fetch all services
        services = session.exec(select(Service)).all()
        services_df = pd.DataFrame([service.dict() for service in services])
        
        # Fetch all service details
        service_details = session.exec(select(ServiceDetail)).all()
        service_details_df = pd.DataFrame([detail.dict() for detail in service_details])
        
        # Fetch all formulare
        formulare = session.exec(select(Formular)).all()
        formulare_df = pd.DataFrame([formular.dict() for formular in formulare])

        # Fetch all standorte
        standorte = session.exec(select(Standorte)).all()
        standorte_df = pd.DataFrame([standort.dict() for standort in standorte])

        # Fetch the relationships between standorte and services
        standorte_services = session.exec(select(StandorteServices)).all()
        standorte_services_df = pd.DataFrame([{
            'standort_id': rel.standort_id,
            'service_id': rel.service_id
        } for rel in standorte_services])

        print("Services:")
        print(services_df)
        print("\nService Details:")
        print(service_details_df)
        print("\nFormulare:")
        print(formulare_df)
        print("\nStandorte:")
        print(standorte_df)
        print("\nStandorte-Services Relationships:")
        print(standorte_services_df)

if __name__ == "__main__":
    display_services()