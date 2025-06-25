import re
from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

class WhatsAppParser:
    """Parser for WhatsApp chat export files"""
    
    def __init__(self):
        # Regex patterns for different WhatsApp date formats (with square brackets)
        self.date_patterns = [
            r'\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2}:\d{2}?\s*(?:AM|PM)?)\]',
            r'\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2})\]',
            r'\[(\d{4}-\d{2}-\d{2})\s*(\d{2}:\d{2}:\d{2})\]',
        ]
        
        # System messages patterns
        self.system_messages = [
            'Messages and calls are end-to-end encrypted',
            'created group',
            'added',
            'removed',
            'left',
            'changed the group description',
            'changed this group\'s icon'
        ]
    
    async def parse_chat(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Parse WhatsApp chat content"""
        
        # Decode content
        text_content = content.decode('utf-8', errors='ignore')
        lines = text_content.split('\n')
        
        messages = []
        participants = set()
        date_range = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Try to parse message
            message_data = self._parse_message_line(line)
            if message_data:
                messages.append(message_data)
                participants.add(message_data['participant'])
                date_range.append(message_data['timestamp'])
        
        return {
            "title": filename.replace('.txt', '').replace('_', ' '),
            "messages": messages,
            "participants": list(participants),
            "date_range_start": min(date_range) if date_range else None,
            "date_range_end": max(date_range) if date_range else None
        }
    
    def _parse_message_line(self, line: str) -> Dict[str, Any] | None:
        """Parse individual message line"""
        
        # Try different date patterns
        for pattern in self.date_patterns:
            match = re.match(pattern, line)
            if match:
                date_str, time_str = match.groups()
                timestamp_str = f"{date_str} {time_str}"
                
                # Extract message content after timestamp and closing bracket
                remaining = line[match.end():].strip()
                
                # Parse participant and message - WhatsApp format: "Participant Name: Message content"
                if ':' in remaining:
                    first_colon = remaining.index(':')
                    participant = remaining[:first_colon].strip()
                    message_content = remaining[first_colon + 1:].strip()
                    
                    # Parse timestamp
                    timestamp = self._parse_timestamp(timestamp_str)
                    if not timestamp:
                        continue
                    
                    # Skip if it's a system message (no participant name)
                    if any(sys_msg in message_content.lower() for sys_msg in self.system_messages):
                        continue
                    
                    # Determine message type
                    msg_type = self._determine_message_type(message_content)
                    
                    return {
                        "timestamp": timestamp,
                        "participant": participant,
                        "content": message_content,
                        "message_type": msg_type,
                        "char_count": len(message_content),
                        "word_count": len(message_content.split()),
                        "has_emoji": self._has_emoji(message_content),
                        "has_link": self._has_link(message_content)
                    }
        
        return None
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime | None:
        """Parse timestamp string to datetime"""
        formats = [
            "%m/%d/%Y, %I:%M:%S %p",
            "%m/%d/%Y, %I:%M %p",
            "%m/%d/%y, %I:%M:%S %p",
            "%m/%d/%y, %I:%M %p",
            "%d/%m/%Y, %H:%M:%S",
            "%d/%m/%Y, %H:%M",
            "%Y-%m-%d %H:%M:%S",
            # Formats without comma (common in WhatsApp exports)
            "%m/%d/%y %I:%M:%S %p",
            "%m/%d/%Y %I:%M:%S %p",
            "%m/%d/%y %I:%M %p",
            "%m/%d/%Y %I:%M %p",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _determine_message_type(self, content: str) -> str:
        """Determine message type"""
        if any(sys_msg in content.lower() for sys_msg in self.system_messages):
            return "system"
        elif "<Media omitted>" in content or "image omitted" in content.lower():
            return "media"
        elif "This message was deleted" in content:
            return "deleted"
        else:
            return "text"
    
    def _has_emoji(self, text: str) -> bool:
        """Check if text contains emojis"""
        # Simple emoji detection - can be improved
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        return bool(emoji_pattern.search(text))
    
    def _has_link(self, text: str) -> bool:
        """Check if text contains links"""
        link_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return bool(re.search(link_pattern, text))
    
    async def store_chat_data(self, session: AsyncSession, chat_id: uuid.UUID, chat_data: Dict):
        """Store parsed chat data in database"""
        from models.participant import Participant
        from models.message import Message
        
        # Store participants
        participant_map = {}
        for participant_name in chat_data["participants"]:
            participant = Participant(
                chat_id=chat_id,
                name=participant_name,
                message_count=sum(1 for msg in chat_data["messages"] if msg["participant"] == participant_name)
            )
            session.add(participant)
            await session.flush()
            participant_map[participant_name] = participant.id
        
        # Store messages
        for msg_data in chat_data["messages"]:
            message = Message(
                chat_id=chat_id,
                participant_id=participant_map[msg_data["participant"]],
                content=msg_data["content"],
                timestamp=msg_data["timestamp"],
                message_type=msg_data["message_type"],
                char_count=msg_data["char_count"],
                word_count=msg_data["word_count"],
                has_emoji=msg_data["has_emoji"],
                has_link=msg_data["has_link"]
            )
            session.add(message)
        
        await session.commit()