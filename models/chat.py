from sqlmodel import SQLModel, Field, Relationship, Column, DateTime
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from models import Message, Participant

class ChatBase(SQLModel):
    title: str
    file_name: str
    file_size: int
    upload_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True)))
    participant_count: int = 0
    message_count: int = 0
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None

class Chat(ChatBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Relationships
    messages: List["Message"] = Relationship(back_populates="chat")
    participants: List["Participant"] = Relationship(back_populates="chat")

class ChatCreate(ChatBase):
    pass

class ChatRead(ChatBase):
    id: UUID

class ChatUpdate(SQLModel):
    title: Optional[str] = None
    participant_count: Optional[int] = None
    message_count: Optional[int] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None