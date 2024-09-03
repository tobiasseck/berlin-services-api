import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.controllers import service_controller, standorte_controller, formular_controller
from app.views import service_view, standorte_view, formular_view

app = FastAPI()

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

app.include_router(service_controller.router)
app.include_router(standorte_controller.router)
app.include_router(formular_controller.router)

app.include_router(service_view.router)
app.include_router(standorte_view.router)
app.include_router(formular_view.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Service App. Access the frontend at /services/, /standorte/, /formulare/"}
