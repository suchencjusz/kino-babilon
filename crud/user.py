from typing import Optional, List
from sqlmodel import Session, select
from models import User


def get_user(session: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return session.get(User, user_id)


def get_user_by_discord_id(session: Session, discord_id: str) -> Optional[User]:
    """Get user by discord_id"""
    statement = select(User).where(User.discord_id == discord_id)
    return session.exec(statement).first()


def get_users(session: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get list of users with pagination"""
    statement = select(User).offset(skip).limit(limit)
    return session.exec(statement).all()


def create_user(session: Session, discord_id: str, nickname: str, permission_level: int = 0) -> User:
    """Create new user"""
    user = User(
        discord_id=discord_id,
        nickname=nickname,
        permission_level=permission_level
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_user(session: Session, user: User, **kwargs) -> User:
    """Update user fields"""
    for key, value in kwargs.items():
        setattr(user, key, value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(session: Session, user_id: int) -> Optional[User]:
    """Delete user by ID"""
    user = session.get(User, user_id)
    if user:
        session.delete(user)
        session.commit()
    return user