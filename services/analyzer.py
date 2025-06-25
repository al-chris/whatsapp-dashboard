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
from .analyzer_extended import ExtendedChatAnalyzer

class ChatAnalyzer:
    """Comprehensive chat analysis service"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.extended = ExtendedChatAnalyzer(session)
        
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
        
        # New comprehensive analyses
        activity_over_time = await self.extended.get_activity_over_time(chat_id, "daily")
        hourly_heatmap = await self.extended.get_hourly_activity_heatmap(chat_id)
        user_statistics = await self.extended.get_user_statistics(chat_id)
        interaction_metrics = await self.extended.get_interaction_metrics(chat_id)
        user_word_clouds = await self.extended.get_user_word_clouds(chat_id)
        extended_content = await self.extended.get_content_analysis(chat_id)
        
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
        """Get basic chat statistics"""
        
        # Get total message count
        total_messages_query = select(func.count(Message.id)).where(Message.chat_id == chat_id)
        total_messages_result = await self.session.execute(total_messages_query)
        total_messages = total_messages_result.scalar_one()
        
        # Get participant count
        participant_count_query = select(func.count(Participant.id)).where(Participant.chat_id == chat_id)
        participant_count_result = await self.session.execute(participant_count_query)
        participant_count = participant_count_result.scalar_one()
        
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
        message_type_counts = {row[0]: row[1] for row in message_types_result.all()}
        
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
            func.sum(func.cast(Message.has_emoji, Integer)).label("emoji_count"),
            func.sum(func.cast(Message.has_link, Integer)).label("link_count"),
            func.min(Message.timestamp).label("first_message"),
            func.max(Message.timestamp).label("last_message")
        ).select_from(
            Participant.__table__.join(Message.__table__)
        ).where(
            Participant.chat_id == chat_id
        ).group_by(Participant.id, Participant.name)
        
        participant_stats_result = await self.session.execute(participant_stats_query)
        participant_stats = participant_stats_result.mappings().all()
        
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
        timeline_data = timeline_result.all()
        
        return [
            {
                "period": row[0],
                "message_count": row[1]
            }
            for row in timeline_data
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
        heatmap_data = heatmap_result.all()
        
        # Create 2D array for heatmap (7 days x 24 hours)
        heatmap_matrix = [[0 for _ in range(24)] for _ in range(7)]
        
        for row in heatmap_data:
            day_idx = int(row[0])
            hour_idx = int(row[1])
            heatmap_matrix[day_idx][hour_idx] = row[2]
        
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
        hourly_data = {row[0]: row[1] for row in hourly_result.all()}
        
        # Get daily distribution
        daily_query = select(
            func.strftime('%w', Message.timestamp).label("day_of_week"),
            func.count(Message.id).label("message_count")
        ).where(
            Message.chat_id == chat_id
        ).group_by(func.strftime('%w', Message.timestamp))
        
        daily_result = await self.session.execute(daily_query)
        daily_data = {row[0]: row[1] for row in daily_result.all()}
        
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
        conversation_starters = {row[0]: row[1] for row in starters_result.all()}
        
        return {
            "most_active_hour": activity_patterns["peak_hour"],
            "most_active_day": activity_patterns["peak_day"],
            "conversation_starters": conversation_starters,
            "most_engaged_participant": participant_stats[0]["name"] if participant_stats else None,
            "average_message_length": sum(p["avg_message_length"] for p in participant_stats) / len(participant_stats) if participant_stats else 0
        }
    
    async def get_activity_over_time(self, chat_id: UUID, period: str = "daily") -> Dict[str, Any]:
        """Get detailed activity over time analysis"""
        
        # Messages per day/week/month
        if period == "daily":
            # Group by date
            stmt = select(
                func.date(Message.timestamp).label("date"),
                func.count(Message.id).label("count")
            ).where(Message.chat_id == chat_id).group_by(func.date(Message.timestamp)).order_by("date")
        elif period == "weekly":
            # Group by week
            stmt = select(
                func.strftime('%Y-W%W', Message.timestamp).label("week"),
                func.count(Message.id).label("count")
            ).where(Message.chat_id == chat_id).group_by(func.strftime('%Y-W%W', Message.timestamp)).order_by("week")
        elif period == "monthly":
            # Group by month
            stmt = select(
                func.strftime('%Y-%m', Message.timestamp).label("month"),
                func.count(Message.id).label("count")
            ).where(Message.chat_id == chat_id).group_by(func.strftime('%Y-%m', Message.timestamp)).order_by("month")
        
        result = await self.session.execute(stmt)
        time_data = result.all()
        
        # First and last message timestamps
        first_last_stmt = select(
            func.min(Message.timestamp).label("first"),
            func.max(Message.timestamp).label("last")
        ).where(Message.chat_id == chat_id)
        
        first_last_result = await self.session.execute(first_last_stmt)
        timestamps = first_last_result.first()
        
        return {
            "period": period,
            "data": [{"period": row.date if period == "daily" else (row.week if period == "weekly" else row.month), "count": row.count} for row in time_data],
            "first_message": timestamps.first.isoformat() if timestamps.first else None,
            "last_message": timestamps.last.isoformat() if timestamps.last else None
        }
    
    async def get_hourly_activity_heatmap(self, chat_id: UUID) -> Dict[str, Any]:
        """Get hourly message distribution heatmap data"""
        
        # Get messages grouped by hour and day of week
        stmt = select(
            func.strftime('%w', Message.timestamp).label("day_of_week"),  # 0=Sunday, 6=Saturday
            func.strftime('%H', Message.timestamp).label("hour"),
            func.count(Message.id).label("count")
        ).where(Message.chat_id == chat_id).group_by(
            func.strftime('%w', Message.timestamp),
            func.strftime('%H', Message.timestamp)
        )
        
        result = await self.session.execute(stmt)
        heatmap_data = result.all()
        
        # Create a 7x24 matrix (days x hours)
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        hours = [f"{h:02d}:00" for h in range(24)]
        
        # Initialize matrix with zeros
        matrix = [[0 for _ in range(24)] for _ in range(7)]
        max_count = 0
        
        # Fill matrix with actual data
        for row in heatmap_data:
            day_idx = int(row.day_of_week)
            hour_idx = int(row.hour)
            count = row.count
            matrix[day_idx][hour_idx] = count
            max_count = max(max_count, count)
        
        return {
            "days": days,
            "hours": hours,
            "data": matrix,
            "max_count": max_count
        }
    
    async def get_user_statistics(self, chat_id: UUID) -> Dict[str, Any]:
        """Get comprehensive user statistics for group chats"""
        
        # Total messages per user
        messages_per_user_stmt = select(
            Participant.name,
            func.count(Message.id).label("message_count")
        ).join(Message).where(
            Message.chat_id == chat_id
        ).group_by(Participant.id, Participant.name).order_by(func.count(Message.id).desc())
        
        messages_result = await self.session.execute(messages_per_user_stmt)
        messages_per_user = messages_result.all()
        
        # Average message length per user
        avg_length_stmt = select(
            Participant.name,
            func.avg(func.length(Message.content)).label("avg_length"),
            func.count(Message.id).label("total_messages")
        ).join(Message).where(
            Message.chat_id == chat_id,
            Message.content.isnot(None)
        ).group_by(Participant.id, Participant.name)
        
        avg_length_result = await self.session.execute(avg_length_stmt)
        avg_lengths = {row.name: round(row.avg_length, 1) for row in avg_length_result.all()}
        
        # Emoji usage per user
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
        
        emoji_usage = {}
        for user_data in messages_per_user:
            user_name = user_data.name
            
            # Get all messages for this user
            user_messages_stmt = select(Message.content).join(Participant).where(
                Message.chat_id == chat_id,
                Participant.name == user_name,
                Message.content.isnot(None)
            )
            
            user_messages_result = await self.session.execute(user_messages_stmt)
            user_messages = user_messages_result.scalars().all()
            
            # Count emojis
            emoji_count = 0
            emoji_types = set()
            for content in user_messages:
                if content:
                    emojis = emoji_pattern.findall(content)
                    emoji_count += len(emojis)
                    emoji_types.update(emojis)
            
            emoji_usage[user_name] = {
                "count": emoji_count,
                "unique_emojis": len(emoji_types)
            }
        
        return {
            "messages_per_user": [{"name": row.name, "count": row.message_count} for row in messages_per_user],
            "avg_message_length": avg_lengths,
            "emoji_usage": emoji_usage
        }
    
    async def get_content_analysis(self, chat_id: UUID) -> Dict[str, Any]:
        """Get content-based analysis including word clouds and emoji analysis"""
        
        # Get all message content
        content_stmt = select(Message.content).where(
            Message.chat_id == chat_id,
            Message.content.isnot(None)
        )
        
        content_result = await self.session.execute(content_stmt)
        all_content = content_result.scalars().all()
        
        # Word frequency analysis
        word_freq = Counter()
        emoji_freq = Counter()
        link_domains = Counter()
        
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
        url_pattern = re.compile(r'https?://(?:[-\w.])+(?:\.[a-zA-Z]{2,})+(?:/[^?\s]*)?(?:\?[^#\s]*)?(?:#[^\s]*)?')
        
        for content in all_content:
            if not content:
                continue
                
            # Extract and count emojis
            emojis = emoji_pattern.findall(content)
            emoji_freq.update(emojis)
            
            # Extract and count domain names from URLs
            urls = url_pattern.findall(content)
            for url in urls:
                try:
                    domain = urlparse(url).netloc
                    if domain:
                        link_domains[domain] += 1
                except:
                    pass
            
            # Clean text for word analysis (remove emojis and URLs)
            clean_text = emoji_pattern.sub('', content)
            clean_text = url_pattern.sub('', clean_text)
            
            # Extract words
            words = re.findall(r'\b[a-zA-Z]{3,}\b', clean_text.lower())
            # Filter out stop words
            filtered_words = [word for word in words if word not in self.stop_words]
            word_freq.update(filtered_words)
        
        return {
            "word_cloud": [{"word": word, "count": count} for word, count in word_freq.most_common(50)],
            "emoji_analysis": [{"emoji": emoji, "count": count} for emoji, count in emoji_freq.most_common(20)],
            "shared_domains": [{"domain": domain, "count": count} for domain, count in link_domains.most_common(10)]
        }
    
    async def get_interaction_metrics(self, chat_id: UUID) -> Dict[str, Any]:
        """Get interaction metrics including response times and conversation starters"""
        
        # Get all messages ordered by timestamp
        messages_stmt = select(
            Message.id,
            Message.timestamp,
            Participant.name.label("sender"),
            Message.content
        ).join(Participant).where(
            Message.chat_id == chat_id
        ).order_by(Message.timestamp)
        
        messages_result = await self.session.execute(messages_stmt)
        messages = messages_result.all()
        
        if len(messages) < 2:
            return {
                "response_times": [],
                "conversation_starters": [],
                "longest_pauses": []
            }
        
        # Calculate response times and conversation patterns
        response_times = defaultdict(list)
        conversation_starters = defaultdict(int)
        pauses = []
        
        prev_message = messages[0]
        conversation_starters[prev_message.sender] += 1  # First message is a conversation starter
        
        for i in range(1, len(messages)):
            current_message = messages[i]
            time_diff = (current_message.timestamp - prev_message.timestamp).total_seconds()
            
            # If different sender and within reasonable response time (< 1 hour)
            if (current_message.sender != prev_message.sender and 
                time_diff < 3600 and time_diff > 0):
                response_times[current_message.sender].append(time_diff)
            
            # Long pause detection (> 4 hours)
            if time_diff > 14400:  # 4 hours in seconds
                pauses.append({
                    "duration_hours": round(time_diff / 3600, 1),
                    "before": prev_message.timestamp.isoformat(),
                    "after": current_message.timestamp.isoformat(),
                    "restarted_by": current_message.sender
                })
                conversation_starters[current_message.sender] += 1
            
            prev_message = current_message
        
        # Calculate average response times
        avg_response_times = {}
        for sender, times in response_times.items():
            if times:
                avg_response_times[sender] = {
                    "avg_seconds": round(sum(times) / len(times), 1),
                    "median_seconds": round(sorted(times)[len(times)//2], 1),
                    "response_count": len(times)
                }
        
        return {
            "response_times": [
                {"name": name, **stats} 
                for name, stats in avg_response_times.items()
            ],
            "conversation_starters": [
                {"name": name, "count": count} 
                for name, count in sorted(conversation_starters.items(), key=lambda x: x[1], reverse=True)
            ],
            "longest_pauses": sorted(pauses, key=lambda x: x["duration_hours"], reverse=True)[:10]
        }
    
    async def get_user_word_clouds(self, chat_id: UUID) -> Dict[str, Any]:
        """Get word clouds per user"""
        
        # Get participants
        participants_stmt = select(Participant.name).join(Message).where(
            Message.chat_id == chat_id
        ).distinct()
        
        participants_result = await self.session.execute(participants_stmt)
        participants = participants_result.scalars().all()
        
        user_word_clouds = {}
        
        for participant_name in participants:
            # Get messages for this participant
            user_messages_stmt = select(Message.content).join(Participant).where(
                Message.chat_id == chat_id,
                Participant.name == participant_name,
                Message.content.isnot(None)
            )
            
            user_messages_result = await self.session.execute(user_messages_stmt)
            user_messages = user_messages_result.scalars().all()
            
            # Analyze words for this user
            word_freq = Counter()
            emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
            url_pattern = re.compile(r'https?://(?:[-\w.])+(?:\.[a-zA-Z]{2,})+(?:/[^?\s]*)?(?:\?[^#\s]*)?(?:#[^\s]*)?')
            
            for content in user_messages:
                if not content:
                    continue
                    
                # Clean text
                clean_text = emoji_pattern.sub('', content)
                clean_text = url_pattern.sub('', clean_text)
                
                # Extract words
                words = re.findall(r'\b[a-zA-Z]{3,}\b', clean_text.lower())
                filtered_words = [word for word in words if word not in self.stop_words]
                word_freq.update(filtered_words)
            
            user_word_clouds[participant_name] = [
                {"word": word, "count": count} 
                for word, count in word_freq.most_common(30)
            ]
        
        return user_word_clouds
    
    async def _get_all_messages(self, chat_id: UUID):
        """Helper to get all messages for a chat"""
        messages_query = select(Message).where(Message.chat_id == chat_id)
        result = await self.session.execute(messages_query)
        return result.scalars().all()