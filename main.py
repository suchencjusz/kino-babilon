import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

if os.path.exists(".env"):
    from dotenv import load_dotenv  # noqa F811

    load_dotenv()

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import create_db_and_tables
from discord import discord
from routes.auth import router as auth_router
from routes.permissions import router as permissions_router
from routes.screenings import router as screenings_router
from routes.users import router as users_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()

    await discord.init()
    yield


app = FastAPI(lifespan=lifespan)


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
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(screenings_router, prefix="/screenings", tags=["screenings"])
app.include_router(permissions_router, prefix="/permissions", tags=["permissions"])
