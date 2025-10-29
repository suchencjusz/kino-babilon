import aiohttp
from typing import Callable, Any
from fastapi import Depends, HTTPException, Security, Request
from sqlmodel import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession() as aio_session:
            async with aio_session.get(
                "https://discord.com/api/users/@me", headers=headers
            ) as response:
                if response.status != 200:
                    raise HTTPException(status_code=401, detail="Invalid or expired token")
                discord_user_data = await response.json()
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    db_user = get_user_by_discord_id(session, str(discord_user_data["id"]))
    if db_user is None:
        db_user = create_user(
            session=session,
            discord_id=str(discord_user_data["id"]),
            nickname=discord_user_data["username"],
            permission_level=0,
        )

    return db_user


def require_permission(required_level: int) -> Callable:
    """
    Fabryka zależności, która tworzy zależność do sprawdzania poziomu uprawnień użytkownika.
    """
    async def _require_permission(current_user: User = Depends(get_current_user)) -> User:
        if current_user.permission_level < required_level:
            raise HTTPException(
                status_code=403,
                detail=f"Wymagany poziom uprawnień: {required_level}. Twój poziom: {current_user.permission_level}.",
            )
        return current_user

    return _require_permission


class OwnerOrPermissionChecker:
    """
    Generyczna zależność sprawdzająca, czy użytkownik jest właścicielem zasobu
    LUB ma wymagany poziom uprawnień.
    """
    def __init__(self, resource_getter: Callable, id_param_name: str, required_level: int, owner_field: str = "creator_uid"):
        self.resource_getter = resource_getter
        self.id_param_name = id_param_name
        self.required_level = required_level
        self.owner_field = owner_field

    def __call__(self, request: Request, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
        resource_id = request.path_params.get(self.id_param_name)
        if not resource_id:
            raise HTTPException(status_code=500, detail=f"Nie można zidentyfikować zasobu (brak '{self.id_param_name}' w ścieżce).")

        resource = self.resource_getter(session=session, id=int(resource_id))
        if not resource:
            raise HTTPException(status_code=404, detail="Zasób nie został znaleziony.")

        owner_id = getattr(resource, self.owner_field, None)
        if owner_id is None:
            raise HTTPException(status_code=500, detail=f"Nie można zweryfikować właściciela zasobu (brak pola '{self.owner_field}').")

        is_owner = current_user.uid == owner_id
        has_permission = current_user.permission_level >= self.required_level

        if not (is_owner or has_permission):
            raise HTTPException(
                status_code=403,
                detail="Brak uprawnień. Musisz być właścicielem lub posiadać odpowiednie permisje.",
            )
        
        return current_user