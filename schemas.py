from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "widz"

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    class Config:
        orm_mode = True

class SeansBase(BaseModel):
    tytul: str
    link: str
    pokoj: str
    data: datetime

class SeansOut(SeansBase):
    id: int
    class Config:
        orm_mode = True

class PlanBase(BaseModel):
    data: datetime
