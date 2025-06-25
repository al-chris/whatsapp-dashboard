from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime

if TYPE_CHECKING:
    from models import Message, Chat

class ParticipantBase(SQLModel):
    name: str
    phone_number: Optional[str] = None
    message_count: int = 0
    first_message_date: Optional[datetime] = None
    last_message_date: Optional[datetime] = None

class Participant(ParticipantBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    chat_id: UUID = Field(foreign_key="chat.id")
    
    # Relationships
    chat: "Chat" = Relationship(back_populates="participants")
    messages: List["Message"] = Relationship(back_populates="participant")

class ParticipantCreate(ParticipantBase):
    chat_id: UUID

class ParticipantRead(ParticipantBase):
    id: UUID
    chat_id: UUID