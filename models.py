from sqlmodel import (
    Column,
    Integer,
    String,
    ForeignKey,
    Field,
    SQLModel,
    Relationship,
    DateTime,
)

from typing import Optional
from datetime import datetime


class User(SQLModel, table=True):
    __tablename__ = "users"

    uid: int = Field(default=None, primary_key=True, index=True)
    discord_id: str = Field(
        sa_column=Column("discord_id", String, unique=True, index=True)
    )
    nickname: str = Field(sa_column=Column("nickname", String))
    permission_level: int = Field(
        sa_column=Column("permission_level", Integer, default=0)
    )


class Media(SQLModel, table=True):
    __tablename__ = "media"

    mid: int = Field(default=None, primary_key=True, index=True)
    title: str = Field(sa_column=Column("title", String))
    year: int = Field(sa_column=Column("year", Integer))
    description: str = Field(sa_column=Column("description", String))
    poster_url: str = Field(sa_column=Column("poster_url", String))
    media_url: str = Field(sa_column=Column("media_url", String))
    media_type: str = Field(
        sa_column=Column("media_type", String)
    )  # 'movie', 'tv_show'
    media_source: str = Field(
        sa_column=Column("media_source", String)
    )  # 'filmweb', 'imdb', 'omdb', 'letterboxd'


class Vote(SQLModel, table=True):
    __tablename__ = "votes"

    vid: int = Field(default=None, primary_key=True, index=True)
    sid: int = Field(sa_column=Column("sid", Integer, ForeignKey("screenings.sid")))
    mid: int = Field(sa_column=Column("mid", Integer, ForeignKey("media.mid")))
    uid: int = Field(sa_column=Column("uid", Integer, ForeignKey("users.uid")))


class Screening(SQLModel, table=True):
    __tablename__ = "screenings"

    sid: int = Field(default=None, primary_key=True, index=True)
    mid: int = Field(sa_column=Column("mid", Integer, ForeignKey("media.mid")))
    creator_uid: int = Field(
        sa_column=Column("creator_uid", Integer, ForeignKey("users.uid"))
    )
    start_datetime: Optional[datetime] = Field(sa_column=Column("start_time", DateTime))
    end_datetime: Optional[datetime] = Field(sa_column=Column("end_time", DateTime))
    location: str = Field(sa_column=Column("location", String))
    description: str = Field(sa_column=Column("description", String))

    creator: "User" = Relationship(back_populates="created_screenings")


class Attendance(SQLModel, table=True):
    __tablename__ = "attendances"

    aid: int = Field(default=None, primary_key=True, index=True)
    sid: int = Field(sa_column=Column("sid", Integer, ForeignKey("screenings.sid")))
    uid: int = Field(sa_column=Column("uid", Integer, ForeignKey("users.uid")))
    vote_datetime: Optional[datetime] = Field(sa_column=Column("vote_datetime", DateTime))
    attendance_status: str = Field(
        sa_column=Column("attendance_status", String)
    )  # 'attending', 'not_attending', 'maybe'


# backpopulates do zrobienia tam gdzie trzeba
