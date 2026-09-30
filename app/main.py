from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import models  # noqa: F401  (registers tables)
from .database import Base, engine
from .routes import router


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="MoveMap",
    description="Your week of training, cardio and recovery, mapped out.",
    version="1.0.0",
    lifespan=lifespan,
)
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).resolve().parent.parent / "static")),
    name="static",
)
app.include_router(router)
