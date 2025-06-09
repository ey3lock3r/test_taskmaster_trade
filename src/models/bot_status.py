from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Column, DateTime, Relationship
from src.model.base import BaseModel

class BotStatus(BaseModel, table=True):
    __tablename__ = 'bot_status'

    id: Optional[int] = Field(default=None, primary_key=True)
    bot_instance_id: int = Field(index=True, foreign_key="bot_instances.id")
    status: str = Field(default="inactive") # e.g., 'active', 'inactive', 'error'
    last_check_in: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone.utc), nullable=True))
    is_active: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None)

    bot_instance: "BotInstance" = Relationship(back_populates="bot_status_entries")