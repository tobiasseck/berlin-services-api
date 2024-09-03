from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from ..models import Standorte, engine

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/standorte/")
async def standorte(request: Request):
    with Session(engine) as session:
        standorte = session.exec(
            select(Standorte).options(joinedload(Standorte.services))
        ).unique().all()
    return templates.TemplateResponse("standorte.html", {"request": request, "standorte": standorte})

@router.get("/standorte/{standort_id}")
def standort_detail(request: Request, standort_id: int):
    with Session(engine) as session:
        standort = session.get(Standorte, standort_id)
        if not standort:
            raise HTTPException(status_code=404, detail="Standort not found")
        return templates.TemplateResponse("standort_detail.html", {"request": request, "standort": standort})
