from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter

from discord import discord

import logging
import uvicorn




@asynccontextmanager
async def lifespan(_: FastAPI):
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

api_router.include_router(
    prefix="/api/v1"
)
