import pandas as pd
from sqlmodel import create_engine, Session
from scraper_v3 import Service, ServiceDetail, Standorte, StandorteServices, Behoerde  # Adjust the import based on where your models are defined

def export_db_to_excel(db_url="sqlite:///services.db", excel_file="services_export.xlsx"):
    # Connect to the database
    engine = create_engine(db_url)

    with Session(engine) as session:
        # Query all tables and convert to pandas DataFrames
        services_df = pd.read_sql(session.query(Service).statement, session.bind)
        service_details_df = pd.read_sql(session.query(ServiceDetail).statement, session.bind)
        standorte_df = pd.read_sql(session.query(Standorte).statement, session.bind)
        standorte_services_df = pd.read_sql(session.query(StandorteServices).statement, session.bind)
        behoerde_df = pd.read_sql(session.query(Behoerde).statement, session.bind)

        # Write the DataFrames to an Excel file, each DataFrame as a separate sheet
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            services_df.to_excel(writer, sheet_name='Services', index=False)
            service_details_df.to_excel(writer, sheet_name='ServiceDetails', index=False)
            standorte_df.to_excel(writer, sheet_name='Standorte', index=False)
            standorte_services_df.to_excel(writer, sheet_name='StandorteServices', index=False)
            behoerde_df.to_excel(writer, sheet_name='Behoerde', index=False)

    print(f"Database exported to {excel_file} successfully.")

if __name__ == "__main__":
    export_db_to_excel()
