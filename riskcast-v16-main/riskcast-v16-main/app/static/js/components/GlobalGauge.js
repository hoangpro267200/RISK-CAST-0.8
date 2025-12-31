/**
 * GlobalGauge Component
 * 
 * Renders a circular SVG gauge displaying a global risk score (0-100).
 * Features color-coded zones (green, yellow, red) and smooth animations.
 * 
 * @class GlobalGauge
 * @exports GlobalGauge
 */
export class GlobalGauge {
  /**
   * Initialize the GlobalGauge component
   */
  constructor() {
    this.container = null;
    this.currentScore = 0;
    this.targetScore = 0;
    this.animationFrame = null;
    this.animationStartTime = null;
    this.animationDuration = 600; // milliseconds
    
    // Gauge configuration
    this.config = {
      size: 220,
      strokeWidth: 18,
      centerSize: 160,
      startAngle: -90, // Start at top (12 o'clock)
      endAngle: 270,   // Full circle
    };
    
    this._stylesInjected = false;
  }

  /**
   * Mount the component to a DOM element
   * @param {HTMLElement} el - Target DOM element
   * @param {number} score - Initial risk score (0-100)
   */
  mount(el, score = 0) {
    if (!el) {
      console.warn('GlobalGauge: No element provided for mounting');
      return;
    }

    this.container = el;
    const clampedScore = this._clampScore(score);
    this.currentScore = clampedScore;
    this.targetScore = clampedScore;
    
    this._injectStyles();
    this._createStructure();
    
    // Always render immediately with the clamped score
    this._updateGaugeVisuals(clampedScore);
  }

  /**
   * Update the gauge with a new score
   * @param {number} newScore - New risk score (0-100)
   */
  update(newScore) {
    if (!this.container) {
      console.warn('GlobalGauge: Component not mounted');
      return;
    }

    const clampedScore = this._clampScore(newScore);
    
    // Reset animation
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
    }
    
    this.currentScore = this.targetScore; // Start from current displayed value
    this.targetScore = clampedScore;
    this.animationStartTime = null;
    
    this._startAnimation();
  }

  /**
   * Clamp score to valid range (0-100)
   * @private
   * @param {number} score - Input score
   * @returns {number} Clamped score
   */
  _clampScore(score) {
    if (score == null || score === undefined) return 0;
    const num = parseFloat(score);
    if (isNaN(num)) return 0;
    return Math.max(0, Math.min(100, num));
  }

  /**
   * Get risk level category based on score
   * @private
   * @param {number} score - Risk score
   * @returns {string} Risk level text
   */
  _getRiskLevel(score) {
    if (score < 40) {
      return 'Rủi Ro Thấp';
    } else if (score < 70) {
      return 'Rủi Ro Trung Bình';
    } else {
      return 'Rủi Ro Cao';
    }
  }

  /**
   * Get CSS variable for color based on score thresholds
   * @private
   * @param {number} score - Risk score
   * @returns {string} CSS variable name
   */
  _getColorVariable(score) {
    if (score < 40) {
      return 'var(--risk-low, #00ff88)';
    } else if (score < 70) {
      return 'var(--risk-medium, #ffcc00)';
    } else {
      return 'var(--risk-high, #ff4466)';
    }
  }


  /**
   * Create the HTML structure for the gauge
   * @private
   */
  _createStructure() {
    const { size, strokeWidth, centerSize } = this.config;
    const radius = (size - strokeWidth) / 2;
    const center = size / 2;
    const circumference = 2 * Math.PI * radius;

    this.container.innerHTML = `
      <div class="global-gauge-wrapper">
        <div class="global-gauge-container">
          <svg 
            class="global-gauge-svg" 
            width="${size}" 
            height="${size}" 
            viewBox="0 0 ${size} ${size}"
          >
            <!-- Background circle (track) -->
            <circle
              class="gauge-track"
              cx="${center}"
              cy="${center}"
              r="${radius}"
              fill="none"
              stroke="rgba(255, 255, 255, 0.08)"
              stroke-width="${strokeWidth}"
              stroke-linecap="round"
            />
            
            <!-- Foreground circle (progress) -->
            <circle
              class="gauge-progress"
              cx="${center}"
              cy="${center}"
              r="${radius}"
              fill="none"
              stroke="var(--risk-low, #00ff88)"
              stroke-width="${strokeWidth}"
              stroke-linecap="round"
              stroke-dasharray="${circumference}"
              stroke-dashoffset="${circumference}"
              transform="rotate(-90 ${center} ${center})"
            />
          </svg>

          <!-- Center content -->
          <div class="gauge-center">
            <div class="gauge-score">0</div>
            <div class="gauge-risk-level">Rủi Ro Thấp</div>
            <div class="gauge-label">Điểm Rủi Ro Tổng Thể</div>
          </div>
        </div>
      </div>
    `;

    // Store references for animation
    this.progressCircle = this.container.querySelector('.gauge-progress');
    this.scoreElement = this.container.querySelector('.gauge-score');
    this.riskLevelElement = this.container.querySelector('.gauge-risk-level');
  }

  /**
   * Start the animation loop
   * @private
   */
  _startAnimation() {
    const animate = (timestamp) => {
      if (!this.animationStartTime) {
        this.animationStartTime = timestamp;
      }

      const elapsed = timestamp - this.animationStartTime;
      const progress = Math.min(elapsed / this.animationDuration, 1);
      
      // Ease-in-out cubic easing function
      const eased = progress < 0.5
        ? 4 * progress * progress * progress
        : 1 - Math.pow(-2 * progress + 2, 3) / 2;

      // Interpolate score
      const currentDisplayScore = this.currentScore + (this.targetScore - this.currentScore) * eased;
      
      this._updateGaugeVisuals(currentDisplayScore);

      if (progress < 1) {
        this.animationFrame = requestAnimationFrame(animate);
      } else {
        this.animationFrame = null;
      }
    };

    this.animationFrame = requestAnimationFrame(animate);
  }

  /**
   * Update the visual elements of the gauge
   * @private
   * @param {number} score - Current animated score
   */
  _updateGaugeVisuals(score) {
    if (!this.progressCircle || !this.scoreElement || !this.riskLevelElement) return;

    const { size, strokeWidth } = this.config;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    
    // Calculate stroke offset (reverse direction for clockwise fill)
    const percentage = score / 100;
    const offset = circumference - (percentage * circumference);
    
    // Get color variable
    const colorVar = this._getColorVariable(score);
    
    // Update progress circle with CSS variable
    this.progressCircle.style.stroke = colorVar;
    this.progressCircle.style.strokeDashoffset = offset;
    
    // Add glow effect - set data attribute for CSS to use
    this.progressCircle.setAttribute('data-risk-level', score < 40 ? 'low' : score < 70 ? 'medium' : 'high');
    this.progressCircle.classList.add('gauge-progress-animated');
    
    // Update center score text with CSS variable
    this.scoreElement.textContent = Math.round(score);
    this.scoreElement.style.color = colorVar;
    this.scoreElement.setAttribute('data-risk-level', score < 40 ? 'low' : score < 70 ? 'medium' : 'high');
    
    // Update risk level text
    const riskLevel = this._getRiskLevel(score);
    this.riskLevelElement.textContent = riskLevel;
    this.riskLevelElement.style.color = colorVar;
  }

  /**
   * Inject component styles into the document head
   * @private
   */
  _injectStyles() {
    if (this._stylesInjected) {
      return;
    }

    if (document.getElementById('global-gauge-styles')) {
      this._stylesInjected = true;
      return;
    }

    const style = document.createElement('style');
    style.id = 'global-gauge-styles';
    style.textContent = `
      /* GlobalGauge Component Styles */
      .global-gauge-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 20px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
      }

      .global-gauge-container {
        position: relative;
        display: inline-flex;
        justify-content: center;
        align-items: center;
      }

      .global-gauge-svg {
        display: block;
        filter: drop-shadow(0 4px 20px rgba(0, 0, 0, 0.3));
      }

      .gauge-track {
        transition: stroke 0.3s ease;
      }

      .gauge-progress {
        transition: stroke 0.3s ease, filter 0.3s ease;
        transform-origin: center;
        --gauge-glow-color: var(--risk-low, #00ff88);
      }

      .gauge-progress-animated[data-risk-level="low"] {
        filter: drop-shadow(0 0 8px rgba(0, 255, 136, 0.25));
      }

      .gauge-progress-animated[data-risk-level="medium"] {
        filter: drop-shadow(0 0 8px rgba(255, 204, 0, 0.25));
      }

      .gauge-progress-animated[data-risk-level="high"] {
        filter: drop-shadow(0 0 8px rgba(255, 68, 102, 0.25));
      }

      /* Center content overlay */
      .gauge-center {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 6px;
        text-align: center;
        pointer-events: none;
      }

      .gauge-score {
        font-size: 56px;
        font-weight: 800;
        line-height: 1;
        letter-spacing: -2px;
        color: var(--risk-low, #00ff88);
        transition: color 0.3s ease;
      }

      .gauge-score[data-risk-level="low"] {
        text-shadow: 0 0 20px rgba(0, 255, 136, 0.4);
      }

      .gauge-score[data-risk-level="medium"] {
        text-shadow: 0 0 20px rgba(255, 204, 0, 0.4);
      }

      .gauge-score[data-risk-level="high"] {
        text-shadow: 0 0 20px rgba(255, 68, 102, 0.4);
      }

      .gauge-risk-level {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: var(--risk-low, #00ff88);
        opacity: 0.7;
        transition: color 0.3s ease, opacity 0.3s ease;
        margin-top: -2px;
      }

      .gauge-label {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: rgba(255, 255, 255, 0.5);
        max-width: 120px;
        line-height: 1.3;
        margin-top: 2px;
      }

      /* Responsive adjustments */
      @media (max-width: 640px) {
        .global-gauge-wrapper {
          padding: 16px;
        }

        .gauge-score {
          font-size: 48px;
        }

        .gauge-risk-level {
          font-size: 10px;
          letter-spacing: 0.8px;
        }

        .gauge-label {
          font-size: 10px;
          letter-spacing: 1px;
        }
      }

      /* Accessibility: Reduced motion preference */
      @media (prefers-reduced-motion: reduce) {
        .gauge-progress {
          transition: none;
        }
      }
    `;

    document.head.appendChild(style);
    this._stylesInjected = true;
  }

  /**
   * Cleanup method to cancel ongoing animations
   * Call this before destroying the component
   */
  destroy() {
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
      this.animationFrame = null;
    }
    this.container = null;
    this.progressCircle = null;
    this.scoreElement = null;
    this.riskLevelElement = null;
  }
}

