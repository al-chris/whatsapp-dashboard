from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func, and_
from models.chat import Chat
from models.message import Message, MessageType
from models.participant import Participant
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Any, Tuple
from uuid import UUID
import re

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
        
        return {
            "basic_stats": basic_stats,
            "timeline": timeline_data,
            "participants": participant_stats,
            "content": content_analysis,
            "activity_patterns": activity_patterns,
            "insights": conversation_insights
        }
    
    async def get_basic_stats(self, chat_id: UUID) -> Dict[str, Any]:
        """Get basic chat statistics"""
        
        # Get total message count
        total_messages_query = select(func.count(Message.id)).where(Message.chat_id == chat_id)
        total_messages_result = await self.session.execute(total_messages_query)
        total_messages = total_messages_result.one()
        
        # Get participant count
        participant_count_query = select(func.count(Participant.id)).where(Participant.chat_id == chat_id)
        participant_count_result = await self.session.execute(participant_count_query)
        participant_count = participant_count_result.one()
        
        # Get date range
        date_range_query = select(
            func.min(Message.timestamp),
            func.max(Message.timestamp)
        ).where(Message.chat_id == chat_id)
        date_range_result = await self.session.execute(date_range_query)
        min_date, max_date = date_range_result.one()
        
        # Calculate duration and average messages per day
        duration_days = 0
        avg_messages_per_day = 0
        
        if min_date and max_date:
            duration_days = (max_date - min_date).days + 1
            avg_messages_per_day = total_messages / duration_days if duration_days > 0 else 0
        
        # Get message type breakdown
        message_types_query = select(
            Message.message_type,
            func.count(Message.id)
        ).where(Message.chat_id == chat_id).group_by(Message.message_type)
        
        message_types_result = await self.session.execute(message_types_query)
        message_type_counts = dict(message_types_result.scalars().all())
        
        return {
            "total_messages": total_messages,
            "participant_count": participant_count,
            "duration_days": duration_days,
            "avg_messages_per_day": round(avg_messages_per_day, 2),
            "date_range": {
                "start": min_date.isoformat() if min_date else None,
                "end": max_date.isoformat() if max_date else None
            },
            "message_types": message_type_counts
        }
    
    async def get_participant_statistics(self, chat_id: UUID) -> List[Dict[str, Any]]:
        """Get detailed statistics for each participant"""
        
        # Get participants with message counts
        participant_stats_query = select(
            Participant.id,
            Participant.name,
            func.count(Message.id).label("message_count"),
            func.avg(Message.char_count).label("avg_message_length"),
            func.sum(Message.char_count).label("total_chars"),
            func.sum(Message.word_count).label("total_words"),
            func.sum(func.cast(Message.has_emoji, int)).label("emoji_count"),
            func.sum(func.cast(Message.has_link, int)).label("link_count"),
            func.min(Message.timestamp).label("first_message"),
            func.max(Message.timestamp).label("last_message")
        ).select_from(
            Participant.__table__.join(Message.__table__)
        ).where(
            Participant.chat_id == chat_id
        ).group_by(Participant.id, Participant.name)
        
        participant_stats_result = await self.session.execute(participant_stats_query)
        participant_stats = participant_stats_result.scalars().all()
        
        results = []
        for stats in participant_stats:
            results.append({
                "id": str(stats.id),
                "name": stats.name,
                "message_count": stats.message_count,
                "avg_message_length": round(stats.avg_message_length or 0, 2),
                "total_characters": stats.total_chars or 0,
                "total_words": stats.total_words or 0,
                "emoji_count": stats.emoji_count or 0,
                "link_count": stats.link_count or 0,
                "first_message": stats.first_message.isoformat() if stats.first_message else None,
                "last_message": stats.last_message.isoformat() if stats.last_message else None
            })
        
        # Sort by message count (descending)
        results.sort(key=lambda x: x["message_count"], reverse=True)
        
        return results
    
    async def get_timeline_data(self, chat_id: UUID, granularity: str = "daily") -> List[Dict[str, Any]]:
        """Get message timeline data"""
        
        if granularity == "daily":
            date_format = "%Y-%m-%d"
        elif granularity == "weekly":
            date_format = "%Y-W%U"  # Year-Week format
        elif granularity == "monthly":
            date_format = "%Y-%m"
        else:
            raise ValueError("Granularity must be 'daily', 'weekly', or 'monthly'")
        
        # Get messages grouped by time period
        if granularity == "daily":
            time_group = func.date(Message.timestamp)
        elif granularity == "weekly":
            time_group = func.strftime('%Y-W%U', Message.timestamp)
        else:  # monthly
            time_group = func.strftime('%Y-%m', Message.timestamp)
        
        timeline_query = select(
            time_group.label("period"),
            func.count(Message.id).label("message_count")
        ).where(
            Message.chat_id == chat_id
        ).group_by(time_group).order_by(time_group)
        
        timeline_result = await self.session.execute(timeline_query)
        timeline_data = timeline_result.scalars().all()
        
        return [
            {
                "period": period,
                "message_count": count
            }
            for period, count in timeline_data
        ]
    
    async def get_word_frequency(self, chat_id: UUID, limit: int = 100) -> List[Dict[str, Any]]:
        """Get word frequency analysis"""
        
        # Get all text messages
        messages_query = select(Message.content).where(
            and_(
                Message.chat_id == chat_id,
                Message.message_type == MessageType.TEXT
            )
        )
        
        messages_result = await self.session.execute(messages_query)
        messages = messages_result.scalars().all()
        
        # Process text and count words
        word_counter = Counter()
        
        for message_content in messages:
            # Clean and tokenize text
            words = self._extract_words(message_content)
            
            # Filter out stop words and short words
            filtered_words = [
                word for word in words
                if len(word) > 2 and word.lower() not in self.stop_words
            ]
            
            word_counter.update(filtered_words)
        
        # Get top words
        top_words = word_counter.most_common(limit)
        
        return [
            {
                "word": word,
                "count": count,
                "frequency": count / sum(word_counter.values()) if word_counter else 0
            }
            for word, count in top_words
        ]
    
    async def get_activity_heatmap(self, chat_id: UUID) -> Dict[str, Any]:
        """Get activity heatmap data (hour vs day of week)"""
        
        # Get messages with hour and day of week
        messages_query = select(
            func.strftime('%w', Message.timestamp).label("day_of_week"),  # 0=Sunday, 6=Saturday
            func.strftime('%H', Message.timestamp).label("hour"),
            func.count(Message.id).label("message_count")
        ).where(
            Message.chat_id == chat_id
        ).group_by(
            func.strftime('%w', Message.timestamp),
            func.strftime('%H', Message.timestamp)
        )
        
        heatmap_result = await self.session.execute(messages_query)
        heatmap_data = heatmap_result.scalars().all()
        
        # Create 2D array for heatmap (7 days x 24 hours)
        heatmap_matrix = [[0 for _ in range(24)] for _ in range(7)]
        
        for day_of_week, hour, count in heatmap_data:
            day_idx = int(day_of_week)
            hour_idx = int(hour)
            heatmap_matrix[day_idx][hour_idx] = count
        
        return {
            "matrix": heatmap_matrix,
            "day_labels": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "hour_labels": [f"{i:02d}:00" for i in range(24)]
        }
    
    async def get_activity_patterns(self, chat_id: UUID) -> Dict[str, Any]:
        """Get activity patterns analysis"""
        
        # Get hourly distribution
        hourly_query = select(
            func.strftime('%H', Message.timestamp).label("hour"),
            func.count(Message.id).label("message_count")
        ).where(
            Message.chat_id == chat_id
        ).group_by(func.strftime('%H', Message.timestamp))
        
        hourly_result = await self.session.execute(hourly_query)
        hourly_data = dict(hourly_result.scalars().all())
        
        # Get daily distribution
        daily_query = select(
            func.strftime('%w', Message.timestamp).label("day_of_week"),
            func.count(Message.id).label("message_count")
        ).where(
            Message.chat_id == chat_id
        ).group_by(func.strftime('%w', Message.timestamp))
        
        daily_result = await self.session.execute(daily_query)
        daily_data = dict(daily_result.scalars().all())
        
        # Find peak activity periods
        peak_hour = max(hourly_data.items(), key=lambda x: x[1])[0] if hourly_data else "00"
        peak_day = max(daily_data.items(), key=lambda x: x[1])[0] if daily_data else "0"
        
        day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        peak_day_name = day_names[int(peak_day)] if peak_day.isdigit() else "Unknown"
        
        return {
            "hourly_distribution": {f"{int(hour):02d}:00": count for hour, count in hourly_data.items()},
            "daily_distribution": {day_names[int(day)]: count for day, count in daily_data.items() if day.isdigit()},
            "peak_hour": f"{int(peak_hour):02d}:00",
            "peak_day": peak_day_name
        }
    
    async def get_conversation_insights(self, chat_id: UUID) -> Dict[str, Any]:
        """Get conversation insights and patterns"""
        
        # Get response time analysis (simplified)
        # This is a basic implementation - can be enhanced with more sophisticated analysis
        
        # Get most active periods
        activity_patterns = await self.get_activity_patterns(chat_id)
        
        # Get participant engagement
        participant_stats = await self.get_participant_statistics(chat_id)
        
        # Calculate conversation starters (first message of each day by participant)
        conversation_starters_query = select(
            Participant.name,
            func.count().label("starter_count")
        ).select_from(
            Message.__table__.join(Participant.__table__)
        ).where(
            and_(
                Message.chat_id == chat_id,
                Message.id.in_(
                    select(func.min(Message.id))
                    .where(Message.chat_id == chat_id)
                    .group_by(func.date(Message.timestamp))
                )
            )
        ).group_by(Participant.name)
        
        starters_result = await self.session.execute(conversation_starters_query)
        conversation_starters = dict(starters_result.scalars().all())
        
        return {
            "most_active_hour": activity_patterns["peak_hour"],
            "most_active_day": activity_patterns["peak_day"],
            "conversation_starters": conversation_starters,
            "most_engaged_participant": participant_stats[0]["name"] if participant_stats else None,
            "average_message_length": sum(p["avg_message_length"] for p in participant_stats) / len(participant_stats) if participant_stats else 0
        }
    
    async def get_content_analysis(self, chat_id: UUID) -> Dict[str, Any]:
        """Get content analysis including emojis, links, etc."""
        
        # Get emoji usage
        emoji_count_query = select(
            func.sum(func.cast(Message.has_emoji, int))
        ).where(Message.chat_id == chat_id)
        emoji_result = await self.session.execute(emoji_count_query)
        total_emojis = emoji_result.one() or 0
        
        # Get link sharing
        link_count_query = select(
            func.sum(func.cast(Message.has_link, int))
        ).where(Message.chat_id == chat_id)
        link_result = await self.session.execute(link_count_query)
        total_links = link_result.one() or 0
        
        # Get word frequency (top 20)
        word_frequency = await self.get_word_frequency(chat_id, 20)
        
        # Get message length distribution
        length_distribution_query = select(
            func.avg(Message.char_count).label("avg_length"),
            func.max(Message.char_count).label("max_length"),
            func.min(Message.char_count).label("min_length")
        ).where(
            and_(
                Message.chat_id == chat_id,
                Message.message_type == MessageType.TEXT
            )
        )
        
        length_result = await self.session.execute(length_distribution_query)
        length_stats = length_result.one()
        
        return {
            "emoji_usage": {
                "total_messages_with_emojis": total_emojis,
                "emoji_frequency": total_emojis / max(1, sum(1 for _ in await self._get_all_messages(chat_id)))
            },
            "link_sharing": {
                "total_messages_with_links": total_links,
                "link_frequency": total_links / max(1, sum(1 for _ in await self._get_all_messages(chat_id)))
            },
            "word_frequency": word_frequency,
            "message_length": {
                "average": round(length_stats.avg_length or 0, 2),
                "maximum": length_stats.max_length or 0,
                "minimum": length_stats.min_length or 0
            }
        }
    
    async def get_summary_report(self, chat_id: UUID) -> Dict[str, Any]:
        """Generate a comprehensive summary report"""
        
        basic_stats = await self.get_basic_stats(chat_id)
        participant_stats = await self.get_participant_statistics(chat_id)
        insights = await self.get_conversation_insights(chat_id)
        content = await self.get_content_analysis(chat_id)
        
        return {
            "summary": {
                "total_messages": basic_stats["total_messages"],
                "duration_days": basic_stats["duration_days"],
                "participants": len(participant_stats),
                "most_active_participant": participant_stats[0]["name"] if participant_stats else None,
                "peak_activity_time": insights["most_active_hour"],
                "peak_activity_day": insights["most_active_day"]
            },
            "highlights": {
                "busiest_day": insights["most_active_day"],
                "most_talkative": participant_stats[0]["name"] if participant_stats else None,
                "emoji_lover": max(participant_stats, key=lambda x: x["emoji_count"])["name"] if participant_stats else None,
                "link_sharer": max(participant_stats, key=lambda x: x["link_count"])["name"] if participant_stats else None
            },
            "statistics": basic_stats,
            "participants": participant_stats[:5],  # Top 5 participants
            "top_words": content["word_frequency"][:10]  # Top 10 words
        }
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text, removing punctuation and special characters"""
        # Remove URLs, mentions, and special WhatsApp formatting
        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'<[^>]+>', '', text)  # Remove media omitted tags
        
        # Extract words (letters only, minimum 2 characters)
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        
        return words
    
    async def _get_all_messages(self, chat_id: UUID):
        """Helper to get all messages for a chat"""
        messages_query = select(Message).where(Message.chat_id == chat_id)
        result = await self.session.execute(messages_query)
        return result.scalars().all()