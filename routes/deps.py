from fastapi import Depends, HTTPException
from sqlmodel import Session

from discord import discord
from fastapi_discord import Unauthorized

from db import get_session
from crud.user import get_user_by_discord_id, create_user
from models import User


async def get_current_user(
    token: str = Depends(discord.get_token),
    session: Session = Depends(get_session),
) -> User:
    try:
        discord_user = await discord.user(token)
    except Unauthorized:
        raise HTTPException(status_code=401, detail="Invalid Discord token")

    db_user = get_user_by_discord_id(session, str(discord_user.id))
    if db_user is None:
        db_user = create_user(
            session=session,
            discord_id=str(discord_user.id),
            nickname=discord_user.username,
            permission_level=0,
        )
    return db_user