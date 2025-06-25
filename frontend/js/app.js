// Main application controller
class WhatsAppDashboardApp {
    constructor() {
        this.currentSection = 'upload';
        this.currentChatId = null;
        this.charts = {};
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadUploads();
        this.showSection('upload');
    }
    
    setupEventListeners() {
        // Navigation
        document.getElementById('homeBtn').addEventListener('click', () => this.showSection('upload'));
        document.getElementById('dashboardBtn').addEventListener('click', () => this.showSection('dashboard'));
        document.getElementById('uploadsBtn').addEventListener('click', () => this.showSection('uploads'));
        
        // Chat selector
        const chatSelector = document.getElementById('chatSelector');
        if (chatSelector) {
            chatSelector.addEventListener('change', (e) => {
                if (e.target.value) {
                    this.loadDashboard(e.target.value);
                }
            });
        }
        
        // View dashboard button (from upload result)
        document.addEventListener('click', (e) => {
            if (e.target.id === 'viewDashboardBtn') {
                if (this.currentChatId) {
                    this.showSection('dashboard');
                    this.loadDashboard(this.currentChatId);
                }
            }
        });
    }
    
    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Show target section
        const targetSection = document.getElementById(`${sectionName}Section`);
        if (targetSection) {
            targetSection.classList.add('active');
        }
        
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        const activeBtn = document.getElementById(`${sectionName}Btn`) || 
                         document.getElementById('homeBtn');
        activeBtn.classList.add('active');
        
        this.currentSection = sectionName;
        
        // Load section-specific data
        if (sectionName === 'uploads') {
            this.loadUploads();
        }
    }
    
    async loadUploads() {
        const uploadsList = document.getElementById('uploadsList');
        const chatSelector = document.getElementById('chatSelector');
        
        try {
            // Show loading
            uploadsList.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading uploads...</p></div>';
            
            const uploads = await window.api.getUploads();
            
            // Update uploads list
            if (uploads.length === 0) {
                uploadsList.innerHTML = `
                    <div class="card" style="text-align: center; padding: 3rem;">
                        <h3>No uploads yet</h3>
                        <p>Upload your first WhatsApp chat to get started!</p>
                        <button class="btn-primary" onclick="app.showSection('upload')">Upload Chat</button>
                    </div>
                `;
            } else {
                uploadsList.innerHTML = uploads.map(upload => `
                    <div class="upload-item">
                        <div class="upload-info">
                            <h4>${this.escapeHtml(upload.title)}</h4>
                            <div class="upload-meta">
                                <span>📅 ${new Date(upload.upload_date).toLocaleDateString()}</span>
                                <span>👥 ${upload.participants} participants</span>
                                <span>💬 ${upload.messages.toLocaleString()} messages</span>
                            </div>
                        </div>
                        <div class="upload-actions">
                            <button class="btn-secondary" onclick="app.viewAnalysis('${upload.id}')">
                                View Analysis
                            </button>
                            <button class="btn-secondary" onclick="app.exportData('${upload.id}')">
                                Export
                            </button>
                            <button class="btn-secondary" onclick="app.deleteChat('${upload.id}')" 
                                    style="color: #dc3545;">
                                Delete
                            </button>
                        </div>
                    </div>
                `).join('');
            }
            
            // Update chat selector
            if (chatSelector) {
                chatSelector.innerHTML = '<option value="">Select a chat to analyze</option>' +
                    uploads.map(upload => 
                        `<option value="${upload.id}">${this.escapeHtml(upload.title)}</option>`
                    ).join('');
            }
            
        } catch (error) {
            console.error('Error loading uploads:', error);
            uploadsList.innerHTML = `
                <div class="card" style="text-align: center; padding: 2rem; border: 2px solid #dc3545;">
                    <h3 style="color: #dc3545;">Error Loading Uploads</h3>
                    <p>${this.escapeHtml(error.message)}</p>
                    <button class="btn-primary" onclick="app.loadUploads()">Retry</button>
                </div>
            `;
        }
    }
    
    async loadDashboard(chatId) {
        this.currentChatId = chatId;
        const dashboardContent = document.getElementById('dashboardContent');
        const chatSelector = document.getElementById('chatSelector');
        
        // Set selected chat
        if (chatSelector) {
            chatSelector.value = chatId;
        }
        
        try {
            // Show loading
            dashboardContent.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading analysis...</p></div>';
            dashboardContent.style.display = 'block';
            
            // Load analysis data
            const analysis = await window.api.getAnalysis(chatId);
            
            // Update overview cards
            this.updateOverviewCards(analysis);
            
            // Restore dashboard content
            dashboardContent.innerHTML = `
                <!-- Overview Cards -->
                <div class="overview-cards">
                    <div class="card">
                        <h3>Total Messages</h3>
                        <div class="metric" id="totalMessages">0</div>
                    </div>
                    <div class="card">
                        <h3>Participants</h3>
                        <div class="metric" id="totalParticipants">0</div>
                    </div>
                    <div class="card">
                        <h3>Date Range</h3>
                        <div class="metric" id="dateRange">-</div>
                    </div>
                    <div class="card">
                        <h3>Avg Messages/Day</h3>
                        <div class="metric" id="avgMessagesPerDay">0</div>
                    </div>
                </div>

                <!-- Charts -->
                <div class="charts-grid">
                    <div class="chart-card">
                        <h3>Messages Over Time</h3>
                        <canvas id="messagesTimeChart"></canvas>
                    </div>
                    <div class="chart-card">
                        <h3>Messages by Participant</h3>
                        <canvas id="participantChart"></canvas>
                    </div>
                    <div class="chart-card">
                        <h3>Activity Heatmap</h3>
                        <div id="activityHeatmap" style="height: 300px;"></div>
                    </div>
                    <div class="chart-card">
                        <h3>Message Types</h3>
                        <canvas id="messageTypesChart"></canvas>
                    </div>
                </div>
            `;
            
            // Update overview cards again
            this.updateOverviewCards(analysis);
            
            // Load charts
            await this.loadCharts(chatId);
            
        } catch (error) {
            console.error('Error loading dashboard:', error);
            dashboardContent.innerHTML = `
                <div class="card" style="text-align: center; padding: 2rem; border: 2px solid #dc3545;">
                    <h3 style="color: #dc3545;">Error Loading Analysis</h3>
                    <p>${this.escapeHtml(error.message)}</p>
                    <button class="btn-primary" onclick="app.loadDashboard('${chatId}')">Retry</button>
                </div>
            `;
        }
    }
    
    updateOverviewCards(analysis) {
        const { chat_info, analysis: data } = analysis;
        
        // Update metrics
        document.getElementById('totalMessages').textContent = 
            chat_info.message_count.toLocaleString();
        document.getElementById('totalParticipants').textContent = 
            chat_info.participant_count;
        
        // Date range
        const startDate = chat_info.date_range.start ? 
            new Date(chat_info.date_range.start).toLocaleDateString() : 'Unknown';
        const endDate = chat_info.date_range.end ? 
            new Date(chat_info.date_range.end).toLocaleDateString() : 'Unknown';
        document.getElementById('dateRange').textContent = `${startDate} - ${endDate}`;
        
        // Average messages per day
        document.getElementById('avgMessagesPerDay').textContent = 
            data.basic_stats.avg_messages_per_day;
    }
    
    async loadCharts(chatId) {
        try {
            // Destroy existing charts
            Object.values(this.charts).forEach(chart => {
                if (chart && typeof chart.destroy === 'function') {
                    chart.destroy();
                }
            });
            this.charts = {};
            
            // Load chart data
            const [timelineData, participantData, activityData, messageTypesData] = await Promise.all([
                window.api.request(`/export/${chatId}/chart-data?chart_type=timeline`),
                window.api.request(`/export/${chatId}/chart-data?chart_type=participants`),
                window.api.request(`/activity-heatmap/${chatId}`),
                window.api.request(`/export/${chatId}/chart-data?chart_type=message-types`)
            ]);
            
            // Create charts
            this.charts.timeline = window.chartManager.createTimelineChart('messagesTimeChart', timelineData.data);
            this.charts.participants = window.chartManager.createParticipantsChart('participantChart', participantData.data);
            this.charts.messageTypes = window.chartManager.createMessageTypesChart('messageTypesChart', messageTypesData.data);
            
            // Create activity heatmap
            window.chartManager.createActivityHeatmap('activityHeatmap', activityData.heatmap);
            
        } catch (error) {
            console.error('Error loading charts:', error);
        }
    }
    
    viewAnalysis(chatId) {
        this.showSection('dashboard');
        this.loadDashboard(chatId);
    }
    
    async exportData(chatId) {
        try {
            // Create export modal or use simple download
            const format = prompt('Export format (json/csv/summary):', 'json');
            if (!format) return;
            
            let url;
            if (format === 'csv') {
                const dataType = prompt('CSV data type (messages/participants/timeline):', 'messages');
                url = `/api/export/${chatId}/csv?data_type=${dataType}`;
            } else {
                url = `/api/export/${chatId}/${format}`;
            }
            
            // Trigger download
            const link = document.createElement('a');
            link.href = url;
            link.download = `chat_${chatId}_${format}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
        } catch (error) {
            console.error('Error exporting data:', error);
            alert('Export failed: ' + error.message);
        }
    }
    
    async deleteChat(chatId) {
        if (!confirm('Are you sure you want to delete this chat? This action cannot be undone.')) {
            return;
        }
        
        try {
            await window.api.deleteChat(chatId);
            alert('Chat deleted successfully!');
            
            // Refresh uploads list
            await this.loadUploads();
            
            // If we're viewing this chat, go back to uploads
            if (this.currentChatId === chatId) {
                this.showSection('uploads');
                this.currentChatId = null;
            }
            
        } catch (error) {
            console.error('Error deleting chat:', error);
            alert('Delete failed: ' + error.message);
        }
    }
    
    setCurrentChatId(chatId) {
        this.currentChatId = chatId;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new WhatsAppDashboardApp();
});