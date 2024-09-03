from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from ..models import Service, ServiceDetail, engine
from fastapi.templating import Jinja2Templates
import re

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def clean_description(description: str) -> str:
    unwanted_phrases = [
        "MAIN CONTENT",
        "Bitte wählen Sie zuerst einen Standort aus.",
        "Zu den verfügbaren Standorten",
        "An diesem Standort einen Termin buchen",
        "Download",
        "Seite als PDF herunterladen",
        "Chat",
        "Stellen Sie unserem Chatbot Bobbi Ihre Fragen.",
        "Stellen Sie unserem bot Bobbi Ihre Fragen.",
        "Jetzt mit Bobbi in 11 Sprachen chatten",
        "Für Sie zuständig",
        "Bitte wählen Sie für eine Terminvereinbarung einen Standort aus"
    ]

    for phrase in unwanted_phrases:
        description = description.replace(phrase, "")

    description = re.sub(r'<form[^>]*>.*?</form>', '', description, flags=re.DOTALL)
    
    cleaned_description = description.strip()
    
    return cleaned_description


@router.get("/api/services/")
def get_services(search: str = Query(""), can_be_done_online: bool = Query(None)):
    with Session(engine) as session:
        query = select(Service)
        if search:
            query = query.where(Service.service_name.contains(search))
        if can_be_done_online is not None:
            query = query.where(Service.can_be_done_online == can_be_done_online)
        services = session.exec(query).all()
        return services

@router.get("/api/services/{service_id}")
async def service_detail(request: Request, service_id: int):
    with Session(engine) as session:
        service = session.exec(select(Service).where(Service.id == service_id)).first()
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        service_detail = session.exec(select(ServiceDetail).where(ServiceDetail.service_id == service_id)).first()
        service_detail.description = clean_description(service_detail.description)
        return templates.TemplateResponse("service_detail.html", {"request": request, "service": service, "service_detail": service_detail})