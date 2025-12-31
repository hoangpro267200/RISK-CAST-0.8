/**
 * ========================================================================
 * RISKCAST v20 - Theme Manager
 * ========================================================================
 * Manages dark/light theme switching
 * 
 * @class ThemeManager
 */
export class ThemeManager {
    constructor() {
        this.html = document.documentElement;
        this.themeToggle = null;
    }
    
    /**
     * Initialize theme manager
     */
    init() {
        this.themeToggle = document.getElementById('rc-theme-toggle');
        
        const savedTheme = localStorage.getItem('rc-theme') || 'dark';
        this.html.classList.remove('rc-theme-dark', 'rc-theme-light');
        this.html.classList.add(`rc-theme-${savedTheme}`);
        
        if (this.themeToggle) {
            this.themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
    }
    
    /**
     * Toggle between dark and light theme
     */
    toggleTheme() {
        const isDark = this.html.classList.contains('rc-theme-dark');
        const newTheme = isDark ? 'light' : 'dark';
        
        this.html.classList.remove('rc-theme-dark', 'rc-theme-light');
        this.html.classList.add(`rc-theme-${newTheme}`);
        
        localStorage.setItem('rc-theme', newTheme);
        
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }
}



