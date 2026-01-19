/**
 * RISKCAST v3.0 Input Page Layout Controller
 * Handles sidebar toggle, ghost spacing, and smooth transitions
 */

class InputLayoutV3 {
    constructor() {
        this.sidebar = null;
        this.sidebarToggle = null;
        this.isCollapsed = false;
        this.init();
    }
    
    init() {
        this.sidebar = document.getElementById('input-sidebar');
        this.sidebarToggle = document.getElementById('sidebar-toggle');
        
        if (!this.sidebar || !this.sidebarToggle) {
            console.warn('[LayoutV3] Sidebar elements not found');
            return;
        }
        
        // Load saved state
        const savedState = localStorage.getItem('input-sidebar-collapsed');
        if (savedState === 'true') {
            this.collapse();
        }
        
        // Bind events
        this.sidebarToggle.addEventListener('click', () => this.toggle());
        
        // Initialize sidebar navigation
        this.initSidebarNavigation();
        
        // Set initial active item
        this.setInitialActiveItem();
        
        // Mobile menu toggle
        if (window.innerWidth <= 1024) {
            this.sidebar.classList.add('mobile');
        }
        
        window.addEventListener('resize', () => this.handleResize());
    }
    
    setInitialActiveItem() {
        const navItems = this.sidebar.querySelectorAll('.sidebar-nav-item');
        if (navItems.length > 0) {
            // Set first item as active by default
            this.updateActiveNavItem(navItems[0]);
        }
    }
    
    initSidebarNavigation() {
        const navItems = this.sidebar.querySelectorAll('.sidebar-nav-item');
        
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                
                const sectionId = item.getAttribute('href') || item.getAttribute('data-section');
                if (!sectionId) return;
                
                // Remove # if present
                const targetId = sectionId.startsWith('#') ? sectionId.substring(1) : sectionId;
                const targetSection = document.getElementById(targetId);
                
                if (targetSection) {
                    // Update active state
                    this.updateActiveNavItem(item);
                    
                    // Smooth scroll to section with proper offset
                    const headerOffset = 160; // Account for sticky header
                    const elementPosition = targetSection.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                    
                    targetSection.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start',
                        inline: 'nearest'
                    });
                    
                    // Fine-tune scroll position after animation
                    setTimeout(() => {
                        const finalPosition = targetSection.getBoundingClientRect().top + window.pageYOffset - headerOffset;
                        window.scrollTo({
                            top: finalPosition,
                            behavior: 'auto'
                        });
                    }, 100);
                    
                    // Close mobile sidebar if open
                    if (window.innerWidth <= 1024 && this.sidebar.classList.contains('open')) {
                        this.sidebar.classList.remove('open');
                    }
                } else {
                    console.warn(`[LayoutV3] Section not found: ${targetId}`);
                }
            });
        });
        
        // Update active item on scroll
        this.initScrollSpy();
    }
    
    updateActiveNavItem(activeItem) {
        const navItems = this.sidebar.querySelectorAll('.sidebar-nav-item');
        navItems.forEach(item => {
            item.classList.remove('active');
        });
        activeItem.classList.add('active');
    }
    
    initScrollSpy() {
        let ticking = false;
        
        const updateActiveSection = () => {
            const sections = document.querySelectorAll('.form-section[id]');
            const navItems = this.sidebar.querySelectorAll('.sidebar-nav-item');
            const scrollPosition = window.pageYOffset + 160; // Header offset
            
            let currentSection = null;
            
            sections.forEach(section => {
                const sectionTop = section.offsetTop;
                const sectionHeight = section.offsetHeight;
                
                if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                    currentSection = section.id;
                }
            });
            
            if (currentSection) {
                navItems.forEach(item => {
                    const href = item.getAttribute('href') || item.getAttribute('data-section');
                    const sectionId = href.startsWith('#') ? href.substring(1) : href;
                    
                    if (sectionId === currentSection) {
                        this.updateActiveNavItem(item);
                    }
                });
            }
            
            ticking = false;
        };
        
        window.addEventListener('scroll', () => {
            if (!ticking) {
                window.requestAnimationFrame(updateActiveSection);
                ticking = true;
            }
        });
    }
    
    toggle() {
        if (this.isCollapsed) {
            this.expand();
        } else {
            this.collapse();
        }
    }
    
    collapse() {
        if (!this.sidebar) return;
        
        this.sidebar.classList.add('collapsed');
        this.isCollapsed = true;
        localStorage.setItem('input-sidebar-collapsed', 'true');
    }
    
    expand() {
        if (!this.sidebar) return;
        
        this.sidebar.classList.remove('collapsed');
        this.isCollapsed = false;
        localStorage.setItem('input-sidebar-collapsed', 'false');
    }
    
    handleResize() {
        if (window.innerWidth <= 1024) {
            this.sidebar.classList.add('mobile');
            if (this.sidebar.classList.contains('open')) {
                // Close mobile menu on resize if needed
            }
        } else {
            this.sidebar.classList.remove('mobile');
            this.sidebar.classList.remove('open');
        }
    }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new InputLayoutV3();
    });
} else {
    new InputLayoutV3();
}

export default InputLayoutV3;

