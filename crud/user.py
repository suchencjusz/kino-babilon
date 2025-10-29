import os
from typing import List, Optional

from sqlmodel import Session, select

from models import User

if os.path.exists(".env"):
    from dotenv import load_dotenv

    load_dotenv()


def get_user(session: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return session.get(User, user_id)


# to do: dlaczego tu jest str?
def get_user_by_discord_id(session: Session, discord_id: str) -> Optional[User]:
    """Get user by discord_id"""
    statement = select(User).where(User.discord_id == discord_id)
    return session.exec(statement).first()


def get_users(session: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get list of users with pagination"""
    statement = select(User).offset(skip).limit(limit)
    return session.exec(statement).all()


def create_user(
    session: Session, discord_id: str, nickname: str, permission_level: int = 0
) -> User:
    """Create new user"""

    # --- first admin ---
    first_admin_id = os.getenv("FIRST_ADMIN_DISCORD_ID")
    if first_admin_id and discord_id == first_admin_id:
        permission_level = 100
        print(f"Creating first admin user with Discord ID {discord_id}")
    # -------------------

    user = User(
        discord_id=discord_id, nickname=nickname, permission_level=permission_level
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
