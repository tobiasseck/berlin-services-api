from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from ..models import Service, engine

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/services/")
async def services(request: Request, search: str = "", can_be_done_online: bool = None):
    with Session(engine) as session:
        query = select(Service).options(joinedload(Service.standorte))
        
        if search:
            query = query.where(Service.service_name.contains(search))
        
        if can_be_done_online is not None:
            query = query.where(Service.can_be_done_online == can_be_done_online)
        
        services = session.exec(query).unique().all()
    
    return templates.TemplateResponse("services.html", {"request": request, "services": services, "search": search, "can_be_done_online": can_be_done_online})

@router.get("/services/{service_id}")
def service_detail(request: Request, service_id: int):
    with Session(engine) as session:
        service = session.get(Service, service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return templates.TemplateResponse("service_detail.html", {"request": request, "service": service})

