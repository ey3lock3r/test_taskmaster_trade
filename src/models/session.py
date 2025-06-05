from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, Relationship, SQLModel
import uuid
from src.model.base import BaseModel # Import BaseModel

class Session(BaseModel, table=True):
    __tablename__ = 'sessions'

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(default_factory=lambda: uuid.uuid4().hex, unique=True, index=True, max_length=36)
    user_id: int = Field(foreign_key="users.id")
    access_token: str = Field(max_length=512)
    refresh_token: str = Field(max_length=512)
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    logged_out_at: Optional[datetime] = None

    user: "User" = Relationship(back_populates="sessions")

    def is_expired(self) -> bool:
        return self.expires_at < datetime.now(timezone.utc)

    def validate(self) -> bool:
        return self.is_active and not self.is_expired()

    def delete(self):
        self.is_active = False
        self.logged_out_at = datetime.now(timezone.utc)

    def __repr__(self):
       return f"<Session(session_id='{self.session_id}', expires_at={self.expires_at})>"