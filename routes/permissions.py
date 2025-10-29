import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
# from fastapi_discord import Unauthorized
from sqlmodel import Session

from crud.user import get_user_by_discord_id, update_user
from db import get_session
from models import User as UserModel  # noqa F401
from routes.deps import get_current_user, require_permission

if os.path.exists(".env"):
    from dotenv import load_dotenv

    load_dotenv()

router = APIRouter()

#
# 0 - niezalogowany
# 20 - moderator
# 100 - admin
#


@router.put("/change-permission/{discord_id}/{new_level}")
async def change_permission(
    discord_id: int,
    new_level: int,
    current_user: UserModel = Depends(require_permission(50)),
    session: Session = Depends(get_session),
):
    """
    Zmienia poziom uprawnień użytkownika.
    - Wymaga uprawnień na poziomie >= 50.
    - Nie można nadać uprawnień wyższych niż własne.
    - Nie można zmienić własnych uprawnień.
    """

    if new_level > current_user.permission_level:
        raise HTTPException(
            status_code=403,
            detail=f"Nie możesz nadać uprawnień ({new_level}) wyższych niż własne ({current_user.permission_level}).",
        )

    if str(discord_id) == current_user.discord_id:
        raise HTTPException(
            status_code=400,
            detail="Nie możesz zmienić własnych uprawnień za pomocą tego endpointu.",
        )

    user_to_update = get_user_by_discord_id(session, str(discord_id))
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = update_user(session, user_to_update, permission_level=new_level)

    return JSONResponse(
        content={
            "message": f"Poziom uprawnień użytkownika {updated_user.nickname} został zmieniony na {new_level}"
        }
    )


@router.get("/ensure-admin")
async def ensure_admin(
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Nadaje uprawnienia administratora (poziom 100) użytkownikowi zdefiniowanemu
    jako FIRST_ADMIN_DISCORD_ID w zmiennych środowiskowych.
    Działa tylko dla tego konkretnego użytkownika.
    """
    first_admin_id = os.getenv("FIRST_ADMIN_DISCORD_ID")

    if not first_admin_id:
        raise HTTPException(
            status_code=500,
            detail="Funkcja pierwszego admina nie jest skonfigurowana (brak FIRST_ADMIN_DISCORD_ID).",
        )

    if current_user.discord_id != first_admin_id:
        raise HTTPException(
            status_code=403,
            detail="Nie masz uprawnień do wykonania tej operacji.",
        )

    if current_user.permission_level == 100:
        return JSONResponse(
            content={"message": "Już posiadasz uprawnienia administratora."}
        )

    updated_user = update_user(session, current_user, permission_level=100)

    return JSONResponse(
        content={
            "message": f"Pomyślnie nadano uprawnienia administratora dla użytkownika {updated_user.nickname}."
        }
    )
