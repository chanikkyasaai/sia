from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    name: str
    email: str
    phone: str
    locale: Optional[str]

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str]

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: str
    password: str