/**
 * ALRIS COMMAND CENTER - Interaction Manager
 * Handles filters, drill-downs, and scope events
 */

const InteractionManager = {
    scope: {
        state: 'National',
        district: null,
        period: 'Monthly'
    },

    init() {
        this.bindGlobalFilters();
        this.initMapEvents();
    },

    bindGlobalFilters() {
        document.getElementById('stateSelect')?.addEventListener('change', (e) => {
            this.scope.state = e.target.value;
            this.updateDashboard();
        });

        document.querySelectorAll('.time-toggle').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.time-toggle').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.scope.period = btn.dataset.period;
                this.updateDashboard();
            });
        });
    },

    initMapEvents() {
        // Placeholder for Map interactivity
        window.addEventListener('map:stateClick', (e) => {
            this.scope.state = e.detail.state;
            this.updateDashboard();
        });
    },

    updateDashboard() {
        console.log('[ALRIS] Scope Scope Updated:', this.scope);
        // Dispatch event for other modules
        const event = new CustomEvent('alris:scopeChange', { detail: this.scope });
        window.dispatchEvent(event);
        
        // Update breadcrumb
        const breadcrumb = document.getElementById('breadcrumb');
        if (breadcrumb) {
            breadcrumb.innerHTML = `<span>India</span> <span>${this.scope.state}</span> ${this.scope.district ? `<span>${this.scope.district}</span>` : ''}`;
        }
    }
};

window.InteractionManager = InteractionManager;
