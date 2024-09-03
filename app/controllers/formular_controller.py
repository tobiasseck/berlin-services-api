from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session, select
from ..models import Formular, engine

router = APIRouter()

@router.get("/api/formulare/")
def get_formulare(search: str = Query("")):
    with Session(engine) as session:
        query = select(Formular)
        if search:
            query = query.where(Formular.title.contains(search))
        formulare = session.exec(query).all()
        return formulare

@router.get("/api/formulare/{formular_id}")
def get_formular(formular_id: int):
    with Session(engine) as session:
        formular = session.get(Formular, formular_id)
        if not formular:
            raise HTTPException(status_code=404, detail="Formular not found")
        return formular
