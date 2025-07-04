from typing import List, Optional
from sqlmodel import Field, Relationship
from src.model.base import BaseModel

class Broker(BaseModel, table=True):
    __tablename__ = 'brokers'

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, unique=True, index=True, nullable=False)
    base_url: str = Field(nullable=False)
    streaming_url: str = Field(nullable=False) # New field for streaming/websocket URL
    is_live_mode: bool = Field(default=False, nullable=False) # True for live, False for sandbox

    # Define the relationship to BrokerageConnection
    connections: List["BrokerageConnection"] = Relationship(back_populates="broker")

    def __repr__(self):
        return f"<Broker(name='{self.name}', base_url='{self.base_url}', is_live_mode={self.is_live_mode})>"