/**
 * ALRIS - Visual Intelligence Layer
 * High-performance chart rendering with official theme defaults
 */

const Charts = {
    instances: {},

    // Official Chart Themes
    theme: {
        fonts: {
            family: "'Inter', sans-serif",
            size: 11
        },
        colors: {
            saffron: '#FF9933',
            green: '#138808',
            navy: '#000080',
            gray: '#6b7280'
        }
    },

    /**
     * Get Default Configuration
     */
    getDefaultOptions(title = '') {
        return {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 1200, easing: 'easeOutQuart' },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        font: { family: this.theme.fonts.family, size: 12, weight: '500' }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 128, 0.9)',
                    titleFont: { family: this.theme.fonts.family, size: 14, weight: 'bold' },
                    bodyFont: { family: this.theme.fonts.family },
                    padding: 12,
                    cornerRadius: 4
                },
                title: {
                    display: !!title,
                    text: title,
                    align: 'start',
                    font: { family: this.theme.fonts.family, size: 16, weight: 'bold' },
                    color: '#000080',
                    padding: { bottom: 20 }
                }
            },
            scales: {
                x: { grid: { display: false }, ticks: { font: { size: 10 } } },
                y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { font: { size: 10 } } }
            }
        };
    },

    /**
     * Render Standard Line Chart
     */
    renderLine(id, labels, datasets, options = {}) {
        if (this.instances[id]) this.instances[id].destroy();

        const ctx = document.getElementById(id).getContext('2d');
        this.instances[id] = new Chart(ctx, {
            type: 'line',
            data: { labels, datasets },
            options: { ...this.getDefaultOptions(), ...options }
        });
    },

    /**
     * Render Complex Forecast Chart with Bands
     */
    renderForecast(id, labels, data, confidenceLow, confidenceHigh) {
        if (this.instances[id]) this.instances[id].destroy();

        const datasets = [
            {
                label: 'Aadhaar Demand Forecast',
                data: data,
                borderColor: this.theme.colors.navy,
                backgroundColor: 'transparent',
                borderWidth: 3,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: this.theme.colors.navy,
                zIndex: 10
            },
            {
                label: 'Confidence Interval (95%)',
                data: confidenceHigh,
                borderColor: 'transparent',
                backgroundColor: 'rgba(0, 0, 128, 0.05)',
                fill: '+1',
                pointRadius: 0
            },
            {
                label: 'Confidence Interval (low)',
                data: confidenceLow,
                borderColor: 'transparent',
                backgroundColor: 'rgba(0, 0, 128, 0.05)',
                fill: false,
                pointRadius: 0
            }
        ];

        this.renderLine(id, labels, datasets, {
            interaction: { mode: 'index', intersect: false },
            scales: {
                y: { beginAtZero: false }
            }
        });
    },

    /**
     * Render Lifecycle Heatmap
     */
    renderHeatmap(containerId, gridData) {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.innerHTML = '';
        container.style.display = 'grid';
        container.style.gridTemplateColumns = `repeat(${gridData[0].length}, 1fr)`;

        gridData.flat().forEach(val => {
            const cell = document.createElement('div');
            cell.className = 'heatmap-cell';
            const intensity = Math.min(val * 10, 1);
            cell.style.backgroundColor = `rgba(0, 0, 128, ${intensity})`;
            cell.title = `Intensity: ${val.toFixed(2)}`;
            container.appendChild(cell);
        });
    }
};

window.Charts = Charts;
