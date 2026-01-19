/**
 * RISKCAST v19 Page Initialization
 * Theme management, scroll navigation, intersection observer, neon particles
 */


// Global state

let aiPanel = null;

let particleCanvas = null;

let particleContext = null;

let particles = [];

let animationFrameId = null;



/**
 * Initialize page on DOMContentLoaded
 */

document.addEventListener('DOMContentLoaded', () => {

    // Prevent double initialization

    if (window.__RC_V19_INIT_DONE__) {

        console.warn('⚠️ RISKCAST v19 already initialized, skipping...');

        return;

    }

    window.__RC_V19_INIT_DONE__ = true;

    

    console.log('🔥 RISKCAST v19 — Starting initialization...');

    

    try {

        // 1. Check if LOGISTICS_DATA is loaded

        if (typeof LOGISTICS_DATA !== 'undefined') {

            console.log('🔥 LOGISTICS_DATA loaded ✓');

        } else {

            console.error('❌ LOGISTICS_DATA not loaded');

        }

        

        // 2. Check if CONTAINER_TYPES is loaded

        if (typeof CONTAINER_TYPES_BY_MODE !== 'undefined') {

            console.log('🔥 CONTAINER_TYPES_BY_MODE loaded ✓');

        } else {

            console.error('❌ CONTAINER_TYPES_BY_MODE not loaded');

        }

        

        // 3. Initialize theme first

        initTheme();

        initThemeToggle();

        console.log('🔥 Theme initialized ✓');

        

        // 4. Initialize controller (MUST come before AI panel)

        if (typeof RiskcastInputController !== 'undefined') {

            if (!window.rcController) {

                console.log('🔥 Creating RiskcastInputController...');

                window.rcController = new RiskcastInputController();

                window.rcController.init();

                console.log('🔥 Controller initialized ✓');

            } else {

                console.log('🔥 Controller already exists ✓');

            }

        } else {

            console.error('❌ RiskcastInputController class not loaded');

        }

        

        // 5. Initialize AI Panel

        initAiPanel();

        

        // 6. Initialize other features

        initScrollNavigation();

        console.log('🔥 Scroll navigation initialized ✓');

        

        initIntersectionObserver();

        console.log('🔥 Intersection observer initialized ✓');

        

        initNeonParticles();

        console.log('🔥 Neon particles initialized ✓');

        

        initFormHoverGlow();

        console.log('🔥 Form hover glow initialized ✓');

        

        // 7. Initialize Lucide icons after all content is loaded

        if (typeof lucide !== 'undefined') {

            lucide.createIcons();

            console.log('🔥 Lucide icons initialized ✓');

        }

        

        console.log('🔥 ========================================');

        console.log('🔥 RISKCAST v19 — ALL SYSTEMS READY ✓');

        console.log('🔥 ========================================');

        

    } catch (err) {

        console.error('❌ Init error (v19):', err);

        console.error('Stack trace:', err.stack);

    }

});



/**
 * Initialize theme based on user preference
 */

function initTheme() {

    const savedTheme = localStorage.getItem('rc-theme');

    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    

    let theme = savedTheme || (prefersDark ? 'dark' : 'light');

    

    document.documentElement.classList.remove('rc-theme-dark', 'rc-theme-light');

    document.documentElement.classList.add(`rc-theme-${theme}`);

}



/**
 * Initialize theme toggle button
 */

function initThemeToggle() {

    const toggleBtn = document.getElementById('rc-theme-toggle');

    

    if (toggleBtn) {

        toggleBtn.addEventListener('click', () => {

            const html = document.documentElement;

            const isDark = html.classList.contains('rc-theme-dark');

            

            // Toggle theme

            html.classList.remove('rc-theme-dark', 'rc-theme-light');

            html.classList.add(isDark ? 'rc-theme-light' : 'rc-theme-dark');

            

            // Save preference

            localStorage.setItem('rc-theme', isDark ? 'light' : 'dark');

            

            // Reinit icons

            if (typeof lucide !== 'undefined') {

                lucide.createIcons();

            }

        });

    }

}



/**
 * Initialize RiskcastInputController (LEGACY - kept for backward compatibility)
 */

function initController() {

    // Controller is now initialized in DOMContentLoaded

    // This function is kept for backward compatibility

    if (window.rcController) {

        console.log('✅ Controller already initialized');

        return window.rcController;

    }

    

    if (typeof RiskcastInputController === 'undefined') {

        console.error('❌ RiskcastInputController not loaded');

        return null;

    }

    

    const controller = new RiskcastInputController();

    controller.init();

    window.rcController = controller;

    

    return controller;

}



/**
 * Initialize AI Assist Panel
 */

function initAiPanel() {

    // Gracefully handle missing AiAssistPanel (optional dependency)

    if (typeof AiAssistPanel === 'undefined') {

        console.log('ℹ️ AiAssistPanel not loaded - AI Panel feature disabled');

        return;

    }

    

    // Check if controller exists

    if (!window.rcController) {

        console.warn('⚠️ Controller must be initialized before AI Panel');

        return;

    }

    

    if (aiPanel) {

        console.warn('⚠️ AI Panel already initialized');

        return;

    }

    

    try {

        aiPanel = new AiAssistPanel(window.rcController);

        aiPanel.init();

        

        // Make globally accessible

        window.aiPanel = aiPanel;

        console.log('🔥 AI Panel initialized ✓');

    } catch (err) {

        console.error('❌ Error initializing AI Panel:', err);

        console.error('Stack trace:', err.stack);

    }

}



/**
 * Initialize scroll navigation
 */

function initScrollNavigation() {

    const navItems = document.querySelectorAll('.rc-nav-item');

    

    navItems.forEach(item => {

        item.addEventListener('click', (e) => {

            e.preventDefault();

            

            const target = item.getAttribute('href');

            const targetSection = document.querySelector(target);

            

            if (targetSection) {

                // Smooth scroll to section

                const headerHeight = 70;

                const targetPosition = targetSection.offsetTop - headerHeight - 20;

                

                window.scrollTo({

                    top: targetPosition,

                    behavior: 'smooth'

                });

                

                // Update active state

                navItems.forEach(nav => nav.classList.remove('active'));

                item.classList.add('active');

            }

        });

    });

}



/**
 * Initialize Intersection Observer for scroll spy
 */

function initIntersectionObserver() {

    const sections = document.querySelectorAll('.rc-section');

    const navItems = document.querySelectorAll('.rc-nav-item');

    

    if (sections.length === 0 || navItems.length === 0) return;

    

    const observerOptions = {

        root: null,

        rootMargin: '-100px 0px -66%',

        threshold: 0

    };

    

    const observer = new IntersectionObserver((entries) => {

        entries.forEach(entry => {

            if (entry.isIntersecting) {

                const sectionId = entry.target.getAttribute('data-section-id');

                

                if (!sectionId) return;

                

                // Update active nav item

                navItems.forEach(nav => {

                    nav.classList.remove('active');

                    if (nav.getAttribute('data-nav-target') === sectionId) {

                        nav.classList.add('active');

                    }

                });

            }

        });

    }, observerOptions);

    

    sections.forEach(section => observer.observe(section));

}



/**
 * Initialize neon particle background
 */

function initNeonParticles() {

    particleCanvas = document.getElementById('rc-neon-canvas');

    

    if (!particleCanvas) return;

    

    particleContext = particleCanvas.getContext('2d');

    

    // Set canvas size

    resizeCanvas();

    window.addEventListener('resize', debounce(resizeCanvas, 250));

    

    // Create particles

    createParticles();

    

    // Start animation

    animateParticles();

}



/**
 * Resize canvas to window size
 */

function resizeCanvas() {

    if (!particleCanvas) return;

    

    particleCanvas.width = window.innerWidth;

    particleCanvas.height = window.innerHeight;

    

    // Recreate particles on resize

    if (particles.length > 0) {

        createParticles();

    }

}



/**
 * Create particle objects
 */

function createParticles() {

    if (!particleCanvas) return;

    

    const particleCount = Math.min(50, Math.floor(window.innerWidth / 30));

    particles = [];

    

    for (let i = 0; i < particleCount; i++) {

        particles.push({

            x: Math.random() * particleCanvas.width,

            y: Math.random() * particleCanvas.height,

            vx: (Math.random() - 0.5) * 0.3,

            vy: (Math.random() - 0.5) * 0.3,

            radius: Math.random() * 2 + 1,

            opacity: Math.random() * 0.3 + 0.1,

            pulseSpeed: Math.random() * 0.02 + 0.01,

            pulsePhase: Math.random() * Math.PI * 2

        });

    }

}



/**
 * Animate particles
 */

function animateParticles() {

    if (!particleContext || !particleCanvas) return;

    

    // Clear canvas

    particleContext.clearRect(0, 0, particleCanvas.width, particleCanvas.height);

    

    // Get theme colors

    const isDark = document.documentElement.classList.contains('rc-theme-dark');

    const primaryColor = isDark ? 'rgba(0, 255, 204' : 'rgba(0, 200, 180';

    const secondaryColor = isDark ? 'rgba(0, 212, 255' : 'rgba(0, 180, 220';

    

    particles.forEach((particle, index) => {

        // Update position

        particle.x += particle.vx;

        particle.y += particle.vy;

        

        // Bounce off edges

        if (particle.x < 0 || particle.x > particleCanvas.width) {

            particle.vx *= -1;

        }

        if (particle.y < 0 || particle.y > particleCanvas.height) {

            particle.vy *= -1;

        }

        

        // Keep in bounds

        particle.x = Math.max(0, Math.min(particleCanvas.width, particle.x));

        particle.y = Math.max(0, Math.min(particleCanvas.height, particle.y));

        

        // Pulse opacity

        particle.pulsePhase += particle.pulseSpeed;

        const pulseOpacity = particle.opacity * (0.7 + 0.3 * Math.sin(particle.pulsePhase));

        

        // Draw particle

        const color = index % 2 === 0 ? primaryColor : secondaryColor;

        particleContext.beginPath();

        particleContext.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);

        particleContext.fillStyle = `${color}, ${pulseOpacity})`;

        particleContext.fill();

        

        // Draw glow

        const gradient = particleContext.createRadialGradient(

            particle.x, particle.y, 0,

            particle.x, particle.y, particle.radius * 3

        );

        gradient.addColorStop(0, `${color}, ${pulseOpacity * 0.8})`);

        gradient.addColorStop(1, `${color}, 0)`);

        

        particleContext.beginPath();

        particleContext.arc(particle.x, particle.y, particle.radius * 3, 0, Math.PI * 2);

        particleContext.fillStyle = gradient;

        particleContext.fill();

    });

    

    // Draw connections between nearby particles

    particleContext.strokeStyle = isDark 

        ? 'rgba(0, 255, 204, 0.1)' 

        : 'rgba(0, 200, 180, 0.1)';

    particleContext.lineWidth = 0.5;

    

    for (let i = 0; i < particles.length; i++) {

        for (let j = i + 1; j < particles.length; j++) {

            const dx = particles[i].x - particles[j].x;

            const dy = particles[i].y - particles[j].y;

            const distance = Math.sqrt(dx * dx + dy * dy);

            

            if (distance < 150) {

                const opacity = (1 - distance / 150) * 0.15;

                particleContext.strokeStyle = isDark

                    ? `rgba(0, 255, 204, ${opacity})`

                    : `rgba(0, 200, 180, ${opacity})`;

                

                particleContext.beginPath();

                particleContext.moveTo(particles[i].x, particles[i].y);

                particleContext.lineTo(particles[j].x, particles[j].y);

                particleContext.stroke();

            }

        }

    }

    

    // Continue animation

    animationFrameId = requestAnimationFrame(animateParticles);

}



/**
 * Clean up on page unload
 */

window.addEventListener('beforeunload', () => {

    if (animationFrameId) {

        cancelAnimationFrame(animationFrameId);

    }

});



/**
 * Utility: Debounce function
 */

function debounce(func, wait) {

    let timeout;

    return function executedFunction(...args) {

        const later = () => {

            clearTimeout(timeout);

            func(...args);

        };

        clearTimeout(timeout);

        timeout = setTimeout(later, wait);

    };

}



/**
 * Performance: Pause particles when page hidden
 */

document.addEventListener('visibilitychange', () => {

    if (document.hidden) {

        if (animationFrameId) {

            cancelAnimationFrame(animationFrameId);

            animationFrameId = null;

        }

    } else {

        if (!animationFrameId && particleCanvas) {

            animateParticles();

        }

    }

});



/**
 * Initialize form hover glow effect
 */
function initFormHoverGlow() {
    const panel = document.querySelector(".rc-form-panel");
    if (!panel) return;

    panel.addEventListener("pointerenter", () => {
        panel.classList.add("rc-form-hovering");
    });

    panel.addEventListener("pointerleave", () => {
        panel.classList.remove("rc-form-hovering");
        panel.style.setProperty("--pointer-x", "-100px");
        panel.style.setProperty("--pointer-y", "-100px");
    });

    panel.addEventListener("pointermove", (e) => {
        const rect = panel.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        panel.style.setProperty("--pointer-x", `${x}px`);
        panel.style.setProperty("--pointer-y", `${y}px`);
    });
}

/**
 * Accessibility: Reduce motion for users who prefer it
 */

if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {

    // Disable particles

    if (particleCanvas) {

        particleCanvas.style.display = 'none';

    }

    

    // Disable animations

    document.documentElement.style.setProperty('--rc-transition-fast', '0s');

    document.documentElement.style.setProperty('--rc-transition-base', '0s');

    document.documentElement.style.setProperty('--rc-transition-slow', '0s');

}

