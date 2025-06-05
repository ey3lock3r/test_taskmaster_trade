from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel

from pydantic import EmailStr, field_validator, ConfigDict

class UserCreate(SQLModel):
    model_config = ConfigDict(extra='forbid') # Forbid extra fields
    username: str
    password: str
    email: Optional[EmailStr] = None

    @field_validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('must be alphanumeric')
        if len(v) < 3:
            raise ValueError('must be at least 3 characters')
        return v

    @field_validator('password')
    def password_complexity(cls, v):
        if len(v) < 8:
            raise ValueError('must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('must contain at least one number')
        if not any(char.isalpha() for char in v):
            raise ValueError('must contain at least one letter')
        return v

class UserResponse(SQLModel):
    id: int
    username: str
    email: str
    is_active: bool

from pydantic import EmailStr, model_validator, ConfigDict

class Token(SQLModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None # Add refresh_token to the Token schema

class LoginRequest(SQLModel):
    model_config = ConfigDict(extra='forbid') # Forbid extra fields
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str

    @model_validator(mode='after')
    def check_username_or_email(self):
        if not self.username and not self.email:
            raise ValueError('Either username or email must be provided')
        return self

class BrokerageConnectionCreate(SQLModel):
    brokerage_name: str
    api_key: str
    api_secret: Optional[str] = None
    account_id: Optional[str] = None

class BrokerageConnectionResponse(SQLModel):
    id: int
    user_id: int
    brokerage_name: str
    account_id: Optional[str] = None
    is_active: bool

class BotInstanceCreate(SQLModel):
    strategy_id: int
    brokerage_connection_id: int
    name: str
    parameters: Optional[Dict[str, Any]] = None

class BotInstanceResponse(SQLModel):
    id: int
    user_id: int
    strategy_id: int
    brokerage_connection_id: int
    name: str
    status: str
    parameters: Optional[Dict[str, Any]] = None
    is_active: bool

class BotStatusResponse(SQLModel):
    id: int
    status: str
    last_check_in: Optional[datetime] = None
    is_active: bool

class TradeOrderResponse(SQLModel):
    id: int
    bot_instance_id: int
    symbol: str
    order_type: str
    quantity: int
    price: Optional[float] = None
    status: str
    executed_at: Optional[datetime] = None
    is_active: bool

class PositionResponse(SQLModel):
    id: int
    bot_instance_id: int
    symbol: str
    quantity: int
    average_cost: float
    current_value: Optional[float] = None
    opened_at: datetime
    is_active: bool