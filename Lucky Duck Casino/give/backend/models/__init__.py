from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import BigInteger
from enum import Enum


class Endpoints(str, Enum):
    blackjack = 'blackjack'
    lose = 'lose'
    flag = 'flag'


class User(SQLModel, table=True):
    __tablename__ = 'Users'
    id: int = Field(primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str = ''
    deck: Optional[str] = ''
    bankroll: int = Field(default=1000)
    state: int = Field(sa_type=BigInteger)
    bet: int = Field(default=0)
    on_hands: Optional[str] = ''
    number_of_games: int = Field(default=0)
    dealer: Optional[str] = ''
