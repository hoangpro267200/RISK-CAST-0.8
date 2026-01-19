/**
 * ========================================================================
 * RISKCAST v20 - Form Panel Glow Effect
 * ========================================================================
 * Luxurious glow effect on form panels
 * 
 * @class FormPanelGlow
 */
export class FormPanelGlow {
    constructor() {
        this.panels = [];
    }
    
    /**
     * Initialize glow effect on all form panels
     */
    init() {
        this.panels = document.querySelectorAll('.rc-form-panel');
        
        this.panels.forEach(panel => {
            let isHovering = false;
            
            panel.addEventListener('pointerenter', () => {
                isHovering = true;
                panel.classList.add('hovering');
            });
            
            panel.addEventListener('pointerleave', () => {
                isHovering = false;
                panel.classList.remove('hovering');
                panel.style.setProperty('--pointer-x', '-500px');
                panel.style.setProperty('--pointer-y', '-500px');
            });
            
            panel.addEventListener('pointermove', (e) => {
                if (!isHovering) return;
                
                const rect = panel.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                panel.style.setProperty('--pointer-x', `${x}px`);
                panel.style.setProperty('--pointer-y', `${y}px`);
            });
        });
        
        console.log('🔥 Panel glow effect initialized ✓');
    }
}



