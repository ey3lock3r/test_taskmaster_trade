from datetime import datetime, timezone # Import timezone
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone # Import timezone

class BaseModel(SQLModel):
    """Base model for database models."""
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False, sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)})
    is_active: bool = Field(default=True)