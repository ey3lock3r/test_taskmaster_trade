from typing import Optional
from sqlmodel import Field, Relationship, SQLModel

class StrategyParameter(SQLModel, table=True):
    __tablename__ = 'strategy_parameters'

    id: Optional[int] = Field(default=None, primary_key=True)
    strategy_definition_id: int = Field(foreign_key="strategy_definitions.id")
    name: str
    value: str

    strategy_definition: "StrategyDefinition" = Relationship(back_populates="parameters")