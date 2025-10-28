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


@router.get("/login")
async def login(response: Response):
    """Returns Discord OAuth login URL with CSRF protection"""

    state = secrets.token_urlsafe(32)

    response.set_cookie(
        key="oauth_state", value=state, max_age=600, httponly=True, samesite="lax"
    )

    return {"url": discord.get_oauth_login_url(state=state)}


@router.get("/callback")
async def callback(
    code: str,
    state: str,
) -> RedirectResponse:
    frontend_url = os.getenv("FRONTEND_REDIRECT_URL")
    payload = f"?code={code}&state={state}"

    return RedirectResponse(url=frontend_url + payload)


@router.get("/getuser")
async def get_user(
    code: str,
    state: str,
    oauth_state: str = Cookie(None),
    session: Session = Depends(get_session),
):
    """Discord OAuth callback - creates or updates user account automatically"""

    token, refresh_token = await discord.get_access_token(code)

    headers = {"Authorization": f"Bearer {token}"}

    async with aiohttp.ClientSession() as aio_session:
        async with aio_session.get(
            "https://discord.com/api/users/@me", headers=headers
        ) as response:
            if response.status != 200:
                raise HTTPException(
                    status_code=400, detail="Failed to fetch user from Discord"
                )
            discord_user_data = await response.json()

    db_user = get_user_by_discord_id(session, discord_user_data["id"])

    if db_user is None:
        db_user = create_user(
            session=session,
            discord_id=discord_user_data["id"],
            nickname=discord_user_data["username"],
            permission_level=0,
        )
    else:
        if db_user.nickname != discord_user_data["username"]:
            db_user = update_user(
                session=session, user=db_user, nickname=discord_user_data["username"]
            )

    response = JSONResponse(
        {
            "access_token": token,
            "refresh_token": refresh_token,
            "user": {
                "uid": db_user.uid,
                "discord_id": db_user.discord_id,
                "nickname": db_user.nickname,
                "permission_level": db_user.permission_level,
                "avatar_url": (
                    f"https://cdn.discordapp.com/avatars/{discord_user_data['id']}/{discord_user_data['avatar']}.png"
                    if discord_user_data.get("avatar")
                    else None
                ),
            },
        }
    )

    response.delete_cookie("oauth_state")

    return response


@router.get("/me")
async def get_current_user(
    token: str = Depends(discord.get_token), session: Session = Depends(get_session)
):
    """Get current authenticated user"""

    try:
        headers = {"Authorization": f"Bearer {token}"}

        async with aiohttp.ClientSession() as aio_session:
            async with aio_session.get(
                "https://discord.com/api/users/@me", headers=headers
            ) as response:
                if response.status != 200:
                    raise HTTPException(status_code=401, detail="Invalid token")
                discord_user_data = await response.json()

        db_user = get_user_by_discord_id(session, discord_user_data["id"])

        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found in database")

        return {
            "uid": db_user.uid,
            "discord_id": db_user.discord_id,
            "nickname": db_user.nickname,
            "permission_level": db_user.permission_level,
        }
    except Unauthorized:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/verify")
async def verify_token(token: str = Depends(discord.get_token)):
    """Verify if token is valid"""

    try:
        headers = {"Authorization": f"Bearer {token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://discord.com/api/users/@me", headers=headers
            ) as response:
                return {"valid": response.status == 200}
    except:
        return {"valid": False}
