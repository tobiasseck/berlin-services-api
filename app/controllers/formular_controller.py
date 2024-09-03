from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from ..models import Formular, engine
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/api/formulare/")
def get_formulare(search: str = Query("")):
    with Session(engine) as session:
        query = select(Formular)
        if search:
            query = query.where(Formular.title.contains(search))
        formulare = session.exec(query).all()
        return formulare

@router.get("/api/formulare/{formular_id}")
async def formular_detail(request: Request, formular_id: int):
    with Session(engine) as session:
        formular = session.exec(select(Formular).where(Formular.id == formular_id).options(selectinload(Formular.service))).first()
        if not formular:
            raise HTTPException(status_code=404, detail="Formular not found")
    return templates.TemplateResponse("formular_detail.html", {"request": request, "formular": formular})
