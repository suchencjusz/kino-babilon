from dotenv import load_dotenv
import os

load_dotenv()

from sqlmodel import Session, SQLModel, create_engine
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kino_babilon.db")
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})


def create_db_and_tables():
    """Creates all database tables"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Returns database session"""
    with Session(engine) as session:
        yield session