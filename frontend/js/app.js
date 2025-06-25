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
                if (e.target.value && window.dashboardManager) {
                    window.dashboardManager.loadChatAnalysis(e.target.value);
                }
            });
        }
        
        // View dashboard button (from upload result)
        document.addEventListener('click', (e) => {
            if (e.target.id === 'viewDashboardBtn') {
                if (this.currentChatId) {
                    this.showSection('dashboard');
                    if (window.dashboardManager) {
                        window.dashboardManager.loadChatAnalysis(this.currentChatId);
                    }
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
    
    viewAnalysis(chatId) {
        this.showSection('dashboard');
        if (window.dashboardManager) {
            window.dashboardManager.loadChatAnalysis(chatId);
        }
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