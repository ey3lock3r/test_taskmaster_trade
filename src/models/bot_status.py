from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Column, DateTime
from src.model.base import BaseModel

class BotStatus(BaseModel, table=True):
    __tablename__ = 'bot_status'

    id: Optional[int] = Field(default=None, primary_key=True)
    status: str = Field(default="inactive") # e.g., 'active', 'inactive', 'error'
    last_check_in: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone.utc), nullable=True))