from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func, and_, Integer
from models.chat import Chat
from models.message import Message, MessageType
from models.participant import Participant
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Any, Tuple
from uuid import UUID
import re
from urllib.parse import urlparse

class ChatAnalyzer:
    """Comprehensive chat analysis service"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Common words to filter out (can be expanded)
        self.stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'throughout', 'despite',
            'towards', 'upon', 'concerning', 'a', 'an', 'as', 'are', 'was', 'were',
            'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'should', 'could', 'can', 'cannot', 'may', 'might', 'must', 'shall',
            'is', 'am', 'it', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
            'she', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your',
            'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours',
            'theirs', 'myself', 'yourself', 'himself', 'herself', 'itself',
            'ourselves', 'yourselves', 'themselves'
        }
    
    async def get_comprehensive_analysis(self, chat_id: UUID) -> Dict[str, Any]:
        """Get comprehensive analysis of the chat"""
        
        # Run all analysis functions
        basic_stats = await self.get_basic_stats(chat_id)
        timeline_data = await self.get_timeline_data(chat_id, "daily")
        participant_stats = await self.get_participant_statistics(chat_id)
        content_analysis = await self.get_content_analysis(chat_id)
        activity_patterns = await self.get_activity_patterns(chat_id)
        conversation_insights = await self.get_conversation_insights(chat_id)
        
        # Import the extended analyzer here to avoid circular imports
        from .analyzer_extended import ExtendedChatAnalyzer
        extended = ExtendedChatAnalyzer(self.session)
        
        # New comprehensive analyses
        activity_over_time = await extended.get_activity_over_time(chat_id, "daily")
        hourly_heatmap = await extended.get_hourly_activity_heatmap(chat_id)
        user_statistics = await extended.get_user_statistics(chat_id)
        interaction_metrics = await extended.get_interaction_metrics(chat_id)
        user_word_clouds = await extended.get_user_word_clouds(chat_id)
        extended_content = await extended.get_content_analysis(chat_id)
        
        return {
            "basic_stats": basic_stats,
            "timeline": timeline_data,
            "participants": participant_stats,
            "content": content_analysis,
            "activity_patterns": activity_patterns,
            "insights": conversation_insights,
            "activity_over_time": activity_over_time,
            "hourly_heatmap": hourly_heatmap,
            "user_statistics": user_statistics,
            "interaction_metrics": interaction_metrics,
            "user_word_clouds": user_word_clouds,
            "extended_content": extended_content
        }
    
    async def get_basic_stats(self, chat_id: UUID) -> Dict[str, Any]:
        """Get basic statistics about the chat"""
        
        # Total messages
        total_messages_query = select(func.count()).select_from(Message).where(Message.chat_id == chat_id)
        total_messages_result = await self.session.execute(total_messages_query)
        total_messages = total_messages_result.scalar()
        
        # Participant count
        participant_count_query = select(func.count()).select_from(Participant).where(Participant.chat_id == chat_id)
        participant_count_result = await self.session.execute(participant_count_query)
        participant_count = participant_count_result.scalar()
        
        # Date range
        date_range_query = select(
            func.min(Message.timestamp).label("first_message"),
            func.max(Message.timestamp).label("last_message")
        ).where(Message.chat_id == chat_id)
        date_range_result = await self.session.execute(date_range_query)
        date_range = date_range_result.first()
        
        # Calculate average messages per day
        if date_range and date_range.first_message and date_range.last_message:
            days_diff = (date_range.last_message - date_range.first_message).days + 1
            avg_messages_per_day = total_messages / days_diff if days_diff > 0 else 0
        else:
            avg_messages_per_day = 0
        
        # Message types distribution
        message_types_query = select(
            Message.message_type,
            func.count()
        ).where(Message.chat_id == chat_id).group_by(Message.message_type)
        
        message_types_result = await self.session.execute(message_types_query)
        message_types = {row[0]: row[1] for row in message_types_result.all()}
        
        return {
            "total_messages": total_messages,
            "participant_count": participant_count,
            "first_message": date_range.first_message.isoformat() if date_range and date_range.first_message else None,
            "last_message": date_range.last_message.isoformat() if date_range and date_range.last_message else None,
            "avg_messages_per_day": round(avg_messages_per_day, 2),
            "message_types": message_types
        }
    
    async def get_timeline_data(self, chat_id: UUID, period: str = "daily") -> Dict[str, Any]:
        """Get timeline data for messages"""
        
        if period == "daily":
            stmt = select(
                func.date(Message.timestamp).label("date"),
                func.count().label("count")
            ).where(Message.chat_id == chat_id).group_by(func.date(Message.timestamp)).order_by("date")
        elif period == "weekly":
            stmt = select(
                func.strftime('%Y-W%W', Message.timestamp).label("week"),
                func.count().label("count")
            ).where(Message.chat_id == chat_id).group_by(func.strftime('%Y-W%W', Message.timestamp)).order_by("week")
        else:  # monthly
            stmt = select(
                func.strftime('%Y-%m', Message.timestamp).label("month"),
                func.count().label("count")
            ).where(Message.chat_id == chat_id).group_by(func.strftime('%Y-%m', Message.timestamp)).order_by("month")
        
        result = await self.session.execute(stmt)
        data = result.all()
        
        return {
            "period": period,
            "data": [{"date": str(row[0]), "count": row[1]} for row in data]
        }
    
    async def get_participant_statistics(self, chat_id: UUID) -> Dict[str, Any]:
        """Get participant statistics"""
        
        # Message distribution by participant
        stmt = select(
            Participant.name,
            func.count().label("message_count"),
            func.avg(Message.char_count).label("avg_chars"),
            func.sum(func.cast(Message.has_emoji, Integer)).label("emoji_count"),
            func.sum(func.cast(Message.has_link, Integer)).label("link_count"),
            func.min(Message.timestamp).label("first_message"),
            func.max(Message.timestamp).label("last_message")
        ).select_from(
            Message.__table__.join(Participant.__table__)
        ).where(
            Message.chat_id == chat_id
        ).group_by(Participant.name).order_by(func.count().desc())
        
        result = await self.session.execute(stmt)
        participants = result.all()
        
        participant_list = []
        for p in participants:
            participant_list.append({
                "name": p.name,
                "message_count": p.message_count,
                "avg_chars": round(float(p.avg_chars or 0), 1),
                "emoji_count": p.emoji_count or 0,
                "link_count": p.link_count or 0,
                "first_message": p.first_message.isoformat() if p.first_message else None,
                "last_message": p.last_message.isoformat() if p.last_message else None
            })
        
        return {
            "message_distribution": participant_list,
            "total_participants": len(participant_list)
        }
    
    async def get_content_analysis(self, chat_id: UUID) -> Dict[str, Any]:
        """Get content analysis"""
        
        # Get basic content stats
        content_stats_query = select(
            func.count().label("total_messages"),
            func.sum(Message.char_count).label("total_chars"),
            func.sum(Message.word_count).label("total_words"),
            func.sum(func.cast(Message.has_emoji, Integer)).label("total_emojis"),
            func.sum(func.cast(Message.has_link, Integer)).label("total_links")
        ).where(Message.chat_id == chat_id)
        
        content_result = await self.session.execute(content_stats_query)
        stats = content_result.first()
        
        return {
            "total_messages": stats.total_messages or 0,
            "total_chars": stats.total_chars or 0,
            "total_words": stats.total_words or 0,
            "total_emojis": stats.total_emojis or 0,
            "total_links": stats.total_links or 0,
            "avg_chars_per_message": round((stats.total_chars or 0) / max(stats.total_messages or 1, 1), 1),
            "avg_words_per_message": round((stats.total_words or 0) / max(stats.total_messages or 1, 1), 1)
        }
    
    async def get_activity_patterns(self, chat_id: UUID) -> Dict[str, Any]:
        """Get activity patterns"""
        
        # Hourly distribution
        hourly_stmt = select(
            func.strftime('%H', Message.timestamp).label("hour"),
            func.count().label("count")
        ).where(Message.chat_id == chat_id).group_by(func.strftime('%H', Message.timestamp)).order_by("hour")
        
        hourly_result = await self.session.execute(hourly_stmt)
        hourly_data = hourly_result.all()
        
        # Daily distribution
        daily_stmt = select(
            func.strftime('%w', Message.timestamp).label("day"),
            func.count().label("count")
        ).where(Message.chat_id == chat_id).group_by(func.strftime('%w', Message.timestamp)).order_by("day")
        
        daily_result = await self.session.execute(daily_stmt)
        daily_data = daily_result.all()
        
        return {
            "hourly_distribution": [{"hour": int(row.hour), "count": row.count} for row in hourly_data],
            "daily_distribution": [{"day": int(row.day), "count": row.count} for row in daily_data]
        }
    
    async def get_conversation_insights(self, chat_id: UUID) -> Dict[str, Any]:
        """Get conversation insights"""
        
        # Most active day
        most_active_day_stmt = select(
            func.date(Message.timestamp).label("date"),
            func.count().label("count")
        ).where(Message.chat_id == chat_id).group_by(func.date(Message.timestamp)).order_by(func.count().desc()).limit(1)
        
        most_active_result = await self.session.execute(most_active_day_stmt)
        most_active = most_active_result.first()
        
        return {
            "most_active_day": {
                "date": str(most_active.date) if most_active else None,
                "message_count": most_active.count if most_active else 0
            }
        }
    
    # Extended analysis methods are delegated to ExtendedChatAnalyzer
    async def get_activity_over_time(self, chat_id: UUID, period: str = "daily") -> Dict[str, Any]:
        from .analyzer_extended import ExtendedChatAnalyzer
        extended = ExtendedChatAnalyzer(self.session)
        return await extended.get_activity_over_time(chat_id, period)
    
    async def get_hourly_activity_heatmap(self, chat_id: UUID) -> Dict[str, Any]:
        from .analyzer_extended import ExtendedChatAnalyzer
        extended = ExtendedChatAnalyzer(self.session)
        return await extended.get_hourly_activity_heatmap(chat_id)
    
    async def get_user_statistics(self, chat_id: UUID) -> Dict[str, Any]:
        from .analyzer_extended import ExtendedChatAnalyzer
        extended = ExtendedChatAnalyzer(self.session)
        return await extended.get_user_statistics(chat_id)
    
    async def get_interaction_metrics(self, chat_id: UUID) -> Dict[str, Any]:
        from .analyzer_extended import ExtendedChatAnalyzer
        extended = ExtendedChatAnalyzer(self.session)
        return await extended.get_interaction_metrics(chat_id)
    
    async def get_user_word_clouds(self, chat_id: UUID) -> Dict[str, Any]:
        from .analyzer_extended import ExtendedChatAnalyzer
        extended = ExtendedChatAnalyzer(self.session)
        return await extended.get_user_word_clouds(chat_id)
    
    async def get_extended_content_analysis(self, chat_id: UUID) -> Dict[str, Any]:
        from .analyzer_extended import ExtendedChatAnalyzer
        extended = ExtendedChatAnalyzer(self.session)
        return await extended.get_content_analysis(chat_id)
