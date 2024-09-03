from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from ..models import Service, engine
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/api/services/")
def get_services(search: str = Query(""), can_be_done_online: bool = Query("")):
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
        service = session.exec(select(Service).where(Service.id == service_id).options(selectinload(Service.standorte))).first()
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
    return templates.TemplateResponse("service_detail.html", {"request": request, "service": service})

