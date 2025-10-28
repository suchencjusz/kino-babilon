import os
import secrets

import aiohttp
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi_discord import Unauthorized
from sqlmodel import Session

from crud.user import create_user, get_user_by_discord_id, update_user
from db import get_session
from discord import discord

router = APIRouter()


# @router.get("/user")