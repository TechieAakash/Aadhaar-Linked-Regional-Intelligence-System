/**
 * ALRIS - Filtering & Scope Management
 * Handles hierarchical drill-down and temporal slices
 */

const Filters = {
    current: {
        state: 'all',
        period: 'all',
        ageGroup: 'all',
        updateType: 'all'
    },

    /**
     * Populate filter dropdowns based on loaded data
     */
    init(data) {
        this.populateStates(data.stateData);
        this.bindEvents();
    },

    populateStates(stateData) {
        const select = document.getElementById('stateFilter');
        if (!select || !stateData) return;

        // Clear existing except 'all'
        select.innerHTML = '<option value="all">All India (National)</option>';

        const states = [...new Set(stateData.map(d => d.state))].sort();
        states.forEach(state => {
            const opt = document.createElement('option');
            opt.value = state;
            opt.textContent = state;
            select.appendChild(opt);
        });
    },

    bindEvents() {
        // State Filter
        document.getElementById('stateFilter')?.addEventListener('change', (e) => {
            this.current.state = e.target.value;
        });

        // Period Filter
        document.querySelectorAll('input[name="period"]').forEach(input => {
            input.addEventListener('change', (e) => {
                this.current.period = e.target.value;
            });
        });

        // Apply Button
        document.getElementById('applyFilters')?.addEventListener('click', () => {
            this.triggerUpdate();
        });

        // Reset Button
        document.getElementById('resetFilters')?.addEventListener('click', () => {
            this.reset();
        });
    },

    triggerUpdate() {
        const btn = document.getElementById('applyFilters');
        if (btn) {
            btn.innerHTML = '<span class="status-dot"></span> Syncing...';
            btn.disabled = true;
        }

        // Emit custom event for app controller to listen
        const event = new CustomEvent('alris:filterUpdate', { detail: this.current });
        window.dispatchEvent(event);

        setTimeout(() => {
            if (btn) {
                btn.innerHTML = 'Apply Filters';
                btn.disabled = false;
            }
        }, 500);
    },

    reset() {
        this.current = { state: 'all', period: 'all', ageGroup: 'all', updateType: 'all' };
        const stateSelect = document.getElementById('stateFilter');
        if (stateSelect) stateSelect.value = 'all';
        this.triggerUpdate();
    }
};

window.Filters = Filters;
