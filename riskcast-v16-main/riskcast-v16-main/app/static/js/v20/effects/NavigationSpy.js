/**
 * ========================================================================
 * RISKCAST v20 - Navigation Scroll Spy
 * ========================================================================
 * Scroll spy for navigation menu
 * 
 * @class NavigationSpy
 */
export class NavigationSpy {
    constructor() {
        this.navItems = [];
        this.sections = [];
        this.observer = null;
    }
    
    /**
     * Initialize navigation scroll spy
     */
    init() {
        this.navItems = document.querySelectorAll('.rc-nav-item');
        this.sections = document.querySelectorAll('.rc-form-panel');
        
        // Setup click handlers
        this.navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const sectionId = item.getAttribute('href');
                const section = document.querySelector(sectionId);
                
                if (section) {
                    const headerHeight = 70;
                    const offset = 100;
                    const targetPosition = section.offsetTop - headerHeight - offset;
                    
                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                    
                    this.navItems.forEach(nav => nav.classList.remove('active'));
                    item.classList.add('active');
                    
                    if (window.innerWidth <= 1024) {
                        const sidebar = document.getElementById('rc-sidebar');
                        if (sidebar) {
                            sidebar.classList.remove('open');
                        }
                    }
                }
            });
        });
        
        // Setup intersection observer for scroll spy
        const observerOptions = {
            root: null,
            rootMargin: '-100px 0px -50%',
            threshold: 0
        };
        
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const sectionId = entry.target.getAttribute('id');
                    this.navItems.forEach(item => {
                        item.classList.remove('active');
                        if (item.getAttribute('href') === `#${sectionId}`) {
                            item.classList.add('active');
                        }
                    });
                }
            });
        }, observerOptions);
        
        this.sections.forEach(section => this.observer.observe(section));
    }
}



