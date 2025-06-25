// Chart management using Chart.js
class ChartManager {
    constructor() {
        this.charts = {};
        this.defaultColors = {
            primary: '#25d366',
            secondary: '#128c7e',
            accent: '#dcf8c6',
            neutral: '#ece5dd',
            info: '#34b7f1',
            success: '#28a745',
            warning: '#ffc107',
            danger: '#dc3545'
        };
        
        this.chartColors = [
            '#25d366', '#128c7e', '#dcf8c6', '#ece5dd', '#34b7f1',
            '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7',
            '#fd79a8', '#6c5ce7', '#a29bfe', '#74b9ff', '#0984e3'
        ];
    }
    
    createTimelineChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        // Destroy existing chart
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        const ctx = canvas.getContext('2d');
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Messages',
                    data: data.datasets?.[0]?.data || [],
                    borderColor: this.defaultColors.primary,
                    backgroundColor: this.hexToRgba(this.defaultColors.primary, 0.1),
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: this.defaultColors.primary,
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: this.defaultColors.primary,
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Date',
                            color: '#666'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        display: true,
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Messages',
                            color: '#666'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                }
            }
        });
        
        return this.charts[canvasId];
    }
    
    createParticipantsChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        // Destroy existing chart
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        const ctx = canvas.getContext('2d');
        
        // Assign colors to participants
        const colors = this.chartColors.slice(0, data.labels?.length || 0);
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels || [],
                datasets: [{
                    data: data.datasets?.[0]?.data || [],
                    backgroundColor: colors,
                    borderColor: '#ffffff',
                    borderWidth: 3,
                    hoverBorderWidth: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed.toLocaleString()} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
        
        return this.charts[canvasId];
    }
    
    createMessageTypesChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        // Destroy existing chart
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        const ctx = canvas.getContext('2d');
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Messages',
                    data: data.datasets?.[0]?.data || [],
                    backgroundColor: data.datasets?.[0]?.backgroundColor || this.chartColors,
                    borderColor: data.datasets?.[0]?.borderColor || this.chartColors,
                    borderWidth: 1,
                    borderRadius: 4,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white'
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Message Type',
                            color: '#666'
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        display: true,
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Count',
                            color: '#666'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                }
            }
        });
        
        return this.charts[canvasId];
    }
    
    createActivityHeatmap(containerId, heatmapData) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // Clear existing content
        container.innerHTML = '';
        
        // Create heatmap using a simple HTML/CSS approach
        const heatmapHtml = this.generateHeatmapHTML(heatmapData);
        container.innerHTML = heatmapHtml;
    }
    
    generateHeatmapHTML(heatmapData) {
        const { matrix, day_labels, hour_labels } = heatmapData;
        
        // Find max value for color scaling
        const maxValue = Math.max(...matrix.flat().filter(v => v > 0));
        
        if (maxValue === 0) {
            return '<div style="text-align: center; padding: 2rem; color: #666;">No activity data available</div>';
        }
        
        let html = '<div class="heatmap-container">';
        
        // Header with hour labels
        html += '<div class="heatmap-header">';
        html += '<div class="heatmap-corner"></div>';
        hour_labels.forEach((hour, index) => {
            if (index % 4 === 0) { // Show every 4th hour to avoid crowding
                html += `<div class="heatmap-hour-label">${hour}</div>`;
            } else {
                html += `<div class="heatmap-hour-label"></div>`;
            }
        });
        html += '</div>';
        
        // Rows with day labels and data
        matrix.forEach((row, dayIndex) => {
            html += '<div class="heatmap-row">';
            html += `<div class="heatmap-day-label">${day_labels[dayIndex]}</div>`;
            
            row.forEach((value, hourIndex) => {
                const intensity = value / maxValue;
                const opacity = Math.max(0.1, intensity);
                const backgroundColor = `rgba(37, 211, 102, ${opacity})`;
                
                html += `<div class="heatmap-cell" 
                    style="background-color: ${backgroundColor};" 
                    title="${day_labels[dayIndex]} ${hour_labels[hourIndex]}: ${value} messages">
                </div>`;
            });
            
            html += '</div>';
        });
        
        html += '</div>';
        
        // Add CSS if not already added
        this.addHeatmapCSS();
        
        return html;
    }
    
    addHeatmapCSS() {
        if (document.getElementById('heatmap-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'heatmap-styles';
        style.textContent = `
            .heatmap-container {
                display: flex;
                flex-direction: column;
                font-size: 12px;
                border: 1px solid #ddd;
                border-radius: 8px;
                overflow: hidden;
            }
            
            .heatmap-header {
                display: flex;
                background: #f8f9fa;
                border-bottom: 1px solid #ddd;
            }
            
            .heatmap-corner {
                width: 80px;
                flex-shrink: 0;
            }
            
            .heatmap-hour-label {
                flex: 1;
                text-align: center;
                padding: 4px 2px;
                font-size: 10px;
                color: #666;
                border-left: 1px solid #eee;
            }
            
            .heatmap-row {
                display: flex;
                border-bottom: 1px solid #eee;
            }
            
            .heatmap-row:last-child {
                border-bottom: none;
            }
            
            .heatmap-day-label {
                width: 80px;
                padding: 8px 4px;
                background: #f8f9fa;
                font-size: 11px;
                color: #333;
                display: flex;
                align-items: center;
                justify-content: center;
                border-right: 1px solid #ddd;
                flex-shrink: 0;
            }
            
            .heatmap-cell {
                flex: 1;
                height: 30px;
                border-left: 1px solid #fff;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .heatmap-cell:hover {
                border: 2px solid #25d366;
                z-index: 10;
                position: relative;
            }
        `;
        document.head.appendChild(style);
    }
    
    addHeatmapStyles() {
        // Check if styles already exist
        if (document.getElementById('heatmap-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'heatmap-styles';
        style.textContent = `
            .heatmap-container {
                width: 100%;
                overflow-x: auto;
                background: white;
                border-radius: 8px;
                padding: 1rem;
            }
            
            .heatmap-header {
                display: flex;
                margin-bottom: 2px;
            }
            
            .heatmap-corner {
                width: 80px;
                height: 25px;
                flex-shrink: 0;
            }
            
            .heatmap-hour {
                flex: 1;
                height: 25px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.75rem;
                color: #666;
                border-left: 1px solid #eee;
                min-width: 35px;
            }
            
            .heatmap-row {
                display: flex;
                margin-bottom: 2px;
            }
            
            .heatmap-day {
                width: 80px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: flex-end;
                padding-right: 8px;
                font-size: 0.8rem;
                color: #666;
                border-right: 1px solid #ddd;
                flex-shrink: 0;
            }
            
            .heatmap-cell {
                flex: 1;
                height: 30px;
                border-left: 1px solid #fff;
                cursor: pointer;
                transition: all 0.2s ease;
                min-width: 35px;
            }
            
            .heatmap-cell:hover {
                border: 2px solid #25d366;
                z-index: 10;
                position: relative;
                transform: scale(1.1);
            }
            
            .heatmap-legend {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                margin-top: 1rem;
                font-size: 0.8rem;
                color: #666;
            }
            
            .legend-gradient {
                width: 100px;
                height: 10px;
                background: linear-gradient(to right, rgb(240, 253, 244), rgb(37, 211, 102));
                border-radius: 5px;
            }
        `;
        document.head.appendChild(style);
    }
    
    destroyChart(canvasId) {
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
            delete this.charts[canvasId];
        }
    }
    
    destroyAllCharts() {
        Object.keys(this.charts).forEach(canvasId => {
            this.destroyChart(canvasId);
        });
    }
    
    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    
    // Utility method to update chart data
    updateChartData(canvasId, newData) {
        const chart = this.charts[canvasId];
        if (!chart) return;
        
        chart.data = newData;
        chart.update('active');
    }
    
    // Utility method to get chart as image
    getChartImage(canvasId, format = 'png') {
        const chart = this.charts[canvasId];
        if (!chart) return null;
        
        return chart.toBase64Image(format);
    }
    
    createWordCloudChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        // Create a simple word cloud using bar chart
        const words = data.slice(0, 15); // Top 15 words
        
        // Destroy existing chart
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: words.map(w => w.word),
                datasets: [{
                    label: 'Frequency',
                    data: words.map(w => w.count),
                    backgroundColor: this.chartColors.slice(0, words.length),
                    borderColor: this.chartColors.slice(0, words.length),
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y', // Horizontal bar chart
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white'
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: { display: true, text: 'Frequency' }
                    },
                    y: {
                        title: { display: true, text: 'Words' }
                    }
                }
            }
        });
        
        return this.charts[canvasId];
    }
    
    createEmojiChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        const emojis = data.slice(0, 10); // Top 10 emojis
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: emojis.map(e => `${e.emoji} (${e.count})`),
                datasets: [{
                    data: emojis.map(e => e.count),
                    backgroundColor: this.chartColors.slice(0, emojis.length),
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { font: { size: 14 } }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${percentage}%`;
                            }
                        }
                    }
                }
            }
        });
        
        return this.charts[canvasId];
    }
    
    createResponseTimeChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        // Convert seconds to minutes for better readability
        const processedData = data.map(user => ({
            ...user,
            avg_minutes: Math.round(user.avg_seconds / 60 * 10) / 10,
            median_minutes: Math.round(user.median_seconds / 60 * 10) / 10
        }));
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: processedData.map(u => u.name),
                datasets: [
                    {
                        label: 'Average Response Time (min)',
                        data: processedData.map(u => u.avg_minutes),
                        backgroundColor: this.hexToRgba(this.defaultColors.primary, 0.7),
                        borderColor: this.defaultColors.primary,
                        borderWidth: 1
                    },
                    {
                        label: 'Median Response Time (min)',
                        data: processedData.map(u => u.median_minutes),
                        backgroundColor: this.hexToRgba(this.defaultColors.secondary, 0.7),
                        borderColor: this.defaultColors.secondary,
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white'
                    }
                },
                scales: {
                    x: { title: { display: true, text: 'Users' } },
                    y: { 
                        beginAtZero: true,
                        title: { display: true, text: 'Response Time (minutes)' }
                    }
                }
            }
        });
        
        return this.charts[canvasId];
    }
    
    createConversationStartersChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.map(u => u.name),
                datasets: [{
                    data: data.map(u => u.count),
                    backgroundColor: this.chartColors.slice(0, data.length),
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        return this.charts[canvasId];
    }
    
    createUserMessageLengthChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        const users = Object.keys(data);
        const lengths = Object.values(data);
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: users,
                datasets: [{
                    label: 'Average Message Length (characters)',
                    data: lengths,
                    backgroundColor: this.chartColors.slice(0, users.length),
                    borderColor: this.chartColors.slice(0, users.length),
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white'
                    }
                },
                scales: {
                    x: { title: { display: true, text: 'Users' } },
                    y: { 
                        beginAtZero: true,
                        title: { display: true, text: 'Average Characters' }
                    }
                }
            }
        });
        
        return this.charts[canvasId];
    }
    
    createUserEmojiUsageChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        const users = Object.keys(data);
        const emojiCounts = users.map(user => data[user].count);
        const uniqueEmojis = users.map(user => data[user].unique_emojis);
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: users,
                datasets: [
                    {
                        label: 'Total Emojis',
                        data: emojiCounts,
                        backgroundColor: this.hexToRgba(this.defaultColors.primary, 0.7),
                        borderColor: this.defaultColors.primary,
                        borderWidth: 1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Unique Emojis',
                        data: uniqueEmojis,
                        backgroundColor: this.hexToRgba(this.defaultColors.secondary, 0.7),
                        borderColor: this.defaultColors.secondary,
                        borderWidth: 1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white'
                    }
                },
                scales: {
                    x: { title: { display: true, text: 'Users' } },
                    y: { 
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: { display: true, text: 'Total Emojis' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: { display: true, text: 'Unique Emojis' },
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });
        
        return this.charts[canvasId];
    }
    
    createSharedDomainsChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        const domains = data.slice(0, 10); // Top 10 domains
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: domains.map(d => d.domain),
                datasets: [{
                    label: 'Links Shared',
                    data: domains.map(d => d.count),
                    backgroundColor: this.chartColors.slice(0, domains.length),
                    borderColor: this.chartColors.slice(0, domains.length),
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white'
                    }
                },
                scales: {
                    x: { 
                        beginAtZero: true,
                        title: { display: true, text: 'Number of Links' }
                    },
                    y: { title: { display: true, text: 'Domains' } }
                }
            }
        });
        
        return this.charts[canvasId];
    }
    
    createAdvancedHeatmap(containerId, data) {
        const container = document.getElementById(containerId);
        if (!container) return null;
        
        const { days, hours, data: matrix, max_count } = data;
        
        // Clear existing content
        container.innerHTML = '';
        
        // Create heatmap HTML structure
        const heatmapHTML = `
            <div class="heatmap-container">
                <div class="heatmap-header">
                    <div class="heatmap-corner"></div>
                    ${hours.map(hour => `<div class="heatmap-hour">${hour}</div>`).join('')}
                </div>
                ${days.map((day, dayIndex) => `
                    <div class="heatmap-row">
                        <div class="heatmap-day">${day}</div>
                        ${hours.map((hour, hourIndex) => {
                            const value = matrix[dayIndex][hourIndex];
                            const intensity = max_count > 0 ? value / max_count : 0;
                            const color = this.getHeatmapColor(intensity);
                            return `<div class="heatmap-cell" 
                                        style="background-color: ${color}" 
                                        title="${day} ${hour}: ${value} messages"
                                        data-value="${value}"></div>`;
                        }).join('')}
                    </div>
                `).join('')}
                <div class="heatmap-legend">
                    <span>Less</span>
                    <div class="legend-gradient"></div>
                    <span>More</span>
                </div>
            </div>
        `;
        
        container.innerHTML = heatmapHTML;
        
        // Add CSS if not already added
        this.addHeatmapStyles();
        
        return container;
    }
    
    getHeatmapColor(intensity) {
        // Create a color gradient from light to dark green
        const minColor = [240, 253, 244]; // Very light green
        const maxColor = [37, 211, 102];  // WhatsApp green
        
        const r = Math.round(minColor[0] + (maxColor[0] - minColor[0]) * intensity);
        const g = Math.round(minColor[1] + (maxColor[1] - minColor[1]) * intensity);
        const b = Math.round(minColor[2] + (maxColor[2] - minColor[2]) * intensity);
        
        return `rgb(${r}, ${g}, ${b})`;
    }
}

// Initialize chart manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chartManager = new ChartManager();
});