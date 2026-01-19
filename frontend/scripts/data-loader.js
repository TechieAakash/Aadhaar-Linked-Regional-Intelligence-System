/**
 * ALRIS - Data Loader Module
 * Handles API orchestration and caching with skeleton screen support
 */

const DataLoader = {
    // Determine API origin
    get apiBase() {
        return window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
               ? '/api/data/' 
               : 'data/';
    },

    /**
     * Fetch all required dashboards datasets
     */
    async loadDashboardData() {
        const datasets = [
            'state_data.json', 'monthly_data.json', 'state_features.json',
            'lifecycle_insights.json', 'forecasts.json', 'anomalies.json',
            'recommendations.json', 'risk_analysis.json', 'pipeline_summary.json'
        ];

        console.log('[ALRIS] Orchestrating data fetch from:', this.apiBase);

        try {
            const results = await Promise.all(
                datasets.map(file => this.fetchJson(file))
            );

            return {
                stateData: results[0] || [],
                monthlyData: results[1] || [],
                stateFeatures: results[2] || [],
                lifecycleInsights: results[3] || {},
                forecasts: results[4] || {},
                anomalies: results[5] || {},
                recommendations: results[6] || {},
                riskAnalysis: results[7] || [],
                pipelineSummary: results[8] || {}
            };
        } catch (error) {
            console.error('[ALRIS] Critical Data Load Failure:', error);
            throw error;
        }
    },

    /**
     * Fetch single JSON file with error handling
     */
    async fetchJson(filename) {
        try {
            const response = await fetch(this.apiBase + filename);
            if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
            return await response.json();
        } catch (e) {
            console.warn(`[ALRIS] Failed to fetch ${filename}. Fallback check...`);
            // Attempt to fetch from local 'data/' folder if API fails (for pure frontend serving)
            if (this.apiBase.includes('/api/')) {
                try {
                    const localResp = await fetch('data/' + filename);
                    if (localResp.ok) return await localResp.json();
                } catch (localErr) {
                    console.error('[ALRIS] Full fallback failure.');
                }
            }
            return null;
        }
    },

    /**
     * Get system health metrics
     */
    async getSystemHealth() {
        try {
            const response = await fetch('/api/stats');
            if (response.ok) return await response.json();
        } catch (e) {
            return { status: 'Offline', engine_health: 'Unavailable' };
        }
        return null;
    }
};

window.DataLoader = DataLoader;
