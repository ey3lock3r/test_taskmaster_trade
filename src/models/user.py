from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from passlib.context import CryptContext
from datetime import datetime, timezone

from src.model.base import BaseModel # Import BaseModel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel, table=True):
    """User model for authentication and authorization."""
    __tablename__ = 'users'

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    email: Optional[str] = Field(default=None, unique=True, index=True, max_length=100)
    hashed_password: str = Field(max_length=100)
    is_admin: bool = Field(default=False)
    last_login: Optional[datetime] = None
    status: str = Field(default="active", max_length=20) # e.g., active, inactive, suspended
    
    sessions: List["Session"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    brokerage_connections: List["BrokerageConnection"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    bot_instances: List["BotInstance"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    strategy_definitions: List["StrategyDefinition"] = Relationship(back_populates="created_user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

    def set_password(self, password: str):
        self.hashed_password = pwd_context.hash(password)

    def check_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', is_admin={self.is_admin}, status='{self.status}')>"