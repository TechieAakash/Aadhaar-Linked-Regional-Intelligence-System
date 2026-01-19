/**
 * ALRIS COMMAND CENTER - Universal Orchestrator
 * Bootstraps the Command Center and manages module communication
 */

const CommandCenter = {
    data: null,

    async init() {
        console.group('[ALRIS] AADHAAR COMMAND CENTER BOOT');
        
        try {
            // 1. Ingest Data from API
            this.data = await DataLoader.loadDashboardData();
            
            // 2. Initial Dashboard Render (Overview stats)
            this.renderExecutiveSummary();
            
            // 3. Start Polling for System Health
            this.updateSystemStatus();
            setInterval(() => this.updateSystemStatus(), 30000);

            console.log('[ALRIS] COMMAND CENTER - ONLINE');
        } catch (err) {
            console.error('[ALRIS] BOOT FAILURE:', err);
        }
        console.groupEnd();
    },

    /**
     * Module 1 & 2: Executive Summary
     */
    renderExecutiveSummary() {
        if (!this.data) return;
        
        // National Statistics (Demo/Simulated for high-fidelity)
        this.animateCounter('nationalCoverage', 94.2);
        this.animateCounter('updateIntensity', 3.2);
        
        if (this.data.anomalies) {
            const count = this.data.anomalies.summary?.total_anomalies || 0;
            document.getElementById('anomalyCount').textContent = count;
        }
    },

    async updateSystemStatus() {
        try {
            const stats = await DataLoader.getSystemHealth();
            if (stats) {
                const statusEl = document.getElementById('serverStatus');
                if (statusEl) statusEl.textContent = `Live: ${stats.status} | Engine: ${stats.engine_health} | Records: ${stats.total_records}`;
                
                const healthEl = document.getElementById('engineHealth');
                if (healthEl) healthEl.textContent = stats.engine_health;
            }
        } catch (e) {}
    },

    animateCounter(id, target) {
        const el = document.getElementById(id);
        if (!el) return;
        let start = 0;
        const duration = 2000;
        const startTime = performance.now();
        
        const step = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const val = (progress * target).toFixed(id.includes('Rate') || id.includes('national') ? 1 : 1);
            el.textContent = val + (id.includes('Rate') || id.includes('national') ? '%' : '');
            
            if (progress < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
    }
};

document.addEventListener('DOMContentLoaded', () => CommandCenter.init());
window.CommandCenter = CommandCenter;
