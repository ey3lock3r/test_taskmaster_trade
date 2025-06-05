from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Index, Column, DateTime

class MarketDataCache_OptionChain(SQLModel, table=True):
    __tablename__ = 'market_data_cache_option_chain'

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str
    expiration_date: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    strike_price: float
    option_type: str # 'call' or 'put'
    bid: Optional[float] = None
    ask: Optional[float] = None
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    open_interest: Optional[int] = None
    volume: Optional[int] = None
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone.utc), nullable=False, onupdate=lambda: datetime.now(timezone.utc)))

    __table_args__ = (
        Index('idx_symbol_expiration', 'symbol', 'expiration_date'),
    )