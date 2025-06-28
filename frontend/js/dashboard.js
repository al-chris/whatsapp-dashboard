// Dashboard-specific functionality
class DashboardManager {
    constructor() {
        this.charts = {};
        this.currentChatId = null;
        this.currentAnalysisData = null;
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Timeline controls
        const timelineControls = document.getElementById('timelineControls');
        if (timelineControls) {
            timelineControls.addEventListener('change', (e) => {
                if (this.currentChatId) {
                    this.loadActivityOverTime(this.currentChatId, e.target.value);
                }
            });
        }
        
        // Content tabs
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('content-tab')) {
                this.switchTab(e.target);
            }
        });
    }
    
    switchTab(clickedTab) {
        const tabContainer = clickedTab.parentElement;
        const contentContainer = tabContainer.nextElementSibling.parentElement;
        
        // Remove active class from all tabs in this container
        tabContainer.querySelectorAll('.content-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Hide all tab contents in this container
        contentContainer.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        // Activate clicked tab
        clickedTab.classList.add('active');
        
        // Show corresponding content
        const targetTab = clickedTab.dataset.tab;
        const targetContent = document.getElementById(targetTab);
        if (targetContent) {
            targetContent.classList.add('active');
        }
    }
    
    async loadChatAnalysis(chatId) {
        this.currentChatId = chatId;
        
        try {
            // Show loading state
            this.showLoading();
            
            // Load comprehensive analysis
            const analysis = await window.api.getChatAnalysis(chatId);
            this.currentAnalysisData = analysis;
            
            console.log('Updating overview cards with:', analysis);
            
            // Update overview cards
            this.updateOverviewCards(analysis);
            
            // Load all visualizations
            await this.loadAllVisualizations(analysis);
            
            // Hide loading state
            this.hideLoading();
            
        } catch (error) {
            console.error('Error loading chat analysis:', error);
            this.hideLoading();
            this.showError('Failed to load chat analysis');
        }
    }
    
    updateOverviewCards(analysis) {
        // Show dashboard content first so elements are available
        const dashboardContent = document.getElementById('dashboardContent');
        if (dashboardContent) {
            dashboardContent.style.display = 'block';
        }
        
        console.log('Updating overview cards with:', analysis);
        
        // Safely get basic stats
        const stats = analysis?.analysis?.basic_stats || {};
        const chatInfo = analysis?.chat_info || {};
        
        // Update total messages
        const totalMessagesEl = document.getElementById('totalMessages');
        if (totalMessagesEl) {
            totalMessagesEl.textContent = (stats.total_messages || chatInfo.message_count || 0).toLocaleString();
        }
        
        // Update participant count
        const totalParticipantsEl = document.getElementById('totalParticipants');
        if (totalParticipantsEl) {
            totalParticipantsEl.textContent = (stats.participant_count || chatInfo.participant_count || 0).toString();
        }
        
        // Update date range
        const dateRangeEl = document.getElementById('dateRange');
        if (dateRangeEl) {
            if (chatInfo.date_range?.start && chatInfo.date_range?.end) {
                const start = new Date(chatInfo.date_range.start).toLocaleDateString();
                const end = new Date(chatInfo.date_range.end).toLocaleDateString();
                dateRangeEl.textContent = `${start} - ${end}`;
            } else {
                dateRangeEl.textContent = '-';
            }
        }
        
        // Update average messages per day
        const avgMessagesPerDayEl = document.getElementById('avgMessagesPerDay');
        if (avgMessagesPerDayEl) {
            avgMessagesPerDayEl.textContent = Math.round(stats.avg_messages_per_day || 0).toLocaleString();
        }
    }
    
    async loadAllVisualizations(analysis) {
        const data = analysis.analysis;
        
        try {
            // Wait for chartManager to be available
            if (!window.chartManager) {
                console.warn('ChartManager not available, waiting...');
                await new Promise(resolve => {
                    const checkChartManager = () => {
                        if (window.chartManager) {
                            resolve();
                        } else {
                            setTimeout(checkChartManager, 100);
                        }
                    };
                    checkChartManager();
                });
            }
            
            // Activity Over Time
            if (data.activity_over_time) {
                this.createTimelineChart(data.activity_over_time);
            }
            
            // Hourly Heatmap
            if (data.hourly_heatmap) {
                this.createHourlyHeatmap(data.hourly_heatmap);
            }
            
            // Participant Statistics
            if (data.participants) {
                this.createParticipantChart(data.participants);
            }
            
            // Message Types (if available in basic_stats)
            if (data.basic_stats?.message_types) {
                this.createMessageTypesChart(data.basic_stats.message_types);
            }
            
            // User Statistics
            if (data.user_statistics) {
                this.createUserStatisticsCharts(data.user_statistics);
            }
            
            // Content Analysis
            if (data.extended_content || data.content) {
                this.createContentAnalysisCharts(data.extended_content || data.content);
            }
            
            // Interaction Metrics
            if (data.interaction_metrics) {
                this.createInteractionMetricsCharts(data.interaction_metrics);
            }
            
            // User Word Clouds
            if (data.user_word_clouds) {
                this.createUserWordClouds(data.user_word_clouds);
            }
            
            // Longest Pauses
            if (data.interaction_metrics?.longest_pauses) {
                this.createLongestPausesList(data.interaction_metrics.longest_pauses);
            }
        } catch (error) {
            console.error('Error loading visualizations:', error);
        }
    }
    
    createTimelineChart(data) {
        if (!data || !data.data || !window.chartManager) return;
        
        try {
            const chartData = {
                labels: data.data.map(d => d.period),
                datasets: [{
                    data: data.data.map(d => d.count)
                }]
            };
            
            if (typeof window.chartManager.createTimelineChart === 'function') {
                window.chartManager.createTimelineChart('messagesTimeChart', chartData);
            } else {
                console.warn('createTimelineChart method not found in chartManager');
            }
        } catch (error) {
            console.error('Error creating timeline chart:', error);
        }
    }
    
    createHourlyHeatmap(data) {
        if (!data || !window.chartManager) return;
        
        if (typeof window.chartManager.createAdvancedHeatmap === 'function') {
            window.chartManager.createAdvancedHeatmap('activityHeatmap', data);
        } else {
            console.warn('createAdvancedHeatmap method not found in chartManager');
        }
    }
    
    createParticipantChart(data) {
        if (!data || !Array.isArray(data) || !window.chartManager) return;
        
        const chartData = {
            labels: data.map(p => p.name),
            datasets: [{
                data: data.map(p => p.message_count),
                backgroundColor: window.chartManager.chartColors
            }]
        };
        
        if (typeof window.chartManager.createParticipantsChart === 'function') {
            window.chartManager.createParticipantsChart('participantChart', chartData);
        } else {
            console.warn('createParticipantsChart method not found in chartManager');
        }
    }
    
    createMessageTypesChart(data) {
        if (!data || !window.chartManager) return;
        
        const chartData = {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: window.chartManager.chartColors
            }]
        };
        
        if (typeof window.chartManager.createMessageTypesChart === 'function') {
            window.chartManager.createMessageTypesChart('messageTypesChart', chartData);
        } else {
            console.warn('createMessageTypesChart method not found in chartManager');
        }
    }
    
    createUserStatisticsCharts(data) {
        if (!data || !window.chartManager) return;
        
        // Average message length chart
        if (typeof window.chartManager.createUserMessageLengthChart === 'function') {
            window.chartManager.createUserMessageLengthChart('userMessageLengthChart', data.avg_message_length);
        } else {
            console.warn('createUserMessageLengthChart method not found in chartManager');
        }
        
        // Emoji usage chart
        if (typeof window.chartManager.createUserEmojiUsageChart === 'function') {
            window.chartManager.createUserEmojiUsageChart('userEmojiUsageChart', data.emoji_usage);
        } else {
            console.warn('createUserEmojiUsageChart method not found in chartManager');
        }
    }
    
    createContentAnalysisCharts(data) {
        if (!data || !window.chartManager) return;
        
        // Word cloud
        if (data.word_cloud) {
            if (typeof window.chartManager.createWordCloudChart === 'function') {
                window.chartManager.createWordCloudChart('wordCloudChart', data.word_cloud);
            } else {
                console.warn('createWordCloudChart method not found in chartManager');
            }
        }
        
        // Emoji analysis
        if (data.emoji_analysis) {
            if (typeof window.chartManager.createEmojiChart === 'function') {
                window.chartManager.createEmojiChart('emojiChart', data.emoji_analysis);
            } else {
                console.warn('createEmojiChart method not found in chartManager');
            }
        }
        
        // Shared domains
        if (data.shared_domains) {
            if (typeof window.chartManager.createSharedDomainsChart === 'function') {
                window.chartManager.createSharedDomainsChart('sharedDomainsChart', data.shared_domains);
            } else {
                console.warn('createSharedDomainsChart method not found in chartManager');
            }
        }
    }
    
    createInteractionMetricsCharts(data) {
        if (!data || !window.chartManager) return;
        
        // Response times
        if (data.response_times) {
            if (typeof window.chartManager.createResponseTimeChart === 'function') {
                window.chartManager.createResponseTimeChart('responseTimeChart', data.response_times);
            } else {
                console.warn('createResponseTimeChart method not found in chartManager');
            }
        }
        
        // Conversation starters
        if (data.conversation_starters) {
            if (typeof window.chartManager.createConversationStartersChart === 'function') {
                window.chartManager.createConversationStartersChart('conversationStartersChart', data.conversation_starters);
            } else {
                console.warn('createConversationStartersChart method not found in chartManager');
            }
        }
    }
    
    createUserWordClouds(data) {
        if (!data) return;
        
        const container = document.getElementById('userWordCloudGrid');
        if (!container) {
            console.warn('userWordCloudGrid element not found');
            return;
        }
        
        container.innerHTML = '';
        
        Object.entries(data).forEach(([userName, words]) => {
            if (!words || !Array.isArray(words)) {
                console.warn(`Invalid word data for user ${userName}:`, words);
                return;
            }
            
            const userCard = document.createElement('div');
            userCard.className = 'user-stat-card';
            userCard.style.cssText = `
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                margin: 10px;
                text-align: center;
            `;
            
            const title = document.createElement('h4');
            title.textContent = userName;
            title.style.cssText = `
                margin: 0 0 10px 0;
                color: #495057;
                font-size: 16px;
            `;
            userCard.appendChild(title);
            
            const wordContainer = document.createElement('div');
            wordContainer.className = 'word-cloud-container';
            wordContainer.style.cssText = `
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
                justify-content: center;
                align-items: center;
            `;
            
            words.slice(0, 15).forEach(wordData => {
                const wordElement = document.createElement('span');
                wordElement.className = 'word-item';
                
                // Handle different data structures
                let word, count;
                if (typeof wordData === 'object' && wordData.word) {
                    word = wordData.word;
                    count = wordData.count || wordData.frequency || 1;
                } else if (Array.isArray(wordData) && wordData.length >= 2) {
                    word = wordData[0];
                    count = wordData[1];
                } else if (typeof wordData === 'string') {
                    word = wordData;
                    count = 1;
                } else {
                    console.warn('Unknown word data format:', wordData);
                    return;
                }
                
                wordElement.textContent = `${word} (${count})`;
                wordElement.style.cssText = `
                    background: #e9ecef;
                    padding: 3px 6px;
                    border-radius: 12px;
                    font-size: ${Math.max(10, Math.min(14, 8 + count / 5))}px;
                    color: #495057;
                    border: 1px solid #ced4da;
                `;
                wordContainer.appendChild(wordElement);
            });
            
            userCard.appendChild(wordContainer);
            container.appendChild(userCard);
        });
    }
    
    createLongestPausesList(pauses) {
        if (!pauses) return;
        
        const container = document.getElementById('longestPauses');
        if (!container) {
            console.warn('longestPauses element not found');
            return;
        }
        
        container.innerHTML = '';
        
        if (!Array.isArray(pauses) || pauses.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">No significant pauses detected</p>';
            return;
        }
        
        pauses.slice(0, 5).forEach(pause => {
            const pauseElement = document.createElement('div');
            pauseElement.className = 'pause-item';
            pauseElement.style.cssText = `
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
            `;
            
            pauseElement.innerHTML = `
                <div class="pause-duration" style="font-size: 18px; font-weight: bold; color: #495057; margin-bottom: 8px;">
                    ${pause.duration_hours} hours
                </div>
                <div class="pause-details" style="color: #6c757d; font-size: 14px;">
                    From: ${new Date(pause.before).toLocaleString()}<br>
                    To: ${new Date(pause.after).toLocaleString()}<br>
                    Conversation restarted by: <span class="pause-restarter" style="font-weight: bold; color: #007bff;">${pause.restarted_by}</span>
                </div>
            `;
            
            container.appendChild(pauseElement);
        });
    }
    
    async loadActivityOverTime(chatId, period) {
        try {
            const data = await window.api.getActivityOverTime(chatId, period);
            this.createTimelineChart(data);
        } catch (error) {
            console.error('Error loading activity over time:', error);
        }
    }
    
    showLoading() {
        // Remove any existing loading overlay
        this.hideLoading();
        
        // Create loading overlay
        const overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            color: white;
            font-size: 18px;
        `;
        
        overlay.innerHTML = `
            <div style="text-align: center;">
                <div class="spinner" style="border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto 20px;"></div>
                <p>Loading analysis...</p>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Add spinner animation if not already present
        if (!document.getElementById('spinnerStyle')) {
            const style = document.createElement('style');
            style.id = 'spinnerStyle';
            style.textContent = `
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.remove();
        }
    }
    
    showError(message) {
        // Hide loading first
        this.hideLoading();
        
        // Show dashboard content so we can display error in it
        const dashboardContent = document.getElementById('dashboardContent');
        if (dashboardContent) {
            dashboardContent.style.display = 'block';
            
            // Add error message at the top
            const existingError = dashboardContent.querySelector('.error-message');
            if (existingError) {
                existingError.remove();
            }
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.style.cssText = `
                background: #f8d7da;
                color: #721c24;
                padding: 15px;
                margin-bottom: 20px;
                border: 1px solid #f5c6cb;
                border-radius: 4px;
                text-align: center;
            `;
            errorDiv.innerHTML = `❌ ${message}`;
            
            dashboardContent.insertBefore(errorDiv, dashboardContent.firstChild);
        }
    }
}

// Initialize dashboard manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardManager = new DashboardManager();
});