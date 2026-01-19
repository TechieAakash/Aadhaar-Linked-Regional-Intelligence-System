/**
 * ALRIS COMMAND CENTER - Policy Recommendation Engine
 * Renders priority-coded decision support cards
 */

const RecommendationEngine = {
    
    render(containerId, data) {
        const container = document.getElementById(containerId);
        // Robust check: data might be the whole object or just the array
        const recs = Array.isArray(data) ? data : (data?.recommendations || []);
        
        if (!container) return;
        
        // Filter out numeric-only "states" or invalid data
        const cleanRecs = recs.filter(rec => {
            const isNumeric = /^\d+$/.test(rec.id) || /^\d+$/.test(rec.region);
            return !isNumeric; 
        });

        if (!cleanRecs || cleanRecs.length === 0) {
            container.innerHTML = '<div style="grid-column: span 12; text-align:center; padding:40px;">No active recommendations.</div>';
            return;
        }

        container.innerHTML = cleanRecs.map(rec => {
            const priorityColors = {
                'Critical': 'var(--color-alert)',
                'High': 'var(--gov-saffron)',
                'Medium': 'var(--gov-blue)',
                'Low': 'var(--color-success)'
            };
            const pColor = priorityColors[rec.priority] || priorityColors['Medium'];
            
            // Check if plan is already executed
            const isExecuted = sessionStorage.getItem('executed_plan_' + rec.id) === 'true';
            
            const btnAttr = isExecuted 
                ? 'disabled style="width:100%; font-size:0.8rem; background:var(--color-success); cursor:default;"'
                : 'style="width:100%; font-size:0.8rem;" onclick="RecommendationEngine.generatePlan(\'' + rec.id + '\', \'' + rec.title.replace(/'/g, "\\'") + '\')"';
            
            const btnContent = isExecuted
                ? '<i class="fas fa-check-circle"></i> &nbsp; Plan Active'
                : '<i class="fas fa-magic"></i> &nbsp; Create Execution Plan';

            return `
                <div class="stat-card" style="grid-column: span 4; border-top: 4px solid ${pColor}; display:flex; flex-direction:column; justify-content:space-between;">
                    <div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                            <span style="background:${pColor}; color:white; padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:700; text-transform:uppercase;">${rec.priority}</span>
                            <span style="font-size:0.75rem; color:var(--text-secondary);">${rec.id}</span>
                        </div>
                        <h4 style="font-size:1rem; margin-bottom:8px; line-height:1.4;">${rec.title}</h4>
                        <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:15px;">${rec.finding}</p>
                    </div>
                    
                    <div style="background:var(--bg-light); padding:10px; border-radius:4px; margin-top:10px;">
                        <div style="font-size:0.75rem; font-weight:700; color:var(--gov-blue); margin-bottom:4px;">RECOMMENDED ACTION:</div>
                        <div style="font-size:0.85rem;">${rec.recommendation}</div>
                    </div>

                    <div style="display:flex; gap:10px; margin-top:15px;">
                        <button class="btn-tool-blue" ${btnAttr}>
                            ${btnContent}
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    },

    generatePlan(id, title) {
        // Redirect to dedicated Execution Plan Page
        // This is a government-grade formal document process
        const encodedTitle = encodeURIComponent(title);
        window.location.href = `/execution-plan?id=${id}&title=${encodedTitle}`;
    },


    getPriorityColor(p) {
        if (p === 'Critical') return '#DC3545';
        if (p === 'High') return '#FF9933';
        return '#0F4D92';
    }
};

window.RecommendationEngine = RecommendationEngine;
