/**
 * RISKCAST FutureOS - Main JavaScript
 * Handles animations, interactions, and dynamic behaviors
 */

/**
 * Calculate responsive route width based on marker positions
 * @param {HTMLElement} startMarker - Starting point marker
 * @param {HTMLElement} endMarker - Ending point marker
 * @returns {string} - CSS width value (in pixels or percentage)
 */
function calculateRouteWidth(startMarker, endMarker) {
  if (!startMarker || !endMarker) {
    return '80px'; // Fallback default
  }

  // Get computed positions from style attributes
  const startTop = parseFloat(startMarker.style.top) || 0;
  const startLeft = parseFloat(startMarker.style.left) || 0;
  const endTop = parseFloat(endMarker.style.top) || 0;
  const endLeft = parseFloat(endMarker.style.left) || 0;

  // Calculate distance using hypotenuse
  const deltaX = endLeft - startLeft;
  const deltaY = endTop - startTop;
  const distance = Math.hypot(deltaX, deltaY);

  // Scale visually (0.9 multiplier for visual adjustment)
  // Convert percentage to pixels based on typical container width (~90% of 600px = 540px)
  const containerWidth = 540; // Approximate container width in pixels
  const distanceInPx = (distance / 100) * containerWidth;
  const routeWidth = distanceInPx * 0.9;

  // Ensure minimum width and return as pixels
  return `${Math.max(routeWidth, 60)}px`;
}

/**
 * IntersectionObserver for fade-up animations
 */
const fadeUpElements = document.querySelectorAll('[data-animate="fade-up"]');
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target); // Only animate once
      }
    });
  },
  { threshold: 0.2 } // Trigger when 20% of the element is visible
);

fadeUpElements.forEach((el) => {
  observer.observe(el);
});

/**
 * IntersectionObserver for staggered fade-up animations (Chaos & Impact sections)
 */
const staggeredFadeUpSections = document.querySelectorAll('[data-animate="fade-up-stagger"]');
const staggeredObserver = new IntersectionObserver(
  (entries, observer) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        Array.from(entry.target.children).forEach((child, index) => {
          // Assuming child is the direct element with anim-fade-up
          setTimeout(() => {
            child.classList.add('is-visible');
          }, index * 200); // Stagger by 200ms
        });
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.2 }
);

staggeredFadeUpSections.forEach((section) => {
  staggeredObserver.observe(section);
});

/**
 * Realtime Map Narrative timeline (Section 5)
 */
const mapSection = document.getElementById('map');
const portKlangMarker = document.getElementById('port-klang-marker');
const portKlangLabel = document.getElementById('port-klang-label');
const mapRoute = document.getElementById('map-route');
const aiBubble = document.getElementById('ai-bubble');
const singaporeMarker = document.getElementById('singapore-marker');
let mapAnimationPlayed = false;

const mapObserver = new IntersectionObserver(
  (entries) => {
    if (entries[0].isIntersecting && !mapAnimationPlayed) {
      mapAnimationPlayed = true;

      // Step 1: show Port Klang marker with text "Congestion detected".
      setTimeout(() => {
        portKlangMarker.classList.add('is-visible');
        portKlangLabel.classList.add('is-visible');
      }, 500);

      // Step 2: animate route highlight to Singapore with responsive width calculation.
      setTimeout(() => {
        singaporeMarker.classList.add('is-visible');
        // Calculate responsive route width based on marker positions
        const routeWidth = calculateRouteWidth(portKlangMarker, singaporeMarker);
        mapRoute.style.width = routeWidth;
        mapRoute.classList.add('is-visible');
      }, 1500);

      // Step 3: show AI bubble with details.
      setTimeout(() => {
        aiBubble.classList.add('is-visible');
      }, 2500);
    }
  },
  { threshold: 0.5 }
);

if (mapSection) {
  mapObserver.observe(mapSection);
}

/**
 * Hover simulations (Section 6)
 */
const simCards = document.querySelectorAll('.rc-sim-card-hover-container');
simCards.forEach((card) => {
  card.addEventListener('mouseenter', () => {
    card.classList.add('is-hovered');
    // Specific animations for each scenario
    const barChart = card.querySelector('.rc-bar-chart');
    if (barChart) {
      Array.from(barChart.children).forEach((bar, index) => {
        bar.style.transitionDelay = `${index * 0.05}s`; // Stagger bars
      });
    }
  });
  card.addEventListener('mouseleave', () => {
    card.classList.remove('is-hovered');
  });
});
