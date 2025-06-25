from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models.chat import Chat
from services.analyzer import ChatAnalyzer
from services.visualizer import DataExporter
from uuid import UUID
import json
import csv
import io
from typing import Dict, Any

router = APIRouter()

@router.get("/export/{chat_id}/json")
async def export_json(
    chat_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> Response:
    """Export chat analysis as JSON"""
    
    # Verify chat exists
    chat = await session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    analyzer = ChatAnalyzer(session)
    
    # Get comprehensive analysis
    analysis_data = await analyzer.get_comprehensive_analysis(chat_id)
    
    # Prepare export data
    export_data = {
        "chat_info": {
            "id": str(chat.id),
            "title": chat.title,
            "file_name": chat.file_name,
            "participant_count": chat.participant_count,
            "message_count": chat.message_count,
            "upload_date": chat.upload_date.isoformat(),
            "date_range": {
                "start": chat.date_range_start.isoformat() if chat.date_range_start else None,
                "end": chat.date_range_end.isoformat() if chat.date_range_end else None
            }
        },
        "analysis": analysis_data,
        "export_info": {
            "exported_at": "2025-06-25T16:24:48Z",
            "format": "json",
            "version": "1.0"
        }
    }
    
    # Convert to JSON
    json_content = json.dumps(export_data, indent=2, ensure_ascii=False)
    
    # Create response
    response = Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=chat_analysis_{chat_id}.json"
        }
    )
    
    return response

@router.get("/export/{chat_id}/csv")
async def export_csv(
    chat_id: UUID,
    data_type: str = "messages",  # messages, participants, timeline
    session: AsyncSession = Depends(get_session)
) -> Response:
    """Export specific chat data as CSV"""
    
    # Verify chat exists
    chat = await session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    if data_type not in ["messages", "participants", "timeline"]:
        raise HTTPException(
            status_code=400,
            detail="data_type must be 'messages', 'participants', or 'timeline'"
        )
    
    exporter = DataExporter(session)
    
    # Get CSV content based on data type
    if data_type == "messages":
        csv_content = await exporter.export_messages_csv(chat_id)
        filename = f"messages_{chat_id}.csv"
    elif data_type == "participants":
        csv_content = await exporter.export_participants_csv(chat_id)
        filename = f"participants_{chat_id}.csv"
    else:  # timeline
        csv_content = await exporter.export_timeline_csv(chat_id)
        filename = f"timeline_{chat_id}.csv"
    
    # Create response
    response = Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
    
    return response

@router.get("/export/{chat_id}/summary")
async def export_summary(
    chat_id: UUID,
    format: str = "json",  # json, txt
    session: AsyncSession = Depends(get_session)
) -> Response:
    """Export chat summary report"""
    
    # Verify chat exists
    chat = await session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    if format not in ["json", "txt"]:
        raise HTTPException(
            status_code=400,
            detail="Format must be 'json' or 'txt'"
        )
    
    analyzer = ChatAnalyzer(session)
    exporter = DataExporter(session)
    
    # Get summary data
    summary_data = await analyzer.get_summary_report(chat_id)
    
    if format == "json":
        content = json.dumps(summary_data, indent=2, ensure_ascii=False)
        media_type = "application/json"
        filename = f"summary_{chat_id}.json"
    else:  # txt
        content = await exporter.format_summary_text(summary_data)
        media_type = "text/plain"
        filename = f"summary_{chat_id}.txt"
    
    # Create response
    response = Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
    
    return response

@router.get("/export/{chat_id}/chart-data")
async def export_chart_data(
    chat_id: UUID,
    chart_type: str,  # timeline, participants, activity, message-types
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Export chart data in format ready for visualization"""
    
    # Verify chat exists
    chat = await session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    valid_chart_types = ["timeline", "participants", "activity", "message-types"]
    if chart_type not in valid_chart_types:
        raise HTTPException(
            status_code=400,
            detail=f"chart_type must be one of: {', '.join(valid_chart_types)}"
        )
    
    visualizer = DataExporter(session)
    
    # Get chart data based on type
    chart_data = await visualizer.get_chart_data(chat_id, chart_type)
    
    return {
        "chat_id": str(chat_id),
        "chart_type": chart_type,
        "data": chart_data
    }