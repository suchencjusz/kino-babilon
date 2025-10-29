from fastapi import APIRouter, Depends

from models import User as UserModel
from routes.deps import get_current_user

router = APIRouter()


# test route za tokenem
@router.get("/me")
async def my_profile(current_user: UserModel = Depends(get_current_user)):

    return {
        "uid": current_user.uid,
        "discord_id": current_user.discord_id,
        "nickname": current_user.nickname,
        "permission_level": current_user.permission_level,
    }
