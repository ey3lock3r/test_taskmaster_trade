from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from src.model.base import BaseModel
from src.models.strategy_parameters import StrategyParameter

class StrategyDefinition(BaseModel, table=True):
    __tablename__ = 'strategy_definitions'

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None
    file_path: str # Path to the strategy file
    class_name: str # Class name within the strategy file
    created_by: int = Field(foreign_key="users.id") # Add foreign key to user

    bot_instances: List["BotInstance"] = Relationship(back_populates="strategy")
    parameters: List["StrategyParameter"] = Relationship(back_populates="strategy_definition")
    created_user: "User" = Relationship(back_populates="strategy_definitions") # Add relationship to user