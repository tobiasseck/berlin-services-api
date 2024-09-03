from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..models import Formular, engine

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/formulare/")
async def formulare(request: Request):
    with Session(engine) as session:
        formulare = session.exec(select(Formular)).all()
    return templates.TemplateResponse("formulare.html", {"request": request, "formulare": formulare})

@router.get("/formulare/{formular_id}")
def formular_detail(request: Request, formular_id: int):
    with Session(engine) as session:
        formular = session.get(Formular, formular_id)
        if not formular:
            raise HTTPException(status_code=404, detail="Formular not found")
        return templates.TemplateResponse("formular_detail.html", {"request": request, "formular": formular})

