import os

from fastapi import APIRouter

# from crud.media import (create_media, delete_media, get_media,


if os.path.exists(".env"):
    from dotenv import load_dotenv

    load_dotenv()

router = APIRouter()

#
# auth factory
#

# is_screening_owner_or_admin = OwnerOrPermissionChecker(
#     resource_getter=get_screening, id_param_name="sid", required_level=100
# )

# is_screening_owner_or_moderator = OwnerOrPermissionChecker(
#     resource_getter=get_screening, id_param_name="sid", required_level=20
# )


#
# modele pydantic
#


#
# endpointy
#
