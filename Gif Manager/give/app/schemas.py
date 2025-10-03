from pydantic import BaseModel
from datetime import datetime


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    gifs_count: int = 0

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class GifFile(BaseModel):
    name: str
    path: str
    size: int
