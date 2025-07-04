from typing import List, Optional
from datetime import datetime, timezone
from sqlmodel import Field, Relationship, SQLModel, LargeBinary, Column, DateTime
from src.model.base import BaseModel
from src.utils.encryption import EncryptionUtil
from src.config import settings
from src.models.broker import Broker # New import

class BrokerageConnection(BaseModel, table=True):
    """
    BrokerageConnection model for storing API credentials and connection details.
    Sensitive data like API keys and secrets should be encrypted.
    """
    __tablename__ = 'brokerage_connections'

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    broker_id: int = Field(foreign_key="brokers.id") # New foreign key
    api_key: Optional[bytes] = Field(default=None, sa_column=Column(LargeBinary, nullable=True)) # Store as bytes, made nullable
    api_secret: Optional[bytes] = Field(default=None, sa_column=Column(LargeBinary, nullable=True)) # Store as bytes
    access_token: Optional[bytes] = Field(default=None, sa_column=Column(LargeBinary, nullable=True)) # Store as bytes
    refresh_token: Optional[bytes] = Field(default=None, sa_column=Column(LargeBinary, nullable=True)) # Store as bytes
    expires_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone.utc), nullable=True)) # Added for token expiration
    connection_status: str = Field(default="disconnected", max_length=20) # e.g., 'connected', 'disconnected', 'error'
    last_connected: Optional[datetime] = None

    user: "User" = Relationship(back_populates="brokerage_connections")
    broker: Optional["Broker"] = Relationship(back_populates="connections") # New relationship
    bot_instances: List["BotInstance"] = Relationship(back_populates="brokerage_connection")

    def __init__(self, user_id: int, broker_id: int, access_token: Optional[str] = None,
                 refresh_token: Optional[str] = None, expires_at: Optional[datetime] = None,
                 api_key: Optional[str] = None, api_secret: Optional[str] = None,
                 connection_status: str = "disconnected", last_connected: Optional[datetime] = None, **kwargs):
        # Initialize SQLModel fields first
        super().__init__(
            user_id=user_id,
            broker_id=broker_id,
            connection_status=connection_status,
            last_connected=last_connected,
            expires_at=expires_at,
            **kwargs
        )
        self._encryption_util = EncryptionUtil(key=settings.encryption_key)

        # Assign and encrypt if provided as string
        self.api_key = self._encryption_util.encrypt(api_key).encode('utf-8') if api_key else None
        self.api_secret = self._encryption_util.encrypt(api_secret).encode('utf-8') if api_secret else None
        self.access_token = self._encryption_util.encrypt(access_token).encode('utf-8') if access_token else None
        self.refresh_token = self._encryption_util.encrypt(refresh_token).encode('utf-8') if refresh_token else None

    def encrypt_field(self, field_name: str, value: Optional[str]):
        """Encrypts a string value and assigns it to the specified field."""
        if value is not None and isinstance(value, str):
            setattr(self, field_name, self._encryption_util.encrypt(value).encode('utf-8'))
        elif value is None:
            setattr(self, field_name, None)
        # If it's already bytes, assume it's encrypted and do nothing

    def decrypt_field(self, field_name: str) -> Optional[str]:
        """Decrypts a byte value from the specified field and returns it as a string."""
        encrypted_value = getattr(self, field_name)
        if encrypted_value:
            return self._encryption_util.decrypt(encrypted_value.decode('utf-8'))
        return None

    def decrypt_api_key(self) -> Optional[str]:
        return self.decrypt_field('api_key')

    def decrypt_api_secret(self) -> Optional[str]:
        return self.decrypt_field('api_secret')

    def decrypt_access_token(self) -> Optional[str]:
        return self.decrypt_field('access_token')

    def decrypt_refresh_token(self) -> Optional[str]:
        return self.decrypt_field('refresh_token')

    @property
    def decrypted_api_key(self) -> Optional[str]:
        return self.decrypt_api_key()

    @property
    def decrypted_api_secret(self) -> Optional[str]:
        return self.decrypt_api_secret()

    @property
    def decrypted_access_token(self) -> Optional[str]:
        return self.decrypt_access_token()

    @property
    def decrypted_refresh_token(self) -> Optional[str]:
        return self.decrypt_refresh_token()

    def __repr__(self):
        return f"<BrokerageConnection(id={self.id}, user_id={self.user_id}, broker_id={self.broker_id}, status='{self.connection_status}')>"