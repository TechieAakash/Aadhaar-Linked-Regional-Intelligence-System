/**
 * ALRIS Service Equity Index (SEI) Dashboard Logic
 * Handles data fetching, KPI updates, and Chart.js visualizations.
 */

document.addEventListener('DOMContentLoaded', async () => {
    
    // API Endpoints
    // API Endpoints
    // API Endpoints
    const DATA_URL = '/api/social/fairness'; // Real Backend Data
    const SUMMARY_URL = '/api/stats'; // System Stats as fallback or computed locally

    // UIDAI Authentication
    const API_KEY = "579b464db66ec23bdd000001623c2de44ffb40755360bbc473134c16";
    const API_HEADERS = {
        'x-api-key': API_KEY, // Authentic Use
        'Content-Type': 'application/json'
    };

    // State Variables
    let seiData = [];
    let summaryData = {};
    let charts = {};

    /**
     * Initialize Dashboard
     */
    async function init() {
        try {
            await fetchData();
            updateKPIs();
            renderRankingList();
            populateDropdown();
            initCharts();
        } catch (error) {
            console.error('SEI Initialization Error:', error);
            document.querySelector('.dashboard-container').innerHTML = `
                <div class="alert alert-danger">
                    <strong>System Error:</strong> Failed to load Service Equity data.<br>
                    Please ensure the backend pipeline has been executed.
                </div>
            `;
        }
    }

    /**
     * Fetch Data from JSON Artifacts
     */
    async function fetchData() {
        const [dResponse, sResponse] = await Promise.all([
            fetch(DATA_URL, { headers: API_HEADERS }),
            fetch(SUMMARY_URL, { headers: API_HEADERS }).catch(() => ({ ok: true, json: () => ({}) })) // Soft fail on summary
        ]);

        if (!dResponse.ok) throw new Error('Data fetch failed');

        seiData = await dResponse.json();
        summaryData = {}; // Dummy empty logic for now, using calculated stats in updateKPIs
        
        console.log('SEI Data Loaded:', seiData.length, 'records');
    }

    /**
     * Update Top-Level KPI Cards
     */
    async function updateKPIs() {
        if (!document.getElementById('nationalScore')) return;
        
        // Calculate National Average from Data
        const avgScore = seiData.reduce((acc, curr) => acc + (curr.inclusion_priority_score || 0), 0) / seiData.length;
        
        document.getElementById('nationalScore').textContent = avgScore.toFixed(1);
        
        // Interpretation Color Logic
        const statusEl = document.getElementById('nationalStatus');
        if (avgScore >= 80) {
            statusEl.textContent = "High Equity & Inclusion";
            statusEl.style.color = "#48bb78"; // Green
        } else if (avgScore >= 60) {
            statusEl.textContent = "Moderate Equity";
            statusEl.style.color = "#ecc94b"; // Yellow
        } else {
            statusEl.textContent = "Significant Gaps Detected";
            statusEl.style.color = "#f56565"; // Red
        }

        // Top Performer
        const sorted = [...seiData].sort((a, b) => (b.inclusion_priority_score || 0) - (a.inclusion_priority_score || 0));
        const topState = sorted[0];
        if (topState) {
            document.getElementById('topStateName').textContent = topState.state;
            document.getElementById('topStateScore').textContent = `Score: ${topState.inclusion_priority_score.toFixed(1)}`;
        }

        // Bottom Performer
        const bottomState = sorted[sorted.length - 1];
        if (bottomState) {
            document.getElementById('bottomStateName').textContent = bottomState.state;
            document.getElementById('bottomStateScore').textContent = `Score: ${bottomState.inclusion_priority_score.toFixed(1)}`;
        }
    }

    /**
     * Render rankings side-panel
     */
    function renderRankingList() {
        const listEl = document.getElementById('rankingList');
        if (!listEl) return;
        
        listEl.innerHTML = '';

        // Sort data by Score DESC
        const sortedData = [...seiData].sort((a, b) => (b.inclusion_priority_score || 0) - (a.inclusion_priority_score || 0));

        sortedData.forEach((item, index) => {
            const rank = index + 1;
            const li = document.createElement('li');
            li.className = 'rank-item';
            
            // Rank Badge Class
            let badgeClass = 'rank-badge';
            if (rank === 1) badgeClass += ' top-1';
            if (rank === 2) badgeClass += ' top-2';
            if (rank === 3) badgeClass += ' top-3';
            
            // Interpretation Text
            let interp = "Balanced Access";
            if (item.inclusion_priority_score < 40) interp = "Critical Gaps";
            else if (item.inclusion_priority_score > 80) interp = "Exemplary";

            li.innerHTML = `
                <div class="${badgeClass}">${rank}</div>
                <div style="flex:1;">
                    <div style="font-weight:700; font-size:0.9rem;">${item.state}</div>
                    <div style="font-size:0.75rem; opacity:0.7;">${interp}</div>
                </div>
                <div style="font-weight:800; font-size:1.1rem; color:var(--gov-blue);">${item.inclusion_priority_score ? item.inclusion_priority_score.toFixed(1) : '0.0'}</div>
            `;
            
            listEl.appendChild(li);
        });
    }

    /**
     * Populate Comparison Dropdown
     */
    function populateDropdown() {
        const select = document.getElementById('stateSelect');
        if (!select) return;

        const states = [...new Set(seiData.map(s => s.state.trim()))].sort();
        states.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s;
            opt.textContent = s;
            select.appendChild(opt);
        });

        // Event Listener
        select.addEventListener('change', (e) => {
            const state = e.target.value;
            updateRadarChart(state);
            updateCompositionChart(state);
            updateBarChart(state);
            updateScatterChart(state);
        });
    }

    /**
     * Initialize Charts
     */
    function initCharts() {
        initRadarChart();
        initScatterChart();
        initCompositionChart();
        initBarChart();
        initHeatmapChart();
    }

    /**
     * 1. Component Analysis Radar Chart
     */
    function initRadarChart() {
        const canvas = document.getElementById('componentChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        
        // Initial Data: National Average
        // Metrics: Rural Parity, Gender Parity, Elderly Access, Social Inclusion (inv. SVI)
        
        // Helper to get mean safely
        const getMean = (key) => {
            const sum = seiData.reduce((a, b) => a + (Number(b[key]) || 0), 0);
            return sum / (seiData.length || 1);
        };
        
        const avg = {
            rural: getMean('rural_parity_index'),
            gender: getMean('gender_parity_index'),
            elderly: getMean('elderly_access_index'),
            inclusion: 100 - getMean('social_vulnerability_index') // Invert SVI so high is good
        };

        charts.radar = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Rural Parity', 'Gender Parity', 'Elderly Access', 'Social Inclusion'],
                datasets: [{
                    label: 'National Average',
                    data: [avg.rural, avg.gender, avg.elderly, avg.inclusion],
                    fill: true,
                    backgroundColor: 'rgba(26, 54, 93, 0.2)', // Gov Blue
                    borderColor: '#1a365d',
                    pointBackgroundColor: '#1a365d',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#1a365d'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(0,0,0,0.1)' },
                        grid: { color: 'rgba(0,0,0,0.05)' },
                        pointLabels: {
                            font: { family: 'Inter', size: 11, weight: '600' }
                        },
                        suggestedMin: 0,
                        suggestedMax: 100
                    }
                },
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    function updateRadarChart(stateName) {
        if (stateName === 'national') {
            // Reset to average
            const avg = [
                d3_mean(seiData, 'score_availability'),
                d3_mean(seiData, 'score_utilization'),
                d3_mean(seiData, 'score_timeliness'),
                d3_mean(seiData, 'score_load_balance'),
                d3_mean(seiData, 'score_demo_coverage')
            ];
            charts.radar.data.datasets = [{
                label: 'National Average',
                data: avg,
                fill: true,
                backgroundColor: 'rgba(26, 54, 93, 0.2)',
                borderColor: '#1a365d',
                pointBackgroundColor: '#1a365d'
            }];
        } else {
            // Compare State vs National
            const state = seiData.find(s => s.state === stateName);
            if (!state) return;

             // Helper to get mean safely
            const getMean = (key) => {
                const sum = seiData.reduce((a, b) => a + (Number(b[key]) || 0), 0);
                return sum / (seiData.length || 1);
            };
            
            const avg = [
                getMean('rural_parity_index'),
                getMean('gender_parity_index'),
                getMean('elderly_access_index'),
                100 - getMean('social_vulnerability_index')
            ];

            const stateScores = [
                state.rural_parity_index || 0,
                state.gender_parity_index || 0,
                state.elderly_access_index || 0,
                100 - (state.social_vulnerability_index || 0)
            ];

            charts.radar.data.datasets = [
                {
                    label: 'National Avg',
                    data: avg,
                    fill: true,
                    backgroundColor: 'rgba(200, 200, 200, 0.2)',
                    borderColor: '#ccc',
                    pointBackgroundColor: '#ccc',
                    borderDash: [5, 5]
                },
                {
                    label: stateName,
                    data: stateScores,
                    fill: true,
                    backgroundColor: 'rgba(237, 137, 54, 0.2)', // Saffron
                    borderColor: '#ed8936',
                    pointBackgroundColor: '#ed8936',
                    pointBorderColor: '#fff'
                }
            ];
        }
        charts.radar.update();
    }

    /**
     * Update Composition Pie Chart (New Function)
     */
    function updateCompositionChart(stateName) {
        if (!charts.pie) return;

        let data = [];
        const datasets = charts.pie.data.datasets[0];

        if (stateName === 'national') {
            const getMean = (key) => seiData.reduce((a, b) => a + (Number(b[key]) || 0), 0) / (seiData.length || 1);
            data = [
                 getMean('rural_parity_index'),
                 getMean('gender_parity_index'),
                 getMean('elderly_access_index'),
                 100 - getMean('social_vulnerability_index')
            ];
            datasets.label = 'National Average';
        } else {
            const state = seiData.find(s => s.state === stateName);
            if (!state) return;
            data = [
                state.rural_parity_index || 0,
                state.gender_parity_index || 0,
                state.elderly_access_index || 0,
                100 - (state.social_vulnerability_index || 0)
            ];
            datasets.label = stateName;
        }
        
        datasets.data = data;
        charts.pie.update();
    }

    /**
     * Update Parity Bar Chart (New Function)
     */
    function updateBarChart(stateName) {
        if (!charts.bar) return;

        let data = [];
        const datasets = charts.bar.data.datasets[0];

        if (stateName === 'national') {
            // Revert to National mean
            const getMean = (key) => seiData.reduce((a, b) => a + (Number(b[key]) || 0), 0) / (seiData.length || 1);
            data = [
                getMean('rural_parity_index'),
                getMean('gender_parity_index'),
                getMean('elderly_access_index'),
                getMean('tribal_parity_index')
            ];
            datasets.label = 'National Average';
            datasets.backgroundColor = ['#48bb78', '#ecc94b', '#f56565', '#4299e1'];
        } else {
            const state = seiData.find(s => s.state === stateName);
            if (!state) return;
            data = [
                state.rural_parity_index || 0,
                state.gender_parity_index || 0,
                state.elderly_access_index || 0,
                state.tribal_parity_index || 0
            ];
            datasets.label = stateName;
            // Highlight bars that are below national avg? For now keep same colors
            datasets.backgroundColor = ['#48bb78', '#ecc94b', '#f56565', '#4299e1'];
        }

        datasets.data = data;
        charts.bar.update();
    }

    /**
     * Update Scatter Chart (New Function)
     */
    function updateScatterChart(stateName) {
        if (!charts.scatter) return;

        const datasets = charts.scatter.data.datasets[0];
        
        // Reset colors and radius
        const defaultColor = (ctx) => {
            const v = ctx.raw;
            if (v && v.x > 50 && v.y > 50) return '#38a169'; 
            return '#2c5282';
        };

        if (stateName === 'national') {
            datasets.backgroundColor = defaultColor;
            datasets.pointRadius = 6;
        } else {
            // Highlight specific state
            datasets.backgroundColor = (ctx) => {
                const pt = ctx.raw;
                if (pt && pt.state === stateName) return '#e53e3e'; // Highlight Red
                return '#cbd5e0'; // Gray out others
            };
            datasets.pointRadius = (ctx) => {
                const pt = ctx.raw;
                if (pt && pt.state === stateName) return 10;
                return 4;
            };
        }
        charts.scatter.update();
    }

    /**
     * 2. Scatter Chart (Correlation)
     */
    function initScatterChart() {
        const canvas = document.getElementById('scatterChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        
        const scatterData = seiData.map(s => ({
            x: s.rural_parity_index || 0,
            y: s.inclusion_priority_score || 0,
            state: s.state
        }));

        charts.scatter = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'States',
                    data: scatterData,
                    backgroundColor: (ctx) => {
                        // Color based on position (Good quadrant = Green)
                        const v = ctx.raw;
                        if (v && v.x > 50 && v.y > 50) return '#38a169'; // Green
                        return '#2c5282'; // Blue
                    },
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: { display: true, text: 'Implementation Score (Rural Parity)' },
                        min: 0, max: 105
                    },
                    y: {
                        title: { display: true, text: 'Overall Inclusion Score (0-100)' },
                        min: 0, max: 105
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const pt = context.raw;
                                return `${pt.state}: Rural Parity ${pt.x.toFixed(1)}, Inclusion Score ${pt.y.toFixed(1)}`;
                            }
                        }
                    },
                    legend: { display: false }
                }
            }
        });
    }

    /**
     * 3. Score Composition Pie Chart
     */
    function initCompositionChart() {
        const canvas = document.getElementById('compositionChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        
        // Use national average data as default
        const getMean = (key) => {
            const sum = seiData.reduce((a, b) => a + (Number(b[key]) || 0), 0);
            return sum / (seiData.length || 1);
        };
        const data = [
             getMean('rural_parity_index'),
             getMean('gender_parity_index'),
             getMean('elderly_access_index'),
             100 - getMean('social_vulnerability_index')
        ];

        charts.pie = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Rural Parity', 'Gender Parity', 'Elderly Access', 'Social Inclusion'],
                datasets: [{
                    data: data,
                    backgroundColor: [
                        '#38a169', // Green
                        '#dd6b20', // Orange
                        '#805ad5', // Purple
                        '#3182ce'  // Blue
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: { position: 'right' },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return ` ${context.label}: ${context.raw.toFixed(1)}`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Helper: Calculate Mean
    function d3_mean(data, key) {
        const sum = data.reduce((a, b) => a + (b[key] || 0), 0);
        return sum / data.length;
    }


    /**
     * 5. Parity Gap Analysis Bar Chart
     */
    function initBarChart() {
        const canvas = document.getElementById('barChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        
        // Use National vs Selected State
        // Defaults to National Average
        const getMean = (key) => seiData.reduce((a, b) => a + (Number(b[key]) || 0), 0) / (seiData.length || 1);
        
        const labels = ['Rural Parity', 'Gender Equity', 'Elderly Access', 'ST/SC Gap'];
        const dataVals = [
            getMean('rural_parity_index'),
            getMean('gender_parity_index'),
            getMean('elderly_access_index'),
            getMean('tribal_parity_index')
        ];

        charts.bar = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'National Average',
                    data: dataVals,
                    backgroundColor: ['#48bb78', '#ecc94b', '#f56565', '#4299e1'],
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, max: 100 }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    /**
     * 6. State Performance Heatmap (Dot Graph)
     */
    function initHeatmapChart() {
        const canvas = document.getElementById('heatmapChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        
        // Prepare data: x = State Index, y = Score, r = Size (Pop density approx?)
        // Color intensity = Score
        const sorted = [...seiData].sort((a,b) => b.inclusion_priority_score - a.inclusion_priority_score);
        
        const dots = sorted.map((s, i) => ({
            x: i, // Rank
            y: s.inclusion_priority_score,
            state: s.state,
            score: s.inclusion_priority_score
        }));

        charts.heatmap = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'States',
                    data: dots,
                    backgroundColor: (ctx) => {
                        const v = ctx.raw ? ctx.raw.score : 0;
                        // Heatmap gradient logic
                        if (v > 80) return `rgba(56, 161, 105, ${v/100})`; // Green
                        if (v > 50) return `rgba(236, 201, 75, ${v/100})`; // Yellow
                        return `rgba(245, 101, 101, ${v/100})`; // Red
                    },
                    pointRadius: 8,
                    pointHoverRadius: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { display: false }, // Hide rank axis
                    y: { 
                        title: { display: true, text: 'Inclusion Score' },
                        min: 0, max: 110 
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.raw.state}: ${ctx.raw.score.toFixed(1)}`
                        }
                    },
                    legend: { display: false }
                }
            }
        });
    }

    // Run
    init();
});
