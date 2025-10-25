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

from enum import Enum

#
# ENUMS
#

class SelectionMode(str, Enum):
    OPERATOR_CHOICE = "operator_choice"
    CURATED_VOTE = "curated_vote"
    OPEN_VOTE = "open_vote"

class AttendanceStatus(str, Enum):
    ATTENDING = "attending"
    NOT_ATTENDING = "not_attending"
    MAYBE = "maybe"

class MediaType(str, Enum):
    MOVIE = "movie"
    TV_SHOW = "tv_show"

class MediaSource(str, Enum):
    FILMWEB = "filmweb"
    IMDB = "imdb"
    OMDB = "omdb"
    LETTERBOXD = "letterboxd"

#
# TABELKI
#

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

    # Relationships
    created_screenings: list["Screening"] = Relationship(back_populates="creator")
    votes: list["Vote"] = Relationship(back_populates="user")
    attendances: list["Attendance"] = Relationship(back_populates="user")


class Media(SQLModel, table=True):
    __tablename__ = "media"

    mid: int = Field(default=None, primary_key=True, index=True)

    title: str = Field(sa_column=Column("title", String))
    year: int = Field(sa_column=Column("year", Integer))
    description: str = Field(sa_column=Column("description", String))
    poster_url: str = Field(sa_column=Column("poster_url", String))
    media_url: str = Field(sa_column=Column("media_url", String))
    media_type: MediaType = Field(default=MediaType.MOVIE)
    media_source: MediaSource = Field(default=MediaSource.FILMWEB)

    # Relationships
    screening_pools: list["ScreeningVotingPool"] = Relationship(back_populates="media")
    votes: list["Vote"] = Relationship(back_populates="media")


class Vote(SQLModel, table=True):
    __tablename__ = "votes"

    vid: int = Field(default=None, primary_key=True, index=True)

    sid: int = Field(sa_column=Column("sid", Integer, ForeignKey("screenings.sid")))
    mid: int = Field(sa_column=Column("mid", Integer, ForeignKey("media.mid")))
    uid: int = Field(sa_column=Column("uid", Integer, ForeignKey("users.uid")))
    created_at: Optional[datetime] = Field(sa_column=Column("created_at", DateTime))

    # Relationships
    screening: "Screening" = Relationship(back_populates="votes")
    user: "User" = Relationship(back_populates="votes")
    media: "Media" = Relationship(back_populates="votes")


class ScreeningVotingPool(SQLModel, table=True):
    __tablename__ = "screening_voting_pool"

    pool_id: int = Field(default=None, primary_key=True, index=True)

    sid: int = Field(sa_column=Column("sid", Integer, ForeignKey("screenings.sid")))
    mid: int = Field(sa_column=Column("mid", Integer, ForeignKey("media.mid")))

    # Relationships
    screening: "Screening" = Relationship(back_populates="voting_pool")
    media: "Media" = Relationship(back_populates="screening_pools")


class Screening(SQLModel, table=True):
    __tablename__ = "screenings"

    sid: int = Field(default=None, primary_key=True, index=True)

    mid: Optional[int] = Field(sa_column=Column("mid", Integer, ForeignKey("media.mid")))

    creator_uid: int = Field(
        sa_column=Column("creator_uid", Integer, ForeignKey("users.uid"))
    )

    selection_mode: SelectionMode = Field(default=SelectionMode.OPERATOR_CHOICE)

    start_datetime: Optional[datetime] = Field(sa_column=Column("start_time", DateTime))
    end_datetime: Optional[datetime] = Field(sa_column=Column("end_time", DateTime))
    location: str = Field(sa_column=Column("location", String))
    description: str = Field(sa_column=Column("description", String))

    # Relationships
    creator: "User" = Relationship(back_populates="created_screenings")
    voting_pool: list["ScreeningVotingPool"] = Relationship(back_populates="screening")
    votes: list["Vote"] = Relationship(back_populates="screening")
    attendances: list["Attendance"] = Relationship(back_populates="screening")


class Attendance(SQLModel, table=True):
    __tablename__ = "attendances"

    aid: int = Field(default=None, primary_key=True, index=True)
    
    sid: int = Field(sa_column=Column("sid", Integer, ForeignKey("screenings.sid")))
    uid: int = Field(sa_column=Column("uid", Integer, ForeignKey("users.uid")))
    created_at: Optional[datetime] = Field(sa_column=Column("created_at", DateTime))
    attendance_status: AttendanceStatus = Field(default=AttendanceStatus.MAYBE)

    # Relationships
    screening: "Screening" = Relationship(back_populates="attendances")
    user: "User" = Relationship(back_populates="attendances")
