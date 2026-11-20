from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import router
from app.config import settings
from app.db import SessionLocal, engine
from app.models import Base
from app.seed_data import ensure_seed_course


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        Base.metadata.create_all(engine)
    if settings.auto_seed_course:
        with SessionLocal() as db:
            ensure_seed_course(db)
    yield


app = FastAPI(title="Adaptive Learning Platform API", version="1.0.0", lifespan=lifespan)
app.include_router(router, prefix="/api/v1")
app.mount("/ui", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="ui")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/ui/")
