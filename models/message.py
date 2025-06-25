from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from enum import Enum

if TYPE_CHECKING:
    from models import Chat, Participant

class MessageType(str, Enum):
    TEXT = "text"
    MEDIA = "media"
    SYSTEM = "system"
    DELETED = "deleted"

class MessageBase(SQLModel):
    content: str
    timestamp: datetime
    message_type: MessageType = MessageType.TEXT
    char_count: int = 0
    word_count: int = 0
    has_emoji: bool = False
    has_link: bool = False

class Message(MessageBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    chat_id: UUID = Field(foreign_key="chat.id")
    participant_id: UUID = Field(foreign_key="participant.id")
    
    # Relationships
    chat: "Chat" = Relationship(back_populates="messages")
    participant: "Participant" = Relationship(back_populates="messages")

class MessageCreate(MessageBase):
    chat_id: UUID
    participant_id: UUID

class MessageRead(MessageBase):
    id: UUID
    chat_id: UUID
    participant_id: UUID
    timestamp: datetime