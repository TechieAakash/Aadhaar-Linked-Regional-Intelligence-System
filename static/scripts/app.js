/**
 * ALRIS - Main Application Controller
 * Orchestrates the Aadhaar Analytics & Governance Decision Support System
 */

const App = {
    data: null,

    /**
     * Entry point
     */
    async init() {
        console.log('[ALRIS] Initializing System Overhaul (Phase 8)...');
        
        try {
            // 1. Initial Data Fetch
            this.data = await DataLoader.loadDashboardData();
            
            // 2. Initialize Subsystems
            Filters.init(this.data);
            this.updateHealth();
            this.bindEvents();
            
            // 3. Initial Render
            this.renderAll();

            // 4. Set up periodic health checks
            setInterval(() => this.updateHealth(), 30000);

            console.log('[ALRIS] System Ready.');
        } catch (error) {
            console.error('[ALRIS] Initialization failed:', error);
            // Show global error state in UI if needed
        }
    },

    bindEvents() {
        // Listen for filter updates
        window.addEventListener('alris:filterUpdate', (e) => {
            console.log('[ALRIS] Filters Updated:', e.detail);
            this.renderAll(e.detail);
        });

        // Navigation handled by hash or simple click
        document.querySelectorAll('.nav-item a').forEach(link => {
            link.addEventListener('click', (e) => {
                document.querySelectorAll('.nav-item a').forEach(a => a.classList.remove('active'));
                link.classList.add('active');
            });
        });
    },

    /**
     * Render the entire dashboard or specific filtered slice
     */
    renderAll(filter = Filters.current) {
        this.updateExecutiveSummary(filter);
        this.renderLifecycleIntelligence(filter);
        this.renderForecastingModule(filter);
        this.renderAnomalyPanel(filter);
        this.renderDecisionSupport(filter);
        this.renderRegionalDrilldown(filter);
        this.updateMetadata(filter);
    },

    /**
     * Update top-row stat cards
     */
    updateExecutiveSummary(filter) {
        const stats = this.data.pipelineSummary?.execution_summary || {};
        
        // Mocking animated counters for demo
        this.animateValue('totalEnrolments', 0, 1380542310, 2000);
        this.animateValue('activeUpdateRate', 0, 12.4, 2000, 1);
        this.animateValue('coverageScore', 0, 99.2, 2000, 1);
        this.animateValue('dataQuality', 0, 94, 2000);
    },

    /**
     * Module 3: Lifecycle
     */
    renderLifecycleIntelligence(filter) {
        const insights = this.data.lifecycleInsights || {};
        const labels = Object.keys(insights.demographic_intensity || {}).slice(0, 10);
        const data = Object.values(insights.demographic_intensity || {}).slice(0, 10);

        Charts.renderLine('lifecycleCurve', labels, [{
            label: 'Update Intensity',
            data: data,
            borderColor: '#FF9933',
            backgroundColor: 'rgba(255, 153, 51, 0.1)',
            fill: true,
            tension: 0.4
        }], {
            plugins: { title: { display: true, text: 'LIFECYCLE UPDATE PATTERNS' } }
        });

        // Mock heatmap grid
        const heatmapData = Array.from({ length: 5 }, () => Array.from({ length: 12 }, () => Math.random()));
        Charts.renderHeatmap('lifecycleHeatmap', heatmapData);
    },

    /**
     * Module 4: Forecasting
     */
    renderForecastingModule(filter) {
        const forecasts = this.data.forecasts || {};
        const labels = forecasts.dates || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
        const values = forecasts.forecast || [100, 120, 115, 130, 145, 140];
        const low = values.map(v => v * 0.9);
        const high = values.map(v => v * 1.1);

        Charts.renderForecast('demandForecast', labels, values, low, high);
    },

    /**
     * Module 5: Anomalies
     */
    renderAnomalyPanel(filter) {
        const anomalies = this.data.anomalies?.summary || {};
        const count = anomalies.total_anomalies || 0;
        document.getElementById('anomalyCount').textContent = count;
        
        // Mock table rows
        const table = document.getElementById('anomalyTable');
        if (table) {
            table.innerHTML = `
                <tr><td>UP_District_12</td><td>Spike</td><td>Biometric Updates > 400%</td><td>Critical</td></tr>
                <tr><td>KA_District_04</td><td>Drop</td><td>Enrolment Lag</td><td>High</td></tr>
                <tr><td>MH_District_09</td><td>Shift</td><td>Demographic Variance</td><td>Medium</td></tr>
            `;
        }
    },

    /**
     * Module 6: Decision Support
     */
    renderDecisionSupport(filter) {
        const recs = this.data.recommendations?.recommendations || [];
        const container = document.getElementById('recommendationsGrid');
        if (!container) return;

        container.innerHTML = recs.slice(0, 3).map(rec => `
            <div class="card recommendation-card ${rec.priority.toLowerCase()}">
                <div class="card-header">
                    <span class="priority-badge ${rec.priority.toLowerCase()}">${rec.priority}</span>
                    <span class="impact-score">Impact: ${rec.impact_score}/10</span>
                </div>
                <div class="rec-action">${rec.action}</div>
                <div class="rec-finding">Finding: ${rec.finding}</div>
                <div class="rec-timeline">Timeline: 2-4 Weeks</div>
            </div>
        `).join('');
    },

    renderRegionalDrilldown(filter) {
        // Map logic would go here (Leaflet/D3)
        // For now, placeholder or table
    },

    /**
     * Metadata & Health
     */
    async updateHealth() {
        const health = await DataLoader.getSystemHealth();
        if (health) {
            const healthEl = document.getElementById('engineHealth');
            if (healthEl) {
                healthEl.textContent = `${health.engine_health} (${health.status})`;
                healthEl.className = health.status === 'Running' ? 'text-green' : 'text-saffron';
            }
        }
    },

    updateMetadata(filter) {
        const timestamp = new Date().toLocaleString();
        document.getElementById('lastUpdated').textContent = `System Last Updated: ${timestamp}`;
        document.getElementById('currentScope').textContent = filter.state === 'all' ? 'National (All India)' : filter.state;
    },

    /**
     * Animation helper for counters
     */
    animateValue(id, start, end, duration, decimals = 0) {
        const obj = document.getElementById(id);
        if (!obj) return;
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const val = (progress * (end - start) + start).toLocaleString(undefined, { 
                minimumFractionDigits: decimals, 
                maximumFractionDigits: decimals 
            });
            obj.innerHTML = id.includes('Rate') ? val + '%' : val;
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => App.init());
