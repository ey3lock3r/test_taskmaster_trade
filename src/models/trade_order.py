from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, Relationship, SQLModel, Column, DateTime

class TradeOrder(SQLModel, table=True):
    __tablename__ = 'trade_orders'

    id: Optional[int] = Field(default=None, primary_key=True)
    bot_instance_id: int = Field(foreign_key="bot_instances.id")
    symbol: str
    order_type: str # e.g., 'market', 'limit', 'stop'
    quantity: int
    price: Optional[float] = None
    status: str # e.g., 'pending', 'filled', 'cancelled', 'rejected'
    executed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone.utc), nullable=True))

    bot_instance: "BotInstance" = Relationship(back_populates="trade_orders")