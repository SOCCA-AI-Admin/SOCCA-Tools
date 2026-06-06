from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.hotel_routes import router

app = FastAPI(title="Hotel-Bildbearbeitung SOCCA")
app.include_router(router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
