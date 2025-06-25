from sqlalchemy.ext.asyncio import AsyncSession
from models.chat import Chat
from models.message import Message, MessageType
from models.participant import Participant
from services.analyzer import ChatAnalyzer
from typing import Dict, List, Any
from uuid import UUID
import csv
import io
import json

class DataExporter:
    """Service for exporting and formatting data for visualizations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.analyzer = ChatAnalyzer(session)
    
    async def get_chart_data(self, chat_id: UUID, chart_type: str) -> Dict[str, Any]:
        """Get data formatted for specific chart types"""
        
        if chart_type == "timeline":
            return await self._get_timeline_chart_data(chat_id)
        elif chart_type == "participants":
            return await self._get_participants_chart_data(chat_id)
        elif chart_type == "activity":
            return await self._get_activity_chart_data(chat_id)
        elif chart_type == "message-types":
            return await self._get_message_types_chart_data(chat_id)
        else:
            raise ValueError(f"Unknown chart type: {chart_type}")
    
    async def _get_timeline_chart_data(self, chat_id: UUID) -> Dict[str, Any]:
        """Format timeline data for Chart.js line chart"""
        
        timeline_data = await self.analyzer.get_timeline_data(chat_id, "daily")
        
        return {
            "type": "line",
            "labels": [item["period"] for item in timeline_data],
            "datasets": [{
                "label": "Messages per Day",
                "data": [item["message_count"] for item in timeline_data],
                "borderColor": "#25d366",
                "backgroundColor": "rgba(37, 211, 102, 0.1)",
                "tension": 0.4
            }]
        }
    
    async def _get_participants_chart_data(self, chat_id: UUID) -> Dict[str, Any]:
        """Format participant data for Chart.js doughnut chart"""
        
        participant_stats = await self.analyzer.get_participant_statistics(chat_id)
        
        # Limit to top 10 participants to avoid cluttered chart
        top_participants = participant_stats[:10]
        
        colors = [
            "#25d366", "#128c7e", "#dcf8c6", "#ece5dd", "#34b7f1",
            "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeaa7"
        ]
        
        return {
            "type": "doughnut",
            "labels": [p["name"] for p in top_participants],
            "datasets": [{
                "data": [p["message_count"] for p in top_participants],
                "backgroundColor": colors[:len(top_participants)],
                "borderWidth": 2,
                "borderColor": "#ffffff"
            }]
        }
    
    async def _get_activity_chart_data(self, chat_id: UUID) -> Dict[str, Any]:
        """Format activity heatmap data for Chart.js"""
        
        heatmap_data = await self.analyzer.get_activity_heatmap(chat_id)
        
        # Convert matrix to Chart.js scatter plot format for heatmap
        scatter_data = []
        max_value = 0
        
        for day_idx, day_data in enumerate(heatmap_data["matrix"]):
            for hour_idx, value in enumerate(day_data):
                if value > 0:
                    scatter_data.append({
                        "x": hour_idx,
                        "y": day_idx,
                        "v": value  # value for color intensity
                    })
                    max_value = max(max_value, value)
        
        return {
            "type": "scatter",
            "data": scatter_data,
            "labels": {
                "x_axis": heatmap_data["hour_labels"],
                "y_axis": heatmap_data["day_labels"]
            },
            "max_value": max_value
        }
    
    async def _get_message_types_chart_data(self, chat_id: UUID) -> Dict[str, Any]:
        """Format message types data for Chart.js bar chart"""
        
        basic_stats = await self.analyzer.get_basic_stats(chat_id)
        message_types = basic_stats["message_types"]
        
        # Map message types to readable labels
        type_labels = {
            "text": "Text Messages",
            "media": "Media",
            "system": "System Messages",
            "deleted": "Deleted Messages"
        }
        
        labels = []
        data = []
        colors = []
        color_map = {
            "text": "#25d366",
            "media": "#128c7e",
            "system": "#dcf8c6",
            "deleted": "#ece5dd"
        }
        
        for msg_type, count in message_types.items():
            labels.append(type_labels.get(msg_type, msg_type.title()))
            data.append(count)
            colors.append(color_map.get(msg_type, "#cccccc"))
        
        return {
            "type": "bar",
            "labels": labels,
            "datasets": [{
                "label": "Message Count",
                "data": data,
                "backgroundColor": colors,
                "borderColor": colors,
                "borderWidth": 1
            }]
        }
    
    async def export_messages_csv(self, chat_id: UUID) -> str:
        """Export messages as CSV"""
        
        # Get all messages with participant info
        from sqlmodel import select
        
        messages_query = select(
            Message.timestamp,
            Participant.name,
            Message.content,
            Message.message_type,
            Message.char_count,
            Message.word_count,
            Message.has_emoji,
            Message.has_link
        ).select_from(
            Message.__table__.join(Participant.__table__)
        ).where(
            Message.chat_id == chat_id
        ).order_by(Message.timestamp)
        
        result = await self.session.execute(messages_query)
        messages = result.all()
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Timestamp", "Participant", "Content", "Type", 
            "Character Count", "Word Count", "Has Emoji", "Has Link"
        ])
        
        # Write data
        for msg in messages:
            writer.writerow([
                msg.timestamp.isoformat(),
                msg.name,
                msg.content,
                msg.message_type,
                msg.char_count,
                msg.word_count,
                msg.has_emoji,
                msg.has_link
            ])
        
        return output.getvalue()
    
    async def export_participants_csv(self, chat_id: UUID) -> str:
        """Export participant statistics as CSV"""
        
        participant_stats = await self.analyzer.get_participant_statistics(chat_id)
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Name", "Message Count", "Average Message Length", 
            "Total Characters", "Total Words", "Emoji Count", 
            "Link Count", "First Message", "Last Message"
        ])
        
        # Write data
        for participant in participant_stats:
            writer.writerow([
                participant["name"],
                participant["message_count"],
                participant["avg_message_length"],
                participant["total_characters"],
                participant["total_words"],
                participant["emoji_count"],
                participant["link_count"],
                participant["first_message"],
                participant["last_message"]
            ])
        
        return output.getvalue()
    
    async def export_timeline_csv(self, chat_id: UUID) -> str:
        """Export timeline data as CSV"""
        
        timeline_data = await self.analyzer.get_timeline_data(chat_id, "daily")
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Date", "Message Count"])
        
        # Write data
        for item in timeline_data:
            writer.writerow([item["period"], item["message_count"]])
        
        return output.getvalue()
    
    async def format_summary_text(self, summary_data: Dict[str, Any]) -> str:
        """Format summary data as readable text"""
        
        text_parts = []
        
        # Header
        text_parts.append("WHATSAPP CHAT ANALYSIS SUMMARY")
        text_parts.append("=" * 40)
        text_parts.append("")
        
        # Basic info
        summary = summary_data["summary"]
        text_parts.append("OVERVIEW:")
        text_parts.append(f"• Total Messages: {summary['total_messages']:,}")
        text_parts.append(f"• Duration: {summary['duration_days']} days")
        text_parts.append(f"• Participants: {summary['participants']}")
        text_parts.append(f"• Most Active Participant: {summary['most_active_participant']}")
        text_parts.append(f"• Peak Activity Time: {summary['peak_activity_time']}")
        text_parts.append(f"• Peak Activity Day: {summary['peak_activity_day']}")
        text_parts.append("")
        
        # Highlights
        highlights = summary_data["highlights"]
        text_parts.append("HIGHLIGHTS:")
        text_parts.append(f"• Busiest Day: {highlights['busiest_day']}")
        text_parts.append(f"• Most Talkative: {highlights['most_talkative']}")
        text_parts.append(f"• Emoji Enthusiast: {highlights['emoji_lover']}")
        text_parts.append(f"• Link Sharer: {highlights['link_sharer']}")
        text_parts.append("")
        
        # Top participants
        text_parts.append("TOP PARTICIPANTS:")
        for i, participant in enumerate(summary_data["participants"], 1):
            text_parts.append(f"{i}. {participant['name']}: {participant['message_count']:,} messages")
        text_parts.append("")
        
        # Top words
        text_parts.append("MOST USED WORDS:")
        for i, word_data in enumerate(summary_data["top_words"], 1):
            text_parts.append(f"{i}. {word_data['word']}: {word_data['count']} times")
        text_parts.append("")
        
        # Footer
        text_parts.append("-" * 40)
        text_parts.append("Generated by WhatsApp Chat Analyzer")
        text_parts.append("2025-06-25 16:24:48 UTC")
        
        return "\n".join(text_parts)

class ChartDataGenerator:
    """Generate data specifically formatted for frontend charts"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.analyzer = ChatAnalyzer(session)
    
    async def generate_timeline_chart(self, chat_id: UUID, granularity: str = "daily") -> Dict[str, Any]:
        """Generate timeline chart configuration"""
        
        timeline_data = await self.analyzer.get_timeline_data(chat_id, granularity)
        
        return {
            "type": "line",
            "data": {
                "labels": [item["period"] for item in timeline_data],
                "datasets": [{
                    "label": f"Messages per {granularity.title()}",
                    "data": [item["message_count"] for item in timeline_data],
                    "borderColor": "#25d366",
                    "backgroundColor": "rgba(37, 211, 102, 0.1)",
                    "fill": True,
                    "tension": 0.4
                }]
            },
            "options": {
                "responsive": True,
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "title": {
                            "display": True,
                            "text": "Number of Messages"
                        }
                    },
                    "x": {
                        "title": {
                            "display": True,
                            "text": "Date"
                        }
                    }
                }
            }
        }
    
    async def generate_activity_heatmap(self, chat_id: UUID) -> Dict[str, Any]:
        """Generate activity heatmap data for custom visualization"""
        
        heatmap_data = await self.analyzer.get_activity_heatmap(chat_id)
        
        return {
            "type": "heatmap",
            "data": heatmap_data["matrix"],
            "labels": {
                "days": heatmap_data["day_labels"],
                "hours": heatmap_data["hour_labels"]
            },
            "colorScale": {
                "min": 0,
                "max": max(max(row) for row in heatmap_data["matrix"]) if any(heatmap_data["matrix"]) else 1
            }
        }