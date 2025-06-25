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
}

// Initialize chart manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chartManager = new ChartManager();
});