from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session

from discord import discord
from fastapi_discord import Unauthorized

from db import get_session
from crud.user import get_user_by_discord_id, create_user
from models import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    """
    Dependency: pobiera token z Authorization: Bearer <token>, waliduje go przez Discord API,
    tworzy użytkownika w DB jeśli nie istnieje i zwraca obiekt User.
    """

    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = credentials.credentials

    try:
        discord_user = await discord.user(token)
    except Unauthorized:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    db_user = get_user_by_discord_id(session, str(discord_user.id))
    if db_user is None:
        db_user = create_user(
            session=session,
            discord_id=str(discord_user.id),
            nickname=discord_user.username,
            permission_level=0,
        )

    return db_user