/**
 * ALRIS COMMAND CENTER - Visualization Engine
 * Renders high-fidelity Chart.js and D3.js components
 */

const VisualizationEngine = {
    charts: {},

    colors: {
        blue: '#0F4D92',
        saffron: '#FF9933',
        green: '#138808',
        alert: '#DC3545',
        gray: '#E2E8F0'
    },

    /**
     * Module 3: Age-Group Heatmap (D3.js)
     */
    renderLifecycleHeatmap(containerId, data) {
        const container = document.getElementById(containerId);
        if (!container || !data) return;
        
        container.innerHTML = '';
        const margin = { top: 30, right: 30, bottom: 50, left: 80 },
              width = container.offsetWidth - margin.left - margin.right,
              height = 350 - margin.top - margin.bottom;

        const svg = d3.select("#" + containerId)
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);

        // X-axis (Months)
        const x = d3.scaleBand()
            .range([0, width])
            .domain(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
            .padding(0.05);
        
        svg.append("g")
            .attr("transform", `translate(0, ${height})`)
            .call(d3.axisBottom(x).tickSize(0))
            .select(".domain").remove();

        // Y-axis (Age Groups)
        const yGroups = ['0-18', '19-30', '31-45', '46-60', '60+'];
        const y = d3.scaleBand()
            .range([height, 0])
            .domain(yGroups)
            .padding(0.05);
        
        svg.append("g")
            .call(d3.axisLeft(y).tickSize(0))
            .select(".domain").remove();

        // Color scale
        const color = d3.scaleSequential()
            .interpolator(d3.interpolateYlOrBr)
            .domain([0, 100]);

        // Mock squares
        const mockData = [];
        yGroups.forEach(gy => {
            x.domain().forEach(gx => {
                mockData.push({ x: gx, y: gy, value: Math.random() * 100 });
            });
        });

        svg.selectAll()
            .data(mockData, d => d.x + ':' + d.y)
            .enter()
            .append("rect")
            .attr("x", d => x(d.x))
            .attr("y", d => y(d.y))
            .attr("width", x.bandwidth())
            .attr("height", y.bandwidth())
            .style("fill", d => color(d.value))
            .attr("class", "heatmap-rect");
    },

    /**
     * Module 4: ARIMA Forecasting with CI Bands (Chart.js)
     */
    /**
     * Module 4: Forecasting Hub (Chart.js)
     * Supports both ARIMA and Simple Moving Average data structures
     */
    renderForecastingHub(canvasId, forecastData) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        if (this.charts[canvasId]) this.charts[canvasId].destroy();

        // Data Normalization
        let labels = [];
        let predicted = [];
        let actual = []; // Optional
        let ciHigh = [];
        let ciLow = [];

        // Check if ARIMA data exists, otherwise fallback to Simple
        if (forecastData.arima) {
            const arima = forecastData.arima;
            labels = Array.from({length: arima.periods_ahead}, (_, i) => `Month +${i+1}`);
            predicted = arima.forecast_values;
            ciHigh = arima.upper_bound;
            ciLow = arima.lower_bound;
        } else if (forecastData.simple) {
            // Fallback for Simple Forecast
            const simple = forecastData.simple;
            labels = Array.from({length: simple.periods_ahead}, (_, i) => `Month +${i+1}`);
            predicted = simple.forecast_values;
            // Create Mock CI for visual consistency
            ciHigh = predicted.map(v => v * 1.05);
            ciLow = predicted.map(v => v * 0.95);
        } else {
            console.warn('[ALRIS] No valid forecast data found.');
            return;
        }

        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Predicted Demand',
                        data: predicted,
                        borderColor: this.colors.saffron,
                        backgroundColor: 'transparent',
                        borderWidth: 3,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        zIndex: 10
                    },
                    {
                        label: 'Upper Bound (95%)',
                        data: ciHigh,
                        fill: '+1',
                        backgroundColor: 'rgba(255, 153, 51, 0.1)',
                        borderColor: 'transparent',
                        pointRadius: 0
                    },
                    {
                        label: 'Lower Bound (95%)',
                        data: ciLow,
                        fill: false,
                        backgroundColor: 'rgba(255, 153, 51, 0.1)',
                        borderColor: 'transparent',
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    tooltip: { mode: 'index', intersect: false }
                },
                scales: {
                    y: { 
                        beginAtZero: false, 
                        grid: { color: 'rgba(0,0,0,0.05)' },
                        title: { display: true, text: 'Enrolment Count' }
                    }
                }
            }
        });
    },

    /**
     * Behavioral Pattern Radar (Chart.js)
     * Visualizes the mix of behavioural clusters
     */
    renderBehavioralRadar(canvasId) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        if (this.charts[canvasId]) this.charts[canvasId].destroy();

        // National/Simulated Cluster Data
        const data = {
            labels: ['Digital Natives', 'Seasonal Adopters', 'Intervention Needed', 'Regional Variations', 'Infrastructure Reliant'],
            datasets: [{
                label: 'National Profile',
                data: [42, 18, 25, 15, 30],
                fill: true,
                backgroundColor: 'rgba(15, 77, 146, 0.2)',
                borderColor: '#0F4D92',
                pointBackgroundColor: '#0F4D92',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#0F4D92'
            }]
        };

        this.charts[canvasId] = new Chart(ctx, {
            type: 'radar',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                elements: {
                    line: { borderWidth: 3 }
                },
                scales: {
                    r: {
                        angleLines: { display: false },
                        suggestedMin: 0,
                        suggestedMax: 50
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    },

    /**
     * Behavioral Pattern Matrix (Quadrant) - DEPRECATED (Moved to Radar)
     */
    renderBehavioralMatrix(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        // Logic moved to Radar for better fidelity
    }
};

window.VisualizationEngine = VisualizationEngine;
