/**
 * ========================================================================
 * RISKCAST v20 - Toast Manager
 * ========================================================================
 * Manages toast notifications
 * 
 * @class ToastManager
 */
export class ToastManager {
    constructor() {
        this.container = null;
    }
    
    /**
     * Show toast notification
     * @param {string} message - Toast message
     * @param {string} type - Toast type (success, error, info)
     */
    showToast(message, type = 'info') {
        if (!this.container) {
            this.container = document.getElementById('rc-toast-container');
        }
        
        if (!this.container) return;
        
        const toast = document.createElement('div');
        toast.className = 'rc-toast';
        
        const iconName = {
            'success': 'check-circle',
            'error': 'alert-circle',
            'info': 'info'
        }[type] || 'info';
        
        toast.innerHTML = `
            <i data-lucide="${iconName}"></i>
            <span>${message}</span>
        `;
        
        this.container.appendChild(toast);
        
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100px)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}



