from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from database import get_session
from models.chat import Chat
from models.message import Message
from models.participant import Participant
from services.analyzer import ChatAnalyzer
from typing import Dict, Any
from uuid import UUID

router = APIRouter()

@router.get("/analysis/{chat_id}")
async def get_chat_analysis(
    chat_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Get comprehensive analysis for a chat"""
    
    # Verify chat exists
    chat = await session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get analyzer
    analyzer = ChatAnalyzer(session)
    
    # Get all analysis data
    analysis_data = await analyzer.get_comprehensive_analysis(chat_id)
    
    return {
        "chat_id": str(chat_id),
        "chat_info": {
            "title": chat.title,
            "participant_count": chat.participant_count,
            "message_count": chat.message_count,
            "date_range": {
                "start": chat.date_range_start.isoformat() if chat.date_range_start else None,
                "end": chat.date_range_end.isoformat() if chat.date_range_end else None
            }
        },
        "analysis": analysis_data
    }

@router.get("/stats/{chat_id}")
async def get_chat_stats(
    chat_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Get basic statistics for a chat"""
    
    # Verify chat exists
    chat = await session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    analyzer = ChatAnalyzer(session)
    
    # Get basic stats
    stats = await analyzer.get_basic_stats(chat_id)
    
    return {
        "chat_id": str(chat_id),
        "stats": stats
    }

@router.get("/insights/{chat_id}")
async def get_chat_insights(
    chat_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Get conversation insights for a chat"""
    
    # Verify chat exists
    chat = await session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    analyzer = ChatAnalyzer(session)
    
    # Get insights
    insights = await analyzer.get_conversation_insights(chat_id)
    
    return {
        "chat_id": str(chat_id),
        "insights": insights
    }

@router.get("/timeline/{chat_id}")
async def get_chat_timeline(
    chat_id: UUID,
    granularity: str = "daily",  # daily, weekly, monthly
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Get message timeline data for charts"""
    
    # Verify chat exists
    chat = await session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    if granularity not in ["daily", "weekly", "monthly"]:
        raise HTTPException(
            status_code=400, 
            detail="Granularity must be 'daily', 'weekly', or 'monthly'"
        )
    
    analyzer = ChatAnalyzer(session)
    
    # Get timeline data
    timeline_data = await analyzer.get_timeline_data(chat_id, granularity)
    
    return {
        "chat_id": str(chat_id),
        "granularity": granularity,
        "timeline": timeline_data
    }

@router.get("/wordcloud/{chat_id}")
async def get_wordcloud_data(
    chat_id: UUID,
    limit: int = 100,
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Get word frequency data for word clouds"""
    
    # Verify chat exists
    chat = await session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    analyzer = ChatAnalyzer(session)
    
    # Get word frequency data
    word_data = await analyzer.get_word_frequency(chat_id, limit)
    
    return {
        "chat_id": str(chat_id),
        "words": word_data
    }

@router.get("/activity-heatmap/{chat_id}")
async def get_activity_heatmap(
    chat_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Get activity heatmap data (hour of day vs day of week)"""
    
    # Verify chat exists
    chat = await session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    analyzer = ChatAnalyzer(session)
    
    # Get heatmap data
    heatmap_data = await analyzer.get_activity_heatmap(chat_id)
    
    return {
        "chat_id": str(chat_id),
        "heatmap": heatmap_data
    }

@router.delete("/chat/{chat_id}")
async def delete_chat(
    chat_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> Dict[str, str]:
    """Delete a chat and all associated data"""
    
    # Verify chat exists
    chat = await session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Delete messages first (due to foreign key constraints)
    messages_query = select(Message).where(Message.chat_id == chat_id)
    messages_result = await session.execute(messages_query)
    messages = messages_result.all()
    
    for message in messages:
        await session.delete(message)
    
    # Delete participants
    participants_query = select(Participant).where(Participant.chat_id == chat_id)
    participants_result = await session.execute(participants_query)
    participants = participants_result.all()
    
    for participant in participants:
        await session.delete(participant)
    
    # Delete chat
    await session.delete(chat)
    await session.commit()
    
    return {"message": f"Chat {chat_id} deleted successfully"}