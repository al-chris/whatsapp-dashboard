from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from services.parser import WhatsAppParser
from models.chat import Chat, ChatCreate
import uuid

router = APIRouter()

@router.post("/upload")
async def upload_chat_file(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    """Upload and process WhatsApp chat file"""
    
    # Validate file type
    if not file.filename.endswith(('.txt', '.zip')):
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .zip files are supported"
        )
    
    # Read file content
    content = await file.read()
    
    # Parse WhatsApp chat
    parser = WhatsAppParser()
    try:
        chat_data = await parser.parse_chat(content, file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error parsing chat file: {str(e)}"
        )
    
    # Create chat record
    chat = Chat(
        title=chat_data.get("title", file.filename),
        file_name=file.filename,
        file_size=len(content),
        participant_count=len(chat_data.get("participants", [])),
        message_count=len(chat_data.get("messages", [])),
        date_range_start=chat_data.get("date_range_start"),
        date_range_end=chat_data.get("date_range_end")
    )
    
    session.add(chat)
    await session.commit()
    await session.refresh(chat)
    
    # Process and store messages and participants
    await parser.store_chat_data(session, chat.id, chat_data)
    
    return {
        "chat_id": str(chat.id),
        "message": "Chat uploaded and processed successfully",
        "stats": {
            "participants": chat.participant_count,
            "messages": chat.message_count,
            "file_size": chat.file_size
        }
    }

@router.get("/uploads")
async def list_uploads(session: AsyncSession = Depends(get_session)):
    """List all uploaded chats"""
    from sqlmodel import select
    
    result = await session.execute(select(Chat))
    chats = result.scalars().all()
    
    return [
        {
            "id": str(chat.id),
            "title": chat.title,
            "upload_date": chat.upload_date.isoformat(),
            "participants": chat.participant_count,
            "messages": chat.message_count
        }
        for chat in chats
    ]