# WhatsApp Chat Analysis Dashboard

![LOGO](logo.png)

A comprehensive web application for analyzing and visualizing WhatsApp chat exports built with FastAPI and vanilla JavaScript.

## Features

### 📊 **Comprehensive Analysis**
- Message statistics and timeline visualization
- Participant activity analysis
- Content analysis (word frequency, emoji usage)
- Activity heatmaps (hour vs day of week)
- Conversation insights and patterns

### 🎨 **Interactive Dashboard**
- Real-time charts and visualizations
- Responsive design for all devices
- Drag & drop file upload
- Multiple export formats (JSON, CSV, TXT)

### 🔒 **Privacy-First**
- Local processing (no data sent to external servers)
- Option to delete uploaded data
- Secure file handling

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLModel** - SQL databases with async support
- **SQLite/PostgreSQL** - Database storage
- **Pydantic** - Data validation

### Frontend
- **Vanilla JavaScript** - No frameworks, pure JS
- **Chart.js** - Interactive charts and graphs
- **Modern CSS** - Grid, Flexbox, animations
- **Responsive Design** - Mobile-first approach

## Quick Start

### Prerequisites
- Python 3.8+
- Modern web browser

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/al-chris/whatsapp-dashboard.git
cd whatsapp-dashboard
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python main.py
```

4. **Open your browser**
```
http://localhost:80
```

## How to Use

### 1. Export WhatsApp Chat
1. Open WhatsApp on your phone
2. Go to the chat you want to analyze
3. Tap on the chat name → **Export Chat**
4. Choose **"Without Media"** for faster processing
5. Save the exported `.txt` file

### 2. Upload and Analyze
1. Visit the dashboard in your browser
2. Drag & drop or click to upload your chat file
3. Wait for processing to complete
4. Explore your chat analysis!

### 3. View Insights
- **Overview**: Basic statistics and metrics
- **Timeline**: Message activity over time
- **Participants**: Who talks the most?
- **Activity Patterns**: When are you most active?
- **Content Analysis**: Most used words and emojis

## API Endpoints

### Upload
- `POST /api/upload` - Upload chat file
- `GET /api/uploads` - List all uploads

### Analysis
- `GET /api/analysis/{chat_id}` - Comprehensive analysis
- `GET /api/stats/{chat_id}` - Basic statistics
- `GET /api/insights/{chat_id}` - Conversation insights
- `GET /api/timeline/{chat_id}` - Timeline data
- `GET /api/wordcloud/{chat_id}` - Word frequency
- `GET /api/activity-heatmap/{chat_id}` - Activity heatmap

### Export
- `GET /api/export/{chat_id}/json` - Export as JSON
- `GET /api/export/{chat_id}/csv` - Export as CSV
- `GET /api/export/{chat_id}/summary` - Summary report

### Management
- `DELETE /api/chat/{chat_id}` - Delete chat data

## Project Structure

```
whatsapp-dashboard/
├── main.py                 # FastAPI application
├── database.py            # Database configuration
├── requirements.txt       # Python dependencies
├── models/               # Data models
│   ├── chat.py
│   ├── message.py
│   └── participant.py
├── api/                  # API endpoints
│   ├── upload.py
│   ├── analysis.py
│   └── export.py
├── services/             # Business logic
│   ├── parser.py         # WhatsApp chat parser
│   ├── analyzer.py       # Analysis engine
│   └── visualizer.py     # Data export utilities
└── frontend/             # Frontend application
    ├── index.html
    ├── styles/
    │   ├── main.css
    │   └── components.css
    └── js/
        ├── app.js        # Main application
        ├── api.js        # API communication
        ├── fileUpload.js # File upload handling
        ├── dashboard.js  # Dashboard management
        └── charts.js     # Chart creation
```

## Configuration

### Database
By default, the application uses SQLite. To use PostgreSQL:

```python
# In database.py
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/whatsapp_dashboard"
```

### CORS
For production, update CORS settings in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

## Development

### Running in Development Mode
```bash
# With auto-reload
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 80
```

### Testing
```bash
# Run tests (when implemented)
pytest

# Manual API testing
curl -X GET "http://localhost:80/health"
```

## Deployment

### Docker (Optional)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
```bash
# Optional environment variables
export DATABASE_URL="sqlite+aiosqlite:///./whatsapp_dashboard.db"
export DEBUG=False
export MAX_FILE_SIZE=52428800  # 50MB
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Privacy Notice

This application processes WhatsApp chat data locally. No data is sent to external servers unless explicitly configured. Users can delete their data at any time through the dashboard.

## Support

- 📖 [Documentation](https://github.com/al-chris/whatsapp-dashboard/wiki)
- 🐛 [Report Issues](https://github.com/al-chris/whatsapp-dashboard/issues)
- 💬 [Discussions](https://github.com/al-chris/whatsapp-dashboard/discussions)

---

**Created by [@al-chris](https://github.com/al-chris)**  
*Last updated: 2025-06-25*
