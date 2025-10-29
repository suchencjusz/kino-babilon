import os

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from routes.deps import get_current_user, OwnerOrPermissionChecker
from db import get_session
from models import Screening as ScreeningModel, User as UserModel, SelectionMode
from crud.screenings import (
    get_screening,
    get_screenings,
    get_screenings_by_creator,
    create_screening,
    update_screening,
    delete_screening,
)

if os.path.exists(".env"):
    from dotenv import load_dotenv

    load_dotenv()

router = APIRouter()

#
# auth factory
#

is_screening_owner_or_admin = OwnerOrPermissionChecker(
    resource_getter=get_screening, id_param_name="sid", required_level=100
)

is_screening_owner_or_moderator = OwnerOrPermissionChecker(
    resource_getter=get_screening, id_param_name="sid", required_level=20
)


#
# modele pydantic
#


class ScreeningCreate(BaseModel):
    """Request body dla tworzenia screeningu"""

    location: str
    start_datetime: datetime
    end_datetime: datetime
    description: Optional[str] = None
    selection_mode: SelectionMode = SelectionMode.OPERATOR_CHOICE


class ScreeningUpdate(BaseModel):
    """Request body dla aktualizacji screeningu"""

    location: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    description: Optional[str] = None
    selection_mode: Optional[SelectionMode] = None


class ScreeningResponse(BaseModel):
    """Response model screeningu"""

    sid: int
    mid: Optional[int]
    creator_uid: int
    location: str
    start_datetime: datetime
    end_datetime: datetime
    description: Optional[str]
    selection_mode: SelectionMode


class BasicScreeningResponse(BaseModel):
    """Basic Response model screeningu"""

    start_datetime: datetime


#
# endpointy
#


@router.post("/", response_model=ScreeningResponse, summary="Create screening")
async def create_screening_endpoint(
    payload: ScreeningCreate,
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Tworzy Screening.
    - location: wymagane
    - start_datetime: wymagane (ISO format)
    - end_datetime: wymagane (ISO format)
    - selection_mode: wymagane (operator_choice, curated_vote, open_vote)
    - mid: hardcoded na 1 tymczasowo
    """

    if not current_user or not getattr(current_user, "uid", None):
        raise HTTPException(status_code=401, detail="Unauthorized")

    if payload.end_datetime <= payload.start_datetime:
        raise HTTPException(
            status_code=400, detail="end_datetime must be after start_datetime"
        )

    screening = create_screening(
        session=session,
        creator_uid=current_user.uid,
        location=payload.location,
        start_datetime=payload.start_datetime,
        end_datetime=payload.end_datetime,
        description=payload.description,
        selection_mode=payload.selection_mode,
        mid=1,
    )

    return screening


@router.get(
    "/basic-by-date-range",
    response_model=List[BasicScreeningResponse],
    summary="Get basic screenings by date range",
)
async def get_basic_screenings_by_date_range(
    start_date: datetime, end_date: datetime, session: Session = Depends(get_session)
):
    """
    Zwraca listę podstawowych informacji o screeningach, które są aktywne w podanym zakresie dat.
    Oznacza to, że na liście znajdą się seanse, które zaczynają się przed `end_date` i kończą po `start_date`.
    Uwzględnia to seanse, które w całości lub częściowo pokrywają się z podanym przedziałem czasowym.

    - start_date: początek zakresu (ISO format) (np: 2024-01-01T00:00:00)
    - end_date: koniec zakresu (ISO format) (np: 2024-01-01T00:00:00)
    """

    if end_date <= start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

    screenings = session.exec(
        select(ScreeningModel.start_datetime)
        .where(ScreeningModel.start_datetime < end_date)
        .where(ScreeningModel.end_datetime > start_date)
    ).all()

    return screenings


@router.get(
    "/by-date-range",
    response_model=List[ScreeningResponse],
    summary="Get screenings by date range",
)
async def get_screenings_by_date_range(
    start_date: datetime,
    end_date: datetime,
    session: Session = Depends(get_session),
):
    """
    Zwraca listę screeningów, które są aktywne w podanym zakresie dat.
    Oznacza to, że na liście znajdą się seanse, które zaczynają się przed `end_date` i kończą po `start_date`.
    Uwzględnia to seanse, które w całości lub częściowo pokrywają się z podanym przedziałem czasowym.

    - start_date: początek zakresu (ISO format) (np: 2024-01-01T00:00:00)
    - end_date: koniec zakresu (ISO format) (np: 2024-01-01T00:00:00)
    """

    if end_date <= start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

    screenings = session.exec(
        select(ScreeningModel)
        .where(ScreeningModel.start_datetime < end_date)
        .where(ScreeningModel.end_datetime > start_date)
    ).all()

    return screenings


@router.get("/", response_model=List[ScreeningResponse], summary="Get all screenings")
async def get_all_screenings(
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
):
    """
    Zwraca listę wszystkich screeningów.
    - skip: ile pomijać (dla paginacji)
    - limit: ile zwrócić
    """

    screenings = get_screenings(session=session, skip=skip, limit=limit)
    return screenings


@router.get("/{sid}", response_model=ScreeningResponse, summary="Get screening by ID")
async def get_screening_endpoint(
    sid: int,
    session: Session = Depends(get_session),
):
    """Zwraca screening po ID"""

    screening = get_screening(session=session, sid=sid)

    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    return screening


@router.get(
    "/user/{user_id}",
    response_model=List[ScreeningResponse],
    summary="Get screenings by user ID",
)
async def get_screenings_by_user_endpoint(
    user_id: int,
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
):
    """Zwraca screeningi utworzone przez danego użytkownika"""

    screenings = get_screenings_by_creator(
        session=session, creator_uid=user_id, skip=skip, limit=limit
    )

    return screenings


# to do: uwzglednic pusta liste
@router.get(
    "/user/me", response_model=List[ScreeningResponse], summary="Get my screenings"
)
async def get_my_screenings_endpoint(
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
):
    """Zwraca screeningi utworzone przez zalogowanego użytkownika"""

    screenings = get_screenings_by_creator(
        session=session, creator_uid=current_user.uid, skip=skip, limit=limit
    )

    return screenings


@router.put(
    "/{screening_id}", response_model=ScreeningResponse, summary="Update screening"
)
async def update_screening_endpoint(
    screening_id: int,
    payload: ScreeningUpdate,
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(is_screening_owner_or_moderator),
):
    """
    Aktualizuje screening, tylko dla:
    - creatora screeningu
    - lub permisji>=20
    """

    screening = get_screening(session=session, sid=screening_id)
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    if screening.creator_uid != current_user.uid:
        raise HTTPException(status_code=403, detail="Only creator can update screening")

    update_data = payload.dict(
        exclude_unset=True
    )  # to do: to trzeba poprawic na model dump

    if "end_datetime" in update_data and "start_datetime" in update_data:
        if update_data["end_datetime"] <= update_data["start_datetime"]:
            raise HTTPException(
                status_code=400, detail="end_datetime must be after start_datetime"
            )

    updated_screening = update_screening(
        session=session, screening=screening, **update_data
    )

    return updated_screening


@router.delete("/{screening_id}", summary="Delete screening")
async def delete_screening_endpoint(
    screening_id: int,
    current_user: UserModel = Depends(is_screening_owner_or_moderator),
    session: Session = Depends(get_session),
):
    """
    Usuwa screening
    - tylko creator screeningu
    - lub permisje>=20
    """

    screening = get_screening(session=session, sid=screening_id)

    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    if screening.creator_uid != current_user.uid:
        raise HTTPException(status_code=403, detail="Only creator can delete screening")

    delete_screening(session=session, sid=screening_id)

    return {"message": "Screening deleted successfully"}
