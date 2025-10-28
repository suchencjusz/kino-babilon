from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from routes.deps import get_current_user
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

router = APIRouter()

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

#
# endpointy
#

#
# to do:
#   - permisje dla adminow itp

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
            status_code=400,
            detail="end_datetime must be after start_datetime"
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


@router.get("/user/me", response_model=List[ScreeningResponse], summary="Get my screenings")
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


@router.put("/{sid}", response_model=ScreeningResponse, summary="Update screening")
async def update_screening_endpoint(
    sid: int,
    payload: ScreeningUpdate,
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Aktualizuje screening (tylko creator może)"""

    screening = get_screening(session=session, sid=sid)
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    if screening.creator_uid != current_user.uid:
        raise HTTPException(status_code=403, detail="Only creator can update screening")

    update_data = payload.dict(exclude_unset=True) # to do: to trzeba poprawic na model dump
    
    if "end_datetime" in update_data and "start_datetime" in update_data:
        if update_data["end_datetime"] <= update_data["start_datetime"]:
            raise HTTPException(
                status_code=400,
                detail="end_datetime must be after start_datetime"
            )

    updated_screening = update_screening(session=session, screening=screening, **update_data)

    return updated_screening


@router.delete("/{sid}", summary="Delete screening")
async def delete_screening_endpoint(
    sid: int,
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Usuwa screening (tylko creator może)"""

    screening = get_screening(session=session, sid=sid)
    
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    if screening.creator_uid != current_user.uid:
        raise HTTPException(status_code=403, detail="Only creator can delete screening")

    delete_screening(session=session, sid=sid)
    
    return {"message": "Screening deleted successfully"}