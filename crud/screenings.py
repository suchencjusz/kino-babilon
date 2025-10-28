from typing import Optional, List
from sqlmodel import Session, select
from models import Screening
from datetime import datetime


def get_screening(session: Session, sid: int) -> Optional[Screening]:
    """Get screening by ID"""
    return session.get(Screening, sid)


def get_screenings(session: Session, skip: int = 0, limit: int = 100) -> List[Screening]:
    """Get all screenings with pagination"""
    statement = select(Screening).offset(skip).limit(limit)
    return session.exec(statement).all()


def get_screenings_by_creator(
    session: Session, creator_uid: int, skip: int = 0, limit: int = 100
) -> List[Screening]:
    """Get screenings created by specific user"""
    statement = (
        select(Screening)
        .where(Screening.creator_uid == creator_uid)
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


def create_screening(
    session: Session,
    creator_uid: int,
    location: str,
    start_datetime: datetime,
    end_datetime: datetime,
    selection_mode: str,
    mid: int = 1,
    description: Optional[str] = None,
) -> Screening:
    """Create new screening"""
    screening = Screening(
        mid=mid,
        creator_uid=creator_uid,
        location=location,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        description=description,
        selection_mode=selection_mode,
    )
    session.add(screening)
    session.commit()
    session.refresh(screening)
    return screening


def update_screening(session: Session, screening: Screening, **kwargs) -> Screening:
    """Update screening fields"""
    for key, value in kwargs.items():
        if hasattr(screening, key):
            setattr(screening, key, value)
    session.add(screening)
    session.commit()
    session.refresh(screening)
    return screening


def delete_screening(session: Session, sid: int) -> Optional[Screening]:
    """Delete screening by ID"""
    screening = session.get(Screening, sid)
    if screening:
        session.delete(screening)
        session.commit()
    return screening