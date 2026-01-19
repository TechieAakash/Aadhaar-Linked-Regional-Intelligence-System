const VERSION = "4.0.0-ROBUST-FIX";
console.log(`[ALRIS] DataLoader Engine Active: ${VERSION}`);

const DataLoader = {
    apiBase: window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
               ? '/api/data/' 
               : 'data/',

    async fetchAll() {
        console.log('[ALRIS] Syncing Analytical Sprints...');
        const files = ['state_data.json', 'state_features.json', 'lifecycle_insights.json', 'forecasts.json', 'anomalies.json', 'recommendations.json'];
        const results = await Promise.all([
            ...files.map(f => this.fetchJson(f)),
            this.fetchWatchlist()
        ]);
        
        return {
            stateData: results[0],
            stateFeatures: results[1],
            lifecycle: results[2],
            forecasts: results[3],
            anomalies: results[4],
            recommendations: results[5],
            watchlist: results[6]
        };
    },

    async fetchJson(filename) {
        const timestamp = new Date().getTime();
        // Use static path directly on Netlify
        const staticPath = `/data/${filename}?v=${timestamp}`;
        
        console.log(`[ALRIS] Fetching: ${staticPath}`);
        
        try {
            const response = await fetch(staticPath);
            if (!response.ok) {
                throw new Error(`Static Path Error: ${response.status}`);
            }
            return await response.json();
        } catch (e) {
            console.error(`[ALRIS] Data Sync Failed for ${filename}:`, e.message);
            return []; // Return empty array as fallback
        }
    },

    async getSystemHealth() {
        // Static hosting - return default status
        return { status: "Static", engine_health: "Active", total_records: "Pre-calculated" };
    },

    async fetchBenchmarkingData() {
        return await this.fetchJson('peer_benchmarks.json');
    },

    async fetchSocialRisk() {
        try {
            const response = await fetch('/data/integrated_service_risk.json');
            if (response.ok) return await response.json();
        } catch (e) {}
        return [];
    },

    async fetchWatchlist() {
        try {
            const response = await fetch('/data/watchlist_active.json');
            if (response.ok) return await response.json();
        } catch (e) {}
        return {};
    }
};

window.DataLoader = DataLoader;
