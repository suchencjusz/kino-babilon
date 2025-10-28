import os
import secrets

import aiohttp
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi_discord import Unauthorized
from sqlmodel import Session

from models import User as UserModel

from routes.deps import get_current_user

from crud.user import create_user, get_user_by_discord_id, update_user
from db import get_session
from discord import discord

router = APIRouter()


# test route za tokenem
@router.get("/me")
async def my_profile(
    current_user: UserModel = Depends(get_current_user)):
    
    return {
        "uid": current_user.uid,
        "discord_id": current_user.discord_id,
        "nickname": current_user.nickname,
        "permission_level": current_user.permission_level,
    }