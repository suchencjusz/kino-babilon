from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Table

votes_table = Table(
    "votes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("movie_id", Integer, ForeignKey("movies.id"), primary_key=True)
)

attendance_table = Table(
    "attendance",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("seans_id", Integer, ForeignKey("seanse.id"), primary_key=True)
)

class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, index=True)
    imdb_id = Column(String, unique=True, index=True)
    title = Column(String)
    plot = Column(Text, nullable=True)       # fabuła filmu
    rating = Column(String, nullable=True)   # ocena IMDb
    poster = Column(String, nullable=True)

    voters = relationship("User", secondary=votes_table, back_populates="voted_movies")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="widz")
    plans = relationship("Plan", back_populates="user")
    voted_movies = relationship("Movie", secondary=votes_table, back_populates="voters")
    attendance = relationship(
        "Seans",
        secondary=attendance_table,
        back_populates="attendees"
    )

class Seans(Base):
    __tablename__ = "seanse"
    id = Column(Integer, primary_key=True, index=True)
    tytul = Column(String)
    link = Column(String)
    pokoj = Column(String)
    data = Column(DateTime)
    operator_id = Column(Integer, ForeignKey("users.id"))
    archiwalny = Column(Boolean, default=False)  # nowa kolumna
    attendees = relationship(
        "User",
        secondary=attendance_table,
        back_populates="attendance"
    )

class Plan(Base):
    __tablename__ = "plany"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    data = Column(DateTime)
    user = relationship("User", back_populates="plans")
