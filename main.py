from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from app.db_setup import init_db
from contextlib import asynccontextmanager
from app import v1_router
from app.middlewares import log_middleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware

from app.logging.logger import logger
# Funktion som körs när vi startar FastAPI -
# perfekt ställe att skapa en uppkoppling till en databas
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db() # Vi ska skapa denna funktion
    yield

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://192.168.56.1:5173/",
    "http://192.168.1.186:5173/",
    "https://fascinating-lollipop-4279f7.netlify.app"
]
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(BaseHTTPMiddleware, dispatch=log_middleware)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(v1_router, prefix="/v1")