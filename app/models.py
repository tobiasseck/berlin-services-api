from sqlmodel import SQLModel, Field, create_engine, Session, select, Relationship
from typing import List, Optional
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../Scraper Build/services.db")

class StandorteServices(SQLModel, table=True):
    standort_id: int = Field(foreign_key="standorte.id", primary_key=True)
    service_id: int = Field(foreign_key="service.id", primary_key=True)

class Service(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    service_name: str
    link: str
    can_be_done_online: bool = Field(default=False)
    standorte: List["Standorte"] = Relationship(back_populates="services", link_model=StandorteServices)
    formulars: Optional[List["Formular"]] = Relationship(back_populates="service")

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

class ServiceDetail(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    service_id: int = Field(foreign_key="service.id")
    title: str
    description: Optional[str] 

class Formular(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    service_id: int = Field(foreign_key="service.id")
    service: Optional[Service] = Relationship(back_populates="formulars")
    title: str
    url: str

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    hashed_password: str
    disabled: bool = False


engine = create_engine(f"sqlite:///{DB_PATH}")

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session    
