from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter

from discord import discord
from db import get_session, create_db_and_tables
from routes.auth import router as auth_router

import logging


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()

    await discord.init()
    yield


app = FastAPI(lifespan=lifespan)
api_router = APIRouter()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])

