/* ==========================================================================
   SUMMARY_V400 - RISK ROW
   Risk module toggles
   ========================================================================== */

const V400RiskRow = (() => {
    
    /**
     * Get SVG icon for risk module
     */
    function getIconSVG(key) {
        const icons = {
            'esg': '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="url(#riskIconGradient1)" opacity="0.6"/><path d="M12 4L9.91 8.26L5 8.77L8.5 12L7.41 16.5L12 14.27L16.59 16.5L15.5 12L19 8.77L14.09 8.26L12 4Z" fill="url(#riskIconGradient1)"/><defs><linearGradient id="riskIconGradient1" x1="2" y1="2" x2="22" y2="22"><stop stop-color="#35E0FF" stop-opacity="0.8"/><stop offset="1" stop-color="#7B4DFF" stop-opacity="0.8"/></linearGradient></defs></svg>',
            'weather': '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2Z" fill="url(#riskIconGradient2)" opacity="0.5"/><path d="M12 8C14.21 8 16 9.79 16 12C16 14.21 14.21 16 12 16C9.79 16 8 14.21 8 12C8 9.79 9.79 8 12 8ZM12 10C10.9 10 10 10.9 10 12C10 13.1 10.9 14 12 14C13.1 14 14 13.1 14 12C14 10.9 13.1 10 12 10ZM9 12C8.45 12 8 12.45 8 13C8 13.55 8.45 14 9 14C9.55 14 10 13.55 10 13C10 12.45 9.55 12 9 12ZM15 12C14.45 12 14 12.45 14 13C14 13.55 14.45 14 15 14C15.55 14 16 13.55 16 13C16 12.45 15.55 12 15 12Z" fill="url(#riskIconGradient2)"/><defs><linearGradient id="riskIconGradient2" x1="2" y1="2" x2="22" y2="22"><stop stop-color="#35E0FF" stop-opacity="0.8"/><stop offset="1" stop-color="#7B4DFF" stop-opacity="0.8"/></linearGradient></defs></svg>',
            'congestion': '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2Z" fill="url(#riskIconGradient3)" opacity="0.5"/><path d="M12 6L13.09 8.26L15.5 8.77L13.91 10.73L14.18 13.27L12 12.27L9.82 13.27L10.09 10.73L8.5 8.77L10.91 8.26L12 6ZM17 11L17.5 12.5L19 13L17.5 13.5L17 15L16.5 13.5L15 13L16.5 12.5L17 11ZM7 11L7.5 12.5L9 13L7.5 13.5L7 15L6.5 13.5L5 13L6.5 12.5L7 11Z" fill="url(#riskIconGradient3)"/><defs><linearGradient id="riskIconGradient3" x1="2" y1="2" x2="22" y2="22"><stop stop-color="#35E0FF" stop-opacity="0.8"/><stop offset="1" stop-color="#7B4DFF" stop-opacity="0.8"/></linearGradient></defs></svg>',
            'carrier_perf': '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 18H20V20H4V18Z" fill="url(#riskIconGradient4)" opacity="0.6"/><path d="M2 6L12 2L22 6V18H2V6ZM4 8V16H20V8L12 5L4 8ZM8 10H16V14H8V10Z" fill="url(#riskIconGradient4)"/><defs><linearGradient id="riskIconGradient4" x1="2" y1="2" x2="22" y2="20"><stop stop-color="#35E0FF" stop-opacity="0.8"/><stop offset="1" stop-color="#7B4DFF" stop-opacity="0.8"/></linearGradient></defs></svg>',
            'market': '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 21H21V23H3V21Z" fill="url(#riskIconGradient5)" opacity="0.6"/><path d="M3 3V5H5V3H3ZM7 3V5H9V3H7ZM11 3V5H13V3H11ZM15 3V5H17V3H15ZM19 3V5H21V3H19ZM3 7V9H5V7H3ZM3 11V13H5V11H3ZM3 15V17H5V15H3ZM3 19V21H5V19H3ZM21 7V9H19V7H21ZM21 11V13H19V11H21ZM21 15V17H19V15H21Z" fill="url(#riskIconGradient5)"/><defs><linearGradient id="riskIconGradient5" x1="3" y1="3" x2="21" y2="21"><stop stop-color="#35E0FF" stop-opacity="0.8"/><stop offset="1" stop-color="#7B4DFF" stop-opacity="0.8"/></linearGradient></defs></svg>',
            'insurance': '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L4 5V11C4 16.55 7.16 21.74 12 23C16.84 21.74 20 16.55 20 11V5L12 2Z" fill="url(#riskIconGradient6)" opacity="0.5"/><path d="M12 4L18 6.5V11C18 15.26 15.39 19.17 12 20.43C8.61 19.17 6 15.26 6 11V6.5L12 4ZM12 7L9 8.5V11C9 13.76 10.8 16.14 13.5 17.09L12 15.5L10.5 14L12 12.5L13.5 14L12 15.5L14.5 17.09C17.2 16.14 19 13.76 19 11V8.5L12 7Z" fill="url(#riskIconGradient6)"/><defs><linearGradient id="riskIconGradient6" x1="4" y1="2" x2="20" y2="23"><stop stop-color="#35E0FF" stop-opacity="0.8"/><stop offset="1" stop-color="#7B4DFF" stop-opacity="0.8"/></linearGradient></defs></svg>'
        };
        return icons[key] || '';
    }
    
    const RISK_MODULES = [
        {
            key: 'esg',
            label: 'ESG',
            icon: getIconSVG('esg')
        },
        {
            key: 'weather',
            label: 'Weather',
            icon: getIconSVG('weather')
        },
        {
            key: 'congestion',
            label: 'Port Congestion',
            icon: getIconSVG('congestion')
        },
        {
            key: 'carrier_perf',
            label: 'Carrier Performance',
            icon: getIconSVG('carrier_perf')
        },
        {
            key: 'market',
            label: 'Market Scanner',
            icon: getIconSVG('market')
        },
        {
            key: 'insurance',
            label: 'Insurance',
            icon: getIconSVG('insurance')
        }
    ];
    
    /**
     * Render risk module row
     */
    function render(state, onToggle) {
        const container = document.getElementById('riskRow');
        if (!container) return;
        
        container.innerHTML = RISK_MODULES.map(module => {
            const isOn = state.riskModules[module.key] || false;
            
            return `
                <div class="risk-card" data-module="${module.key}">
                    <div class="risk-card__icon">${module.icon}</div>
                    <div class="risk-card__label">${module.label}</div>
                    <div class="risk-card__toggle ${isOn ? 'risk-card__toggle--on' : ''}" 
                         data-module="${module.key}">
                        <div class="risk-card__toggle-knob"></div>
                    </div>
                    <div class="risk-card__status ${isOn ? 'risk-card__status--on' : ''}">
                        ${isOn ? 'Bật' : 'Tắt'}
                    </div>
                </div>
            `;
        }).join('');
        
        // Attach toggle handlers
        attachToggleHandlers(onToggle);
    }
    
    /**
     * Attach toggle click handlers
     */
    function attachToggleHandlers(onToggle) {
        const toggles = document.querySelectorAll('.risk-card__toggle');
        
        toggles.forEach(toggle => {
            toggle.addEventListener('click', () => {
                const moduleKey = toggle.dataset.module;
                const card = toggle.closest('.risk-card');
                const statusEl = card.querySelector('.risk-card__status');
                
                // Toggle state
                const isCurrentlyOn = toggle.classList.contains('risk-card__toggle--on');
                const newState = !isCurrentlyOn;
                
                // Update UI
                if (newState) {
                    toggle.classList.add('risk-card__toggle--on');
                    statusEl.classList.add('risk-card__status--on');
                    statusEl.textContent = 'Bật';
                } else {
                    toggle.classList.remove('risk-card__toggle--on');
                    statusEl.classList.remove('risk-card__status--on');
                    statusEl.textContent = 'Tắt';
                }
                
                // Callback
                if (onToggle) {
                    onToggle(moduleKey, newState);
                }
            });
        });
    }
    
    // Public API
    return {
        render
    };
})();


