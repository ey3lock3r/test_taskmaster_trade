from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel, JSON, Column
from src.model.base import BaseModel
from src.models.trade_order import TradeOrder
from src.models.position import Position

class BotInstance(BaseModel, table=True):
    __tablename__ = 'bot_instances'

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    strategy_id: int = Field(foreign_key="strategy_definitions.id")
    brokerage_connection_id: int = Field(foreign_key="brokerage_connections.id")
    name: str = Field(index=True)
    status: str = "inactive" # e.g., 'active', 'inactive', 'error'
    parameters: Optional[dict] = Field(default=None, sa_column=Column(JSON)) # Store strategy-specific parameters as JSON

    user: "User" = Relationship(back_populates="bot_instances")
    strategy: "StrategyDefinition" = Relationship(back_populates="bot_instances")
    brokerage_connection: "BrokerageConnection" = Relationship(back_populates="bot_instances")
    trade_orders: List["TradeOrder"] = Relationship(back_populates="bot_instance")
    positions: List["Position"] = Relationship(back_populates="bot_instance")