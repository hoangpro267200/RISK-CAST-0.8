/**
 * ========================================================================
 * RISKCAST v20 - Pill Group Manager
 * ========================================================================
 * Manages pill group selections (excluding priority which is handled separately)
 * 
 * @class PillGroupManager
 */
export class PillGroupManager {
    /**
     * @param {Object} callbacks - Callback functions (onFormDataChange)
     */
    constructor(callbacks = {}) {
        this.callbacks = callbacks;
    }
    
    /**
     * Initialize pill groups
     */
    initPillGroups() {
        const pillGroups = document.querySelectorAll('.rc-pill-group');
        
        pillGroups.forEach(group => {
            const pills = group.querySelectorAll('.rc-pill');
            const fieldName = group.getAttribute('data-field');
            
            // Skip priority field (handled separately)
            if (fieldName === 'priority') return;
            
            pills.forEach(pill => {
                pill.addEventListener('click', () => {
                    const value = pill.getAttribute('data-value');
                    
                    pills.forEach(p => p.classList.remove('active'));
                    pill.classList.add('active');
                    
                    if (this.callbacks.onPillSelect) {
                        this.callbacks.onPillSelect(fieldName, value);
                    }
                    
                    console.log(`Pill selected: ${fieldName} = ${value}`);
                    
                    if (this.callbacks.onFormDataChange) {
                        this.callbacks.onFormDataChange();
                    }
                });
            });
        });
        
        console.log('🔥 Pill groups initialized ✓');
    }
}



