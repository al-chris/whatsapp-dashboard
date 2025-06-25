// File upload handling
class FileUploadManager {
    constructor() {
        this.uploadZone = document.getElementById('uploadZone');
        this.fileInput = document.getElementById('fileInput');
        this.uploadProgress = document.getElementById('uploadProgress');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.uploadResult = document.getElementById('uploadResult');
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Click to browse
        this.uploadZone.addEventListener('click', () => {
            this.fileInput.click();
        });
        
        // File input change
        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFile(e.target.files[0]);
            }
        });
        
        // Drag and drop
        this.uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadZone.classList.add('dragover');
        });
        
        this.uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            this.uploadZone.classList.remove('dragover');
        });
        
        this.uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.uploadZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFile(files[0]);
            }
        });
    }
    
    async handleFile(file) {
        // Validate file
        if (!this.validateFile(file)) {
            return;
        }
        
        // Reset UI
        this.hideResult();
        this.showProgress();
        
        try {
            // Upload file with progress tracking
            const result = await window.api.uploadFile(file, (progress) => {
                this.updateProgress(progress, 'Uploading...');
            });
            
            // Process completion
            this.updateProgress(100, 'Processing complete!');
            
            // Show result after short delay
            setTimeout(() => {
                this.showResult(result);
                window.app.setCurrentChatId(result.chat_id);
            }, 1000);
            
        } catch (error) {
            console.error('Upload error:', error);
            this.showError(error.message);
        }
    }
    
    validateFile(file) {
        // Check file type
        const validTypes = ['.txt', '.zip'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!validTypes.includes(fileExtension)) {
            alert('Please select a valid WhatsApp chat file (.txt or .zip)');
            return false;
        }
        
        // Check file size (50MB limit)
        const maxSize = 50 * 1024 * 1024; // 50MB
        if (file.size > maxSize) {
            alert('File size too large. Please select a file smaller than 50MB.');
            return false;
        }
        
        return true;
    }
    
    showProgress() {
        this.uploadProgress.style.display = 'block';
        this.progressFill.style.width = '0%';
        this.progressText.textContent = 'Preparing upload...';
    }
    
    updateProgress(percentage, text) {
        this.progressFill.style.width = percentage + '%';
        this.progressText.textContent = text || `Uploading... ${Math.round(percentage)}%`;
    }
    
    hideProgress() {
        this.uploadProgress.style.display = 'none';
    }
    
    showResult(result) {
        this.hideProgress();
        
        // Update stats
        const statsHtml = `
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-number">${result.stats.participants}</div>
                    <div class="stat-label">Participants</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">${result.stats.messages.toLocaleString()}</div>
                    <div class="stat-label">Messages</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">${this.formatFileSize(result.stats.file_size)}</div>
                    <div class="stat-label">File Size</div>
                </div>
            </div>
        `;
        
        document.getElementById('uploadStats').innerHTML = statsHtml;
        this.uploadResult.style.display = 'block';
        
        // Refresh uploads list
        if (window.app) {
            window.app.loadUploads();
        }
    }
    
    showError(message) {
        this.hideProgress();
        
        const errorHtml = `
            <div class="card" style="border: 2px solid #dc3545; text-align: center;">
                <h3 style="color: #dc3545;">Upload Failed</h3>
                <p>${this.escapeHtml(message)}</p>
                <button class="btn-primary" onclick="fileUploadManager.hideResult()">Try Again</button>
            </div>
        `;
        
        this.uploadResult.innerHTML = errorHtml;
        this.uploadResult.style.display = 'block';
    }
    
    hideResult() {
        this.uploadResult.style.display = 'none';
        this.uploadResult.innerHTML = `
            <div class="result-card">
                <h3>Upload Successful!</h3>
                <div class="stats" id="uploadStats"></div>
                <button id="viewDashboardBtn" class="btn-primary">View Analysis</button>
            </div>
        `;
        
        // Reset file input
        this.fileInput.value = '';
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize file upload manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.fileUploadManager = new FileUploadManager();
});