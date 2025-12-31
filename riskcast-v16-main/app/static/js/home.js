/* ============================================================================
   RISKCAST FUTUREOS V900 CINEMATIC — JAVASCRIPT
   All interactive behaviors, animations, and UX enhancements
   ============================================================================ */

   (function() {
    'use strict';
  
    // ============================================================================
    // UTILITY FUNCTIONS
    // ============================================================================
  
    /**
     * Smooth scroll to target element
     */
    function smoothScrollTo(target) {
      const el = document.querySelector(target);
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const offset = rect.top + window.scrollY - 104; // header (72px) + ticker (32px)
      window.scrollTo({ top: offset, behavior: 'smooth' });
    }
  
    /**
     * Debounce function for performance
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
  
    // ============================================================================
    // BOOT SEQUENCE
    // ============================================================================

    function initBootSequence() {
      const bootLayer = document.getElementById('rc-boot');
      const bar = document.getElementById('rc-boot-progress-bar');
      
      if (!bootLayer) {
        return;
      }

      // Fallback: Hide boot layer after max 5 seconds regardless
      const fallbackHide = setTimeout(() => {
        bootLayer.classList.add('rc-boot-hidden');
        bootLayer.style.display = 'none';
      }, 5000);

      if (!bar) {
        // If no progress bar, hide immediately
        setTimeout(() => {
          bootLayer.classList.add('rc-boot-hidden');
          bootLayer.style.display = 'none';
          clearTimeout(fallbackHide);
        }, 500);
        return;
      }

      // Start animation with small delay to ensure rendering
      setTimeout(() => {
        // Animate progress bar
        requestAnimationFrame(() => {
          bar.style.width = '100%';
        });

        // Hide boot layer after animation
        setTimeout(() => {
          bootLayer.classList.add('rc-boot-hidden');
          bootLayer.style.display = 'none';
          clearTimeout(fallbackHide);
        }, 2300);
      }, 100);
    }
  
    // ============================================================================
    // SCROLL REVEAL ANIMATIONS
    // ============================================================================
  
    function initScrollReveal() {
      const rcAnimObserver = new IntersectionObserver(
        (entries, observer) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add('is-visible');
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.2 }
      );
  
      document.querySelectorAll('.rc-anim').forEach((el) => {
        rcAnimObserver.observe(el);
      });
    }
  
    // ============================================================================
    // SMOOTH SCROLL NAVIGATION
    // ============================================================================
  
    function initSmoothScroll() {
      document.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-scroll]');
        if (!btn) return;
        
        const target = btn.getAttribute('data-scroll');
        if (target) {
          e.preventDefault();
          smoothScrollTo(target);
        }
      });
    }
  
    // ============================================================================
    // MAP NARRATIVE TIMELINE
    // ============================================================================
  
    function initMapNarrative() {
      const mapSection = document.getElementById('rc-map-section');
      if (!mapSection) return;
  
      const klang = document.getElementById('rc-port-klang');
      const klangLabel = document.getElementById('rc-port-klang-label');
      const sin = document.getElementById('rc-port-sin');
      const route = document.getElementById('rc-map-route');
      const ai = document.getElementById('rc-map-ai');
      let played = false;
  
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting && !played) {
              played = true;
  
              // Step 1: show Port Klang as risk (400ms delay)
              setTimeout(() => {
                if (klang) klang.classList.add('is-visible');
                if (klangLabel) klangLabel.classList.add('is-visible');
              }, 400);
  
              // Step 2: show Singapore + draw route (1400ms delay)
              setTimeout(() => {
                if (sin) sin.classList.add('is-visible');
                if (route) {
                  route.classList.add('is-visible');
                  route.style.width = 'calc(14vw + 80px)';
                }
              }, 1400);
  
              // Step 3: show AI bubble (2400ms delay)
              setTimeout(() => {
                if (ai) ai.classList.add('is-visible');
              }, 2400);
  
              observer.unobserve(mapSection);
            }
          });
        },
        { threshold: 0.45 }
      );
  
      observer.observe(mapSection);
    }
  
    // ============================================================================
    // INTERACTIVE SIMULATION (USER-CONTROLLED)
    // ============================================================================
  
    function initInteractiveSimulation() {
      const scenarioBtns = document.querySelectorAll('.rc-sim-scenario-btn');
      const responseContents = document.querySelectorAll('.rc-sim-response-content');
      
      if (scenarioBtns.length === 0) return;
  
      scenarioBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const scenario = btn.getAttribute('data-scenario');
          
          // Update button active states
          scenarioBtns.forEach(b => {
            b.classList.remove('active');
            b.setAttribute('aria-checked', 'false');
          });
          btn.classList.add('active');
          btn.setAttribute('aria-checked', 'true');
          
          // Update response content with smooth crossfade
          responseContents.forEach(content => {
            const contentScenario = content.getAttribute('data-response');
            if (contentScenario === scenario) {
              content.classList.add('active');
            } else {
              content.classList.remove('active');
            }
          });
        });
      });
  
      // Risk intensity slider feedback
      const slider = document.getElementById('risk-intensity');
      if (slider) {
        slider.addEventListener('input', debounce((e) => {
          const value = e.target.value;
          // Could add visual feedback here based on intensity
          console.log('Risk intensity:', value);
        }, 100));
      }
    }
  
    // ============================================================================
    // CASE STUDIES CAROUSEL
    // ============================================================================
  
    function initCarousel() {
      const track = document.getElementById('rc-carousel-track');
      const prevBtn = document.querySelector('.rc-carousel-prev');
      const nextBtn = document.querySelector('.rc-carousel-next');
      const dotsContainer = document.getElementById('rc-carousel-dots');
      
      if (!track || !prevBtn || !nextBtn) return;
  
      const cards = Array.from(track.querySelectorAll('.rc-carousel-card'));
      const cardWidth = cards[0]?.offsetWidth || 320;
      const gap = 24; // 1.5rem in pixels
      const cardsPerView = window.innerWidth >= 1024 ? 3 : (window.innerWidth >= 768 ? 2 : 1);
      
      let currentIndex = 0;
      const maxIndex = Math.max(0, cards.length - cardsPerView);
  
      // Create dots
      cards.forEach((_, index) => {
        if (index < cards.length - cardsPerView + 1) {
          const dot = document.createElement('button');
          dot.className = 'rc-carousel-dot';
          dot.setAttribute('aria-label', `Go to slide ${index + 1}`);
          if (index === 0) dot.classList.add('active');
          dot.addEventListener('click', () => goToSlide(index));
          dotsContainer.appendChild(dot);
        }
      });
  
      const dots = Array.from(dotsContainer.querySelectorAll('.rc-carousel-dot'));
  
      function updateCarousel() {
        const offset = -(currentIndex * (cardWidth + gap));
        track.style.transform = `translateX(${offset}px)`;
        
        // Update dots
        dots.forEach((dot, index) => {
          dot.classList.toggle('active', index === currentIndex);
        });
        
        // Update button states
        prevBtn.disabled = currentIndex === 0;
        nextBtn.disabled = currentIndex >= maxIndex;
      }
  
      function goToSlide(index) {
        currentIndex = Math.max(0, Math.min(index, maxIndex));
        updateCarousel();
      }
  
      prevBtn.addEventListener('click', () => {
        if (currentIndex > 0) {
          currentIndex--;
          updateCarousel();
        }
      });
  
      nextBtn.addEventListener('click', () => {
        if (currentIndex < maxIndex) {
          currentIndex++;
          updateCarousel();
        }
      });
  
      // Handle window resize
      let resizeTimeout;
      window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
          currentIndex = 0;
          updateCarousel();
        }, 200);
      });
  
      // Touch/swipe support for mobile
      let touchStartX = 0;
      let touchEndX = 0;
  
      track.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
      }, { passive: true });
  
      track.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
      }, { passive: true });
  
      function handleSwipe() {
        const swipeThreshold = 50;
        if (touchStartX - touchEndX > swipeThreshold && currentIndex < maxIndex) {
          // Swipe left - next
          currentIndex++;
          updateCarousel();
        } else if (touchEndX - touchStartX > swipeThreshold && currentIndex > 0) {
          // Swipe right - prev
          currentIndex--;
          updateCarousel();
        }
      }
  
      updateCarousel();
    }
  
    // ============================================================================
    // CHATBOT PANEL TOGGLE
    // ============================================================================
  
    function initChatbot() {
      const trigger = document.getElementById('rc-chatbot-trigger');
      const panel = document.getElementById('rc-chatbot-panel');
      const closeBtn = document.getElementById('rc-chatbot-close');
      const suggestionBtns = document.querySelectorAll('.rc-chatbot-suggestion-btn');
      
      if (!trigger || !panel || !closeBtn) return;
  
      function openPanel() {
        panel.classList.add('open');
        trigger.setAttribute('aria-expanded', 'true');
      }
  
      function closePanel() {
        panel.classList.remove('open');
        trigger.setAttribute('aria-expanded', 'false');
      }
  
      trigger.addEventListener('click', () => {
        if (panel.classList.contains('open')) {
          closePanel();
        } else {
          openPanel();
        }
      });
  
      closeBtn.addEventListener('click', closePanel);
  
      // Close on outside click
      document.addEventListener('click', (e) => {
        if (!e.target.closest('#rc-chatbot') && panel.classList.contains('open')) {
          closePanel();
        }
      });
  
      // Handle suggestion button clicks
      suggestionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const text = btn.textContent.trim();
          console.log('Chatbot suggestion clicked:', text);
          // In a real implementation, this would trigger actual chatbot logic
          alert(`You selected: "${text}"\n\nIn production, this would start a conversation flow.`);
        });
      });
  
      // Handle chat input (Enter key)
      const chatInput = panel.querySelector('.rc-chatbot-input');
      const sendBtn = panel.querySelector('.rc-chatbot-send');
      
      if (chatInput && sendBtn) {
        function sendMessage() {
          const message = chatInput.value.trim();
          if (message) {
            console.log('Sending message:', message);
            // In production, this would send to backend/AI
            alert(`Message sent: "${message}"\n\nIn production, this would be processed by the AI.`);
            chatInput.value = '';
          }
        }
  
        sendBtn.addEventListener('click', sendMessage);
        
        chatInput.addEventListener('keypress', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
          }
        });
      }
    }
  
    // ============================================================================
    // BUSINESS IMPACT PROGRESS BARS ANIMATION
    // ============================================================================
  
    function initImpactProgressBars() {
      const impactTiles = document.querySelectorAll('.rc-impact-tile');
      if (impactTiles.length === 0) return;
  
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              const progressBar = entry.target.querySelector('.rc-impact-progress-fill');
              if (progressBar) {
                // Trigger animation by adding a class or forcing reflow
                progressBar.style.animation = 'none';
                requestAnimationFrame(() => {
                  requestAnimationFrame(() => {
                    progressBar.style.animation = '';
                  });
                });
              }
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.5 }
      );
  
      impactTiles.forEach((tile) => observer.observe(tile));
    }
  
    // ============================================================================
    // PORTAL POWER-UP ANIMATION
    // ============================================================================
  
    function initPortalAnimation() {
      const portalShell = document.querySelector('.rc-portal-shell');
      if (!portalShell) return;
  
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              // Portal rings already have rotation animation
              // Could add additional "power up" effects here
              const rings = portalShell.querySelectorAll('.rc-portal-ring, .rc-portal-ring-2');
              rings.forEach((ring, index) => {
                setTimeout(() => {
                  ring.style.opacity = '1';
                  ring.style.transform = 'scale(1)';
                }, index * 200);
              });
              observer.unobserve(portalShell);
            }
          });
        },
        { threshold: 0.6 }
      );
  
      observer.observe(portalShell);
    }
  
    // ============================================================================
    // LIVE DATA TICKER AUTO-UPDATE (OPTIONAL)
    // ============================================================================
  
    function initLiveDataTicker() {
      // In production, this would fetch real data from API
      // For now, it's just a CSS animation
      
      // Optional: Update ticker values periodically
      const tickerItems = document.querySelectorAll('.rc-ticker-item span');
      
      function updateTickerValue(element) {
        const currentText = element.textContent;
        const match = currentText.match(/[\d,]+/);
        if (match) {
          const currentValue = parseInt(match[0].replace(/,/g, ''));
          const variation = Math.floor(Math.random() * 10) - 5; // -5 to +5
          const newValue = Math.max(0, currentValue + variation);
          element.textContent = newValue.toLocaleString();
        }
      }
  
      // Update every 30 seconds (optional, disabled by default)
      // setInterval(() => {
      //   tickerItems.forEach(item => updateTickerValue(item));
      // }, 30000);
    }
  
    // ============================================================================
    // KEYBOARD NAVIGATION SUPPORT
    // ============================================================================
  
    function initKeyboardNavigation() {
      // Add keyboard shortcuts
      document.addEventListener('keydown', (e) => {
        // ESC to close chatbot
        if (e.key === 'Escape') {
          const panel = document.getElementById('rc-chatbot-panel');
          if (panel && panel.classList.contains('open')) {
            panel.classList.remove('open');
            document.getElementById('rc-chatbot-trigger')?.setAttribute('aria-expanded', 'false');
          }
        }
      });
  
      // Ensure all interactive elements are keyboard accessible
      const interactiveElements = document.querySelectorAll('button, a, [data-scroll]');
      interactiveElements.forEach(el => {
        if (!el.hasAttribute('tabindex')) {
          el.setAttribute('tabindex', '0');
        }
      });
    }
  
    // ============================================================================
    // VIDEO BACKGROUND OPTIMIZATION
    // ============================================================================
  
    function initVideoBackground() {
      const video = document.querySelector('.rc-hero-video');
      if (!video) return;
  
      // Pause video when not in viewport to save resources
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              video.play().catch(err => console.log('Video autoplay prevented:', err));
            } else {
              video.pause();
            }
          });
        },
        { threshold: 0.25 }
      );
  
      observer.observe(video);
  
      // Fallback for browsers that don't support the video format
      video.addEventListener('error', () => {
        console.warn('Video failed to load. Using fallback background.');
        video.style.display = 'none';
      });
    }
  
    // ============================================================================
    // PARALLAX SCROLL EFFECTS (SUBTLE)
    // ============================================================================
  
    function initParallax() {
      const heroGlobe = document.querySelector('.rc-hero-globe-shell');
      const videoLayer = document.querySelector('.rc-hero-video-layer');
      
      if (!heroGlobe && !videoLayer) return;
  
      const handleScroll = debounce(() => {
        const scrollY = window.scrollY;
        const maxScroll = 800; // Parallax effect range
        
        if (scrollY < maxScroll) {
          // Subtle parallax for globe
          if (heroGlobe) {
            const offset = scrollY * 0.3;
            heroGlobe.style.transform = `translateY(${offset}px)`;
          }
          
          // Even more subtle for video background
          if (videoLayer) {
            const offset = scrollY * 0.15;
            videoLayer.style.transform = `translateY(${offset}px)`;
          }
        }
      }, 10);
  
      window.addEventListener('scroll', handleScroll, { passive: true });
    }
  
    // ============================================================================
    // PERFORMANCE MONITORING
    // ============================================================================
  
    function initPerformanceMonitoring() {
      // Log performance metrics in development
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        window.addEventListener('load', () => {
          setTimeout(() => {
            const perfData = performance.getEntriesByType('navigation')[0];
            console.log('Page Load Performance:');
            console.log('- DOM Content Loaded:', Math.round(perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart), 'ms');
            console.log('- Full Load:', Math.round(perfData.loadEventEnd - perfData.loadEventStart), 'ms');
            console.log('- DOM Interactive:', Math.round(perfData.domInteractive - perfData.fetchStart), 'ms');
          }, 0);
        });
      }
    }
  
    // ============================================================================
    // ACCESSIBILITY ENHANCEMENTS
    // ============================================================================
  
    function initAccessibility() {
      // Announce page load to screen readers
      const srAnnounce = document.createElement('div');
      srAnnounce.setAttribute('role', 'status');
      srAnnounce.setAttribute('aria-live', 'polite');
      srAnnounce.className = 'sr-only';
      srAnnounce.style.position = 'absolute';
      srAnnounce.style.left = '-10000px';
      srAnnounce.style.width = '1px';
      srAnnounce.style.height = '1px';
      srAnnounce.style.overflow = 'hidden';
      document.body.appendChild(srAnnounce);
  
      window.addEventListener('load', () => {
        setTimeout(() => {
          srAnnounce.textContent = 'RISKCAST FutureOS page loaded. Operating system for logistics risk.';
        }, 1000);
      });
  
      // Focus management for modals/panels
      const chatPanel = document.getElementById('rc-chatbot-panel');
      if (chatPanel) {
        const observer = new MutationObserver((mutations) => {
          mutations.forEach((mutation) => {
            if (mutation.attributeName === 'class') {
              if (chatPanel.classList.contains('open')) {
                const firstInput = chatPanel.querySelector('input, button');
                if (firstInput) {
                  setTimeout(() => firstInput.focus(), 100);
                }
              }
            }
          });
        });
        observer.observe(chatPanel, { attributes: true });
      }
    }
  
    // ============================================================================
    // INITIALIZATION - MAIN ENTRY POINT
    // ============================================================================
  
    function init() {
      // Core functionality
      initBootSequence();
      initScrollReveal();
      initSmoothScroll();
      
      // Section-specific features
      initMapNarrative();
      initInteractiveSimulation();
      initCarousel();
      initChatbot();
      initImpactProgressBars();
      initPortalAnimation();
      
      // Enhancements
      initVideoBackground();
      initParallax();
      initLiveDataTicker();
      initKeyboardNavigation();
      initAccessibility();
      
      // Development tools
      initPerformanceMonitoring();
      
      console.log('%c🚀 RISKCAST FutureOS v900 Cinematic Initialized', 'color: #36e27b; font-size: 14px; font-weight: bold;');
    }
  
    // Start everything when DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      // DOM is already ready, initialize immediately
      init();
    }

  })();

  /* ============================================================================
     HERO V900 - CINEMATIC HOLOGRAM SPHERE JAVASCRIPT
     ============================================================================ */

  (function() {
    'use strict';

    /**
     * Initialize Hologram Globe V900
     * DISABLED: Replaced by GlobeUI v5 component
     */
    function initHologramGlobeV900() {
      // GlobeUI v5 handles its own rendering, no need for this
      return;
      const globeContainer = document.querySelector('.rc-hero-globe-h900');
      if (!globeContainer) return;

      const pointsContainer = globeContainer.querySelector('.rc-globe-points-h900');
      if (!pointsContainer) return;

      // Generate 140 hologram points (cities) with random positions
      const pointCount = 140;
      const radius = 48; // Percentage of container

      for (let i = 0; i < pointCount; i++) {
        const point = document.createElement('div');
        point.className = 'rc-globe-point';

        // Generate random spherical coordinates
        const theta = Math.random() * Math.PI * 2; // Longitude
        const phi = Math.acos(Math.random() * 2 - 1); // Latitude

        // Convert to 2D projection
        const x = 50 + radius * Math.sin(phi) * Math.cos(theta);
        const y = 50 + radius * Math.sin(phi) * Math.sin(theta);

        point.style.left = x + '%';
        point.style.top = y + '%';

        // Random flicker delay (0.6-1.4s)
        const flickerDelay = 0.6 + Math.random() * 0.8;
        point.style.animationDelay = flickerDelay + 's';
        point.style.animationDuration = (0.6 + Math.random() * 0.8) + 's';

        pointsContainer.appendChild(point);
      }
    }

    /**
     * Initialize when DOM is ready
     */
    function initV900() {
      // Wait for DOM
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
          setTimeout(initHologramGlobeV900, 100);
        });
      } else {
        setTimeout(initHologramGlobeV900, 100);
      }
    }

    initV900();
  })();

// =============================
// HERO FutureOS v9000 – JS (Tối giản)
// =============================

function initFutureOSGlobe() {
  const globe = document.querySelector(".globe-grid");
  if (!globe) return;

  let r = 0;
  setInterval(() => {
    r += 0.02;
    globe.style.transform = `rotateX(25deg) rotateY(${r}rad)`;
  }, 16);
}

document.addEventListener("DOMContentLoaded", initFutureOSGlobe);
