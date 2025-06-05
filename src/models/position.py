from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, Relationship, SQLModel, Column, DateTime

class Position(SQLModel, table=True):
    __tablename__ = 'positions'

    id: Optional[int] = Field(default=None, primary_key=True)
    bot_instance_id: int = Field(foreign_key="bot_instances.id")
    symbol: str
    quantity: int
    average_cost: float
    current_value: Optional[float] = None
    opened_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone.utc), nullable=False))

    bot_instance: "BotInstance" = Relationship(back_populates="positions")