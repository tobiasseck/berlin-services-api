import typesense
from sqlmodel import create_engine, Session, select
from app.models import Service, Standorte, Formular

# Typesense client setup
client = typesense.Client({
    'nodes': [{
        'host': 'localhost',  # Replace with your Typesense server's host
        'port': '8108',  # Replace with your Typesense server's port
        'protocol': 'https'  # Use 'https' if your server uses SSL
    }],
    'api_key': 'xyz',  # Replace with your actual Typesense API key
    'connection_timeout_seconds': 2
})

# Database connection
engine = create_engine('sqlite:///services.db')

def setup_typesense():
    # Create schema for services
    service_schema = {
        'name': 'services',
        'fields': [
            {'name': 'service_name', 'type': 'string'},
            {'name': 'can_be_done_online', 'type': 'bool'},
        ]
    }

    # Create schema for standorte
    standorte_schema = {
        'name': 'standorte',
        'fields': [
            {'name': 'name', 'type': 'string'},
            {'name': 'address', 'type': 'string'},
        ]
    }

    # Create schema for formulare
    formular_schema = {
        'name': 'formulare',
        'fields': [
            {'name': 'title', 'type': 'string'},
            {'name': 'url', 'type': 'string'},
        ]
    }

    # Delete existing collections (if they exist)
    for schema in [service_schema, standorte_schema, formular_schema]:
        try:
            client.collections[schema['name']].delete()
        except Exception as e:
            print(f"Collection {schema['name']} not found or could not be deleted: {e}")

    # Create collections in Typesense
    client.collections.create(service_schema)
    client.collections.create(standorte_schema)
    client.collections.create(formular_schema)

def import_services_to_typesense():
    with Session(engine) as session:
        services = session.exec(select(Service)).all()
        for service in services:
            document = {
                'id': str(service.id),
                'service_name': service.service_name,
                'can_be_done_online': service.can_be_done_online,
            }
            client.collections['services'].documents.create(document)

def import_standorte_to_typesense():
    with Session(engine) as session:
        standorte = session.exec(select(Standorte)).all()
        for standort in standorte:
            document = {
                'id': str(standort.id),
                'name': standort.name,
                'address': standort.address or "",
            }
            client.collections['standorte'].documents.create(document)

def import_formulare_to_typesense():
    with Session(engine) as session:
        formulare = session.exec(select(Formular)).all()
        for formular in formulare:
            document = {
                'id': str(formular.id),
                'title': formular.title,
                'url': formular.url,
            }
            client.collections['formulare'].documents.create(document)

if __name__ == "__main__":
    setup_typesense()
    import_services_to_typesense()
    import_standorte_to_typesense()
    import_formulare_to_typesense()
    print("Typesense setup and data import completed successfully.")
