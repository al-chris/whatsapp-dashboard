// Dashboard-specific functionality
class DashboardManager {
    constructor() {
        this.charts = {};
        this.currentChatId = null;
    }
    
    // Dashboard-specific methods can be added here
    // For now, this file is prepared for future dashboard functionality
}

// Initialize dashboard manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardManager = new DashboardManager();
});