from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func, and_, Integer, text
from models.chat import Chat
from models.message import Message, MessageType
from models.participant import Participant
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Any, Tuple, Optional
from uuid import UUID
import re
from urllib.parse import urlparse

class ExtendedChatAnalyzer:
    """Extended analysis features for chat data"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Common words to filter out
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
    
    async def get_activity_over_time(self, chat_id: UUID, period: str = "daily") -> Dict[str, Any]:
        """Get detailed activity over time analysis"""
        
        # Messages per day/week/month
        if period == "daily":
            # Group by date
            stmt = select(
                func.date(Message.timestamp).label("date"),
                func.count().label("count")
            ).where(Message.chat_id == chat_id).group_by(func.date(Message.timestamp)).order_by("date")
        elif period == "weekly":
            # Group by week
            stmt = select(
                func.strftime('%Y-W%W', Message.timestamp).label("week"),
                func.count().label("count")
            ).where(Message.chat_id == chat_id).group_by(func.strftime('%Y-W%W', Message.timestamp)).order_by("week")
        elif period == "monthly":
            # Group by month
            stmt = select(
                func.strftime('%Y-%m', Message.timestamp).label("month"),
                func.count().label("count")
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
            "data": [{"period": getattr(row, period == "daily" and "date" or (period == "weekly" and "week" or "month")), "count": row.count} for row in time_data],
            "first_message": timestamps.first.isoformat() if timestamps and timestamps.first else None,
            "last_message": timestamps.last.isoformat() if timestamps and timestamps.last else None
        }
    
    async def get_hourly_activity_heatmap(self, chat_id: UUID) -> Dict[str, Any]:
        """Get hourly message distribution heatmap data"""
        
        # Get messages grouped by hour and day of week
        stmt = select(
            func.strftime('%w', Message.timestamp).label("day_of_week"),  # 0=Sunday, 6=Saturday
            func.strftime('%H', Message.timestamp).label("hour"),
            func.count().label("count")
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
            count = int(row.count)
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
            func.count().label("message_count")
        ).select_from(
            Message.__table__.join(Participant.__table__)
        ).where(
            Message.chat_id == chat_id
        ).group_by(Participant.name).order_by(func.count().desc())
        
        messages_result = await self.session.execute(messages_per_user_stmt)
        messages_per_user = messages_result.all()
        
        # Average message length per user
        avg_length_stmt = select(
            Participant.name,
            func.avg(func.length(Message.content)).label("avg_length")
        ).select_from(
            Message.__table__.join(Participant.__table__)
        ).where(
            Message.chat_id == chat_id,
            Message.content.isnot(None)
        ).group_by(Participant.name)
        
        avg_length_result = await self.session.execute(avg_length_stmt)
        avg_lengths = {row.name: round(float(row.avg_length), 1) for row in avg_length_result.all()}
        
        # Get emoji usage per user
        emoji_usage = await self._get_emoji_usage_per_user(chat_id, [row.name for row in messages_per_user])
        
        return {
            "messages_per_user": [{"name": row.name, "count": row.message_count} for row in messages_per_user],
            "avg_message_length": avg_lengths,
            "emoji_usage": emoji_usage
        }
    
    async def _get_emoji_usage_per_user(self, chat_id: UUID, user_names: List[str]) -> Dict[str, Dict[str, int]]:
        """Helper method to get emoji usage per user"""
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
        
        emoji_usage = {}
        
        for user_name in user_names:
            # Get all messages for this user
            user_messages_stmt = select(Message.content).select_from(
                Message.__table__.join(Participant.__table__)
            ).where(
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
        
        return emoji_usage
    
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
            Message.timestamp,
            Participant.name.label("sender"),
            Message.content
        ).select_from(
            Message.__table__.join(Participant.__table__)
        ).where(
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
    
    async def get_user_word_clouds(self, chat_id: UUID) -> Dict[str, List[Dict[str, Any]]]:
        """Get word clouds per user"""
        
        # Get participants
        participants_stmt = select(Participant.name).select_from(
            Message.__table__.join(Participant.__table__)
        ).where(
            Message.chat_id == chat_id
        ).distinct()
        
        participants_result = await self.session.execute(participants_stmt)
        participants = participants_result.scalars().all()
        
        user_word_clouds = {}
        
        for participant_name in participants:
            # Get messages for this participant
            user_messages_stmt = select(Message.content).select_from(
                Message.__table__.join(Participant.__table__)
            ).where(
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
