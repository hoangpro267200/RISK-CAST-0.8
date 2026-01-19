/**
 * ========================================================================
 * RISKCAST v20 - Sidebar Manager
 * ========================================================================
 * Manages sidebar collapse/expand functionality
 * 
 * @class SidebarManager
 */
export class SidebarManager {
    constructor() {
        this.sidebar = null;
        this.sidebarToggle = null;
    }
    
    /**
     * Initialize sidebar manager
     */
    init() {
        this.sidebar = document.getElementById('rc-sidebar');
        this.sidebarToggle = document.getElementById('rc-sidebar-toggle');
        
        if (this.sidebarToggle) {
            this.sidebarToggle.addEventListener('click', () => {
                if (this.sidebar) {
                    this.sidebar.classList.toggle('open');
                }
            });
        }
        
        // Close sidebar when clicking outside (mobile)
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 1024 && this.sidebar) {
                if (!this.sidebar.contains(e.target) && 
                    this.sidebarToggle && 
                    !this.sidebarToggle.contains(e.target)) {
                    this.sidebar.classList.remove('open');
                }
            }
        });
    }
}



