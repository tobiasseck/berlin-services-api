from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from ..models import Standorte, engine
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/api/standorte/")
def get_standorte(search: str = Query("")):
    with Session(engine) as session:
        query = select(Standorte)
        if search:
            query = query.where(Standorte.name.contains(search))
        standorte = session.exec(query).all()
        return standorte

@router.get("/api/standorte/{standort_id}")
async def standort_detail(request: Request, standort_id: int):
    with Session(engine) as session:
        standort = session.exec(select(Standorte).where(Standorte.id == standort_id).options(selectinload(Standorte.services))).first()
        if not standort:
            raise HTTPException(status_code=404, detail="Standort not found")
    return templates.TemplateResponse("standort_detail.html", {"request": request, "standort": standort})
