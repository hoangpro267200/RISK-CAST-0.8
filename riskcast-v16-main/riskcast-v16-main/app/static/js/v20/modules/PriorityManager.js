/**
 * ========================================================================
 * RISKCAST v20 - Priority Manager
 * ========================================================================
 * Manages 4-mode priority system (Fastest, Balanced, Cheapest, Most Reliable)
 * 
 * @class PriorityManager
 */
export class PriorityManager {
    /**
     * @param {Object} stateManager - State manager instance
     * @param {Object} transportModule - Transport module instance
     * @param {Object} callbacks - Callback functions
     */
    constructor(stateManager, transportModule, callbacks = {}) {
        this.state = stateManager;
        this.transportModule = transportModule;
        this.callbacks = callbacks;
    }
    
    /**
     * Initialize priority manager
     */
    init() {
        this.bindPriorityPills();
        console.log('🔥 Priority manager initialized ✓ (4 modes: fastest, balanced, cheapest, reliable)');
    }
    
    /**
     * Bind priority pill group
     */
    bindPriorityPills() {
        const priorityGroup = document.querySelector('.rc-pill-group[data-field="priority"]');
        if (!priorityGroup) return;
        
        const pills = priorityGroup.querySelectorAll('.rc-pill');
        
        pills.forEach(pill => {
            pill.addEventListener('click', () => {
                const value = pill.getAttribute('data-value');
                
                pills.forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                
                this.state.setState('priority', value);
                
                console.log(`🔥 Priority selected: ${value} (4-mode system)`);
                
                // Reload service routes with new priority filter
                if (this.transportModule && this.transportModule.loadServiceRoutes) {
                    const tradeLane = this.state.getStateValue('tradeLane');
                    const mode = this.state.getStateValue('mode');
                    if (tradeLane && mode) {
                        this.transportModule.loadServiceRoutes();
                    }
                }
                
                if (this.callbacks.onFormDataChange) {
                    this.callbacks.onFormDataChange();
                }
            });
        });
    }
    
    /**
     * Calculate priority score for a route
     * @param {Object} route - Route object
     * @param {string} priority - Priority mode
     * @returns {number} Priority score
     */
    calculatePriorityScore(route, priority) {
        const transit = route.transit_days || 15;
        const cost = route.cost || 1000;
        const reliability = route.reliability || 80;
        
        // Normalize to 0-100 scale (higher is better)
        const speedScore = Math.max(0, 100 - transit * 2);
        const costScore = Math.max(0, 100 - (cost - 1000) / 10);
        const reliabilityScore = reliability;
        
        if (priority === 'balanced') {
            return (speedScore + costScore + reliabilityScore) / 3;
        }
        
        return reliabilityScore;
    }
}



