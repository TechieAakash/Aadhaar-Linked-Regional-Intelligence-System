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
        const apiPath = `/api/data/${filename}?v=${timestamp}`;
        
        console.log(`[ALRIS] Fetching: ${apiPath}`);
        
        try {
            const response = await fetch(apiPath);
            if (!response.ok) {
                // If API fails, try direct static path as second resort
                const staticPath = `${window.location.origin}/data/${filename}?v=${timestamp}`;
                console.warn(`[ALRIS] API Failed (${response.status}). Trying Static: ${staticPath}`);
                const localResp = await fetch(staticPath);
                if (localResp.ok) return await localResp.json();
                throw new Error(`Server API Error: ${response.status} | Static Path Error: ${localResp.status}`);
            }
            return await response.json();
        } catch (e) {
            console.error(`[ALRIS] Data Sync Failed for ${filename}:`, e.message);
            throw e; // Propagate the error to the caller
        }
    },

    async getSystemHealth() {
        try {
            const response = await fetch('/api/stats');
            if (response.ok) return await response.json();
        } catch (e) {}
        return { status: "Offline", engine_health: "Standby", total_records: "N/A" };
    },

    async fetchBenchmarkingData() {
        return await this.fetchJson('peer_benchmarks.json');
    },

    async fetchSocialRisk() {
        try {
            const response = await fetch('/api/social/risk');
            if (response.ok) return await response.json();
        } catch (e) {}
        return [];
    },

    async fetchWatchlist() {
        try {
            const response = await fetch('/api/data/watchlist_active.json');
            if (response.ok) return await response.json();
        } catch (e) {}
        return {};
    }
};

window.DataLoader = DataLoader;
