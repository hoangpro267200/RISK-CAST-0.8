/* ============================================================================
   RISKCAST FutureOS - Homepage v2000 JavaScript
   Cinematic Decision Cockpit
   ============================================================================ */

(function() {
  'use strict';

  // ============================================================================
  // CONFIGURATION
  // ============================================================================
  const CONFIG = {
    globe: {
      radius: 2.5,
      atmosphereScale: 1.15,
      riskPointCount: 8,
      microStarCount: 120,
      arcCount: 5,
      starfieldCount: 250,
      rotationSpeed: 50, // seconds per full revolution
      cameraFOV: 45,
      bloom: {
        strength: 0.7,
        threshold: 0.2,
        radius: 0.3
      },
      parallax: {
        maxTilt: 8, // degrees
        sensitivity: 0.001
      }
    },
    animations: {
      fadeInOffset: 30,
      threshold: 0.2,
      staggerDelay: 120 // ms
    }
  };

  let isReducedMotion = false;

  // ============================================================================
  // UTILITY FUNCTIONS
  // ============================================================================
  function checkReducedMotion() {
    isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (isReducedMotion) {
      document.documentElement.classList.add('reduced-motion');
    }
    return isReducedMotion;
  }

  function throttle(func, wait) {
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
  // WEBGL DETECTION & FALLBACK
  // ============================================================================
  function detectWebGL() {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (!gl) {
        document.body.classList.add('no-webgl');
        return false;
      }
      return true;
    } catch (e) {
      document.body.classList.add('no-webgl');
      return false;
    }
  }

  // ============================================================================
  // SCROLL ANIMATIONS
  // ============================================================================
  function initAnimations() {
    const animElements = document.querySelectorAll('.rc-anim-fade-up');
    
    if (!animElements.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry, index) => {
          if (entry.isIntersecting) {
            // Stagger delay for grid items
            const delay = isReducedMotion ? 0 : (index % 3) * CONFIG.animations.staggerDelay;
            
            setTimeout(() => {
              entry.target.classList.add('is-visible');
              observer.unobserve(entry.target);
            }, delay);
          }
        });
      },
      { 
        threshold: CONFIG.animations.threshold,
        rootMargin: '0px 0px -50px 0px'
      }
    );

    animElements.forEach((el) => observer.observe(el));
  }

  // ============================================================================
  // THREE.JS GLOBE INITIALIZATION
  // ============================================================================
  function initGlobeV2000() {
    const container = document.getElementById('globe-v2000');
    if (!container) {
      console.warn('[RISKCAST v2000] Globe container not found');
      return;
    }
    
    if (!detectWebGL()) {
      console.warn('[RISKCAST v2000] WebGL not available, using SVG fallback');
      return;
    }
    
    if (typeof THREE === 'undefined') {
      console.warn('[RISKCAST v2000] Three.js not loaded');
      return;
    }
    
    if (!THREE.WebGLRenderer) {
      console.warn('[RISKCAST v2000] Three.js WebGLRenderer not available');
      return;
    }

    let scene, camera, renderer, composer;
    let sphere, atmosphere, riskPoints, microStars, arcs, starfield;
    let clock = new THREE.Clock();
    let mouseX = 0, mouseY = 0;
    let targetRotationX = 0, targetRotationY = 0;
    let animationFrameId = null;
    let isInitialized = false;

    // Shaders
    const atmosphereVertexShader = `
      uniform float time;
      varying vec3 vWorldPosition;
      varying vec3 vNormal;

      void main() {
        vNormal = normalize(normalMatrix * normal);
        vec3 pos = position;
        pos += normal * 0.02;
        vec4 worldPos = modelMatrix * vec4(pos, 1.0);
        vWorldPosition = worldPos.xyz;
        float scale = 1.0 + sin(time * 0.4) * 0.03;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(pos * scale, 1.0);
      }
    `;

    const atmosphereFragmentShader = `
      uniform float time;
      varying vec3 vWorldPosition;
      varying vec3 vNormal;
      uniform vec3 cameraPosition;

      void main() {
        vec3 viewDirection = normalize(cameraPosition - vWorldPosition);
        float fresnel = pow(1.0 - dot(viewDirection, vNormal), 2.0);
        float dist = length(vWorldPosition);
        float gradient = 1.0 - smoothstep(2.5, 3.0, dist);
        float rim = fresnel * 0.8;
        float breath = 0.7 + sin(time * 0.4) * 0.3;
        vec3 color = mix(
          vec3(0.0, 0.95, 1.0),
          vec3(0.0, 0.8, 0.9),
          gradient
        );
        float alpha = (gradient * 0.25 + rim * 0.5) * breath;
        gl_FragColor = vec4(color, alpha);
      }
    `;

    const riskPulseVertexShader = `
      uniform float time;
      uniform float pulseSpeed;
      varying float vPulse;

      void main() {
        vPulse = sin(time * pulseSpeed) * 0.5 + 0.5;
        vec3 pos = position;
        float scale = 0.6 + vPulse * 0.8;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(pos * scale, 1.0);
        gl_PointSize = 10.0 * (300.0 / -gl_Position.z);
      }
    `;

    const riskPulseFragmentShader = `
      uniform vec3 color;
      varying float vPulse;

      void main() {
        vec2 center = gl_PointCoord - vec2(0.5);
        float dist = length(center);
        if (dist > 0.5) discard;
        float alpha = (1.0 - dist * 2.0) * (0.7 + vPulse * 0.3);
        vec3 finalColor = color * (1.0 + vPulse * 0.5);
        gl_FragColor = vec4(finalColor, alpha);
      }
    `;

    function init() {
      if (isInitialized) return;

      try {
        // Scene
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x020405);
        scene.fog = new THREE.Fog(0x020405, 15, 25);

        // Camera
        const aspect = container.clientWidth / container.clientHeight;
        camera = new THREE.PerspectiveCamera(CONFIG.globe.cameraFOV, aspect, 0.1, 100);
        camera.position.set(0, 0, 8);

        // Renderer
        renderer = new THREE.WebGLRenderer({ 
          antialias: true,
          alpha: false,
          powerPreference: "high-performance"
        });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setClearColor(0x020405, 1);
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.2;
        container.appendChild(renderer.domElement);

        // Post-processing
        composer = new THREE.EffectComposer(renderer);
        const renderPass = new THREE.RenderPass(scene, camera);
        composer.addPass(renderPass);

        const bloomPass = new THREE.UnrealBloomPass(
          new THREE.Vector2(container.clientWidth, container.clientHeight),
          CONFIG.globe.bloom.strength,
          CONFIG.globe.bloom.radius,
          CONFIG.globe.bloom.threshold
        );
        composer.addPass(bloomPass);

        // 3D Sphere
        const sphereGeometry = new THREE.SphereGeometry(CONFIG.globe.radius, 64, 64);
        const sphereMaterial = new THREE.MeshStandardMaterial({
          color: 0x0a1210,
          roughness: 0.9,
          metalness: 0.1,
          emissive: 0x001013,
          emissiveIntensity: 0.1
        });
        sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
        scene.add(sphere);

        // Atmosphere
        const atmosphereGeometry = new THREE.SphereGeometry(
          CONFIG.globe.radius * CONFIG.globe.atmosphereScale,
          64,
          64
        );
        const atmosphereMaterial = new THREE.ShaderMaterial({
          vertexShader: atmosphereVertexShader,
          fragmentShader: atmosphereFragmentShader,
          uniforms: {
            time: { value: 0 },
            cameraPosition: { value: camera.position }
          },
          transparent: true,
          side: THREE.BackSide,
          blending: THREE.AdditiveBlending,
          depthWrite: false
        });
        atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
        scene.add(atmosphere);

        // Risk Points
        const riskGeometry = new THREE.BufferGeometry();
        const riskPositions = [];
        const riskColors = [];
        const riskColor = new THREE.Color(0xff3366);

        for (let i = 0; i < CONFIG.globe.riskPointCount; i++) {
          const theta = Math.random() * Math.PI * 2;
          const phi = Math.acos(Math.random() * 2 - 1);
          const radius = CONFIG.globe.radius * 1.02;

          riskPositions.push(
            radius * Math.sin(phi) * Math.cos(theta),
            radius * Math.sin(phi) * Math.sin(theta),
            radius * Math.cos(phi)
          );
          riskColors.push(riskColor.r, riskColor.g, riskColor.b);
        }

        riskGeometry.setAttribute('position', new THREE.Float32BufferAttribute(riskPositions, 3));
        riskGeometry.setAttribute('color', new THREE.Float32BufferAttribute(riskColors, 3));

        const riskMaterial = new THREE.ShaderMaterial({
          vertexShader: riskPulseVertexShader,
          fragmentShader: riskPulseFragmentShader,
          uniforms: {
            time: { value: 0 },
            pulseSpeed: { value: 2.0 },
            color: { value: riskColor }
          },
          transparent: true,
          vertexColors: true,
          blending: THREE.AdditiveBlending,
          depthWrite: false
        });

        riskPoints = new THREE.Points(riskGeometry, riskMaterial);
        scene.add(riskPoints);

        // Micro Stars
        const starGeometry = new THREE.BufferGeometry();
        const starPositions = [];
        const starColor = new THREE.Color(0x00e4ff);

        for (let i = 0; i < CONFIG.globe.microStarCount; i++) {
          const theta = Math.random() * Math.PI * 2;
          const phi = Math.acos(Math.random() * 2 - 1);
          const radius = CONFIG.globe.radius * 0.999;

          starPositions.push(
            radius * Math.sin(phi) * Math.cos(theta),
            radius * Math.sin(phi) * Math.sin(theta),
            radius * Math.cos(phi)
          );
        }

        starGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starPositions, 3));

        const starMaterial = new THREE.PointsMaterial({
          color: starColor,
          size: 1.2,
          transparent: true,
          opacity: 0.35,
          blending: THREE.AdditiveBlending,
          sizeAttenuation: true
        });

        microStars = new THREE.Points(starGeometry, starMaterial);
        scene.add(microStars);

        // Arc Paths
        arcs = [];
        const arcColors = [
          new THREE.Color(0x36e27b),
          new THREE.Color(0x00f0ff),
          new THREE.Color(0x36e27b),
          new THREE.Color(0x00f0ff),
          new THREE.Color(0x36e27b)
        ];

        for (let i = 0; i < CONFIG.globe.arcCount; i++) {
          const startTheta = Math.random() * Math.PI * 2;
          const startPhi = Math.acos(Math.random() * 2 - 1);
          const endTheta = Math.random() * Math.PI * 2;
          const endPhi = Math.acos(Math.random() * 2 - 1);

          const startRadius = CONFIG.globe.radius * 1.05;
          const endRadius = CONFIG.globe.radius * 1.05;

          const start = new THREE.Vector3(
            startRadius * Math.sin(startPhi) * Math.cos(startTheta),
            startRadius * Math.sin(startPhi) * Math.sin(startTheta),
            startRadius * Math.cos(startPhi)
          );

          const end = new THREE.Vector3(
            endRadius * Math.sin(endPhi) * Math.cos(endTheta),
            endRadius * Math.sin(endPhi) * Math.sin(endTheta),
            endRadius * Math.cos(endPhi)
          );

          const mid = start.clone().add(end).multiplyScalar(0.5);
          const control = mid.clone().normalize().multiplyScalar(CONFIG.globe.radius * 1.3);

          const curve = new THREE.QuadraticBezierCurve3(start, control, end);
          const points = curve.getPoints(80);
          const curveGeometry = new THREE.BufferGeometry().setFromPoints(points);

          const curveMaterial = new THREE.LineBasicMaterial({
            color: arcColors[i % arcColors.length],
            transparent: true,
            opacity: 0.12,
            linewidth: 1
          });

          const arcLine = new THREE.Line(curveGeometry, curveMaterial);
          scene.add(arcLine);

          const pulseGeometry = new THREE.BufferGeometry();
          pulseGeometry.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0], 3));

          const pulseMaterial = new THREE.PointsMaterial({
            color: arcColors[i % arcColors.length],
            size: 6,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending
          });

          const pulse = new THREE.Points(pulseGeometry, pulseMaterial);
          scene.add(pulse);

          arcs.push({
            curve: curve,
            line: arcLine,
            pulse: pulse,
            progress: Math.random(),
            speed: 0.25 + Math.random() * 0.15
          });
        }

        // Starfield
        const starfieldGeometry = new THREE.BufferGeometry();
        const starfieldPositions = [];
        const starfieldColor = new THREE.Color(0x00f0ff);

        for (let i = 0; i < CONFIG.globe.starfieldCount; i++) {
          const radius = 15 + Math.random() * 10;
          const theta = Math.random() * Math.PI * 2;
          const phi = Math.acos(Math.random() * 2 - 1);

          starfieldPositions.push(
            radius * Math.sin(phi) * Math.cos(theta),
            radius * Math.sin(phi) * Math.sin(theta),
            radius * Math.cos(phi)
          );
        }

        starfieldGeometry.setAttribute(
          'position',
          new THREE.Float32BufferAttribute(starfieldPositions, 3)
        );

        const starfieldMaterial = new THREE.PointsMaterial({
          color: starfieldColor,
          size: 0.8,
          transparent: true,
          opacity: 0.25,
          blending: THREE.AdditiveBlending
        });

        starfield = new THREE.Points(starfieldGeometry, starfieldMaterial);
        scene.add(starfield);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0x00f0ff, 0.12);
        scene.add(ambientLight);

        const pointLight1 = new THREE.PointLight(0x00f0ff, 0.6, 20);
        pointLight1.position.set(5, 5, 5);
        scene.add(pointLight1);

        const pointLight2 = new THREE.PointLight(0x36e27b, 0.5, 20);
        pointLight2.position.set(-5, -5, -5);
        scene.add(pointLight2);

        // Mouse Parallax
        const onMouseMove = throttle((event) => {
          if (isReducedMotion) return;
          
          const rect = container.getBoundingClientRect();
          mouseX = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
          mouseY = ((event.clientY - rect.top) / rect.height - 0.5) * 2;

          targetRotationX = mouseY * CONFIG.globe.parallax.maxTilt * CONFIG.globe.parallax.sensitivity * 10;
          targetRotationY = mouseX * CONFIG.globe.parallax.maxTilt * CONFIG.globe.parallax.sensitivity * 10;
        }, 16);

        container.addEventListener('mousemove', onMouseMove);

        // Resize Handler
        const onWindowResize = throttle(() => {
          if (!container || !camera || !renderer || !composer) return;
          
          const width = container.clientWidth;
          const height = container.clientHeight;

          camera.aspect = width / height;
          camera.updateProjectionMatrix();

          renderer.setSize(width, height);
          composer.setSize(width, height);
        }, 250);

        window.addEventListener('resize', onWindowResize);

        // Animation Loop
        function animate() {
          animationFrameId = requestAnimationFrame(animate);

          const elapsedTime = clock.getElapsedTime();
          const delta = clock.getDelta();

          if (isReducedMotion) {
            // Minimal animation in reduced motion mode
            composer.render();
            return;
          }

          // Update shader uniforms
          atmosphereMaterial.uniforms.time.value = elapsedTime;
          atmosphereMaterial.uniforms.cameraPosition.value.copy(camera.position);

          riskMaterial.uniforms.time.value = elapsedTime;

          // Auto-rotate
          const rotationSpeed = (Math.PI * 2) / CONFIG.globe.rotationSpeed;
          sphere.rotation.y += rotationSpeed * delta;
          atmosphere.rotation.y += rotationSpeed * delta;
          microStars.rotation.y += rotationSpeed * delta;
          riskPoints.rotation.y += rotationSpeed * delta;

          // Parallax tilt
          camera.rotation.x += (targetRotationX - camera.rotation.x) * 0.05;
          camera.rotation.y += (targetRotationY - camera.rotation.y) * 0.05;

          // Update arc pulses
          arcs.forEach((arc) => {
            arc.progress += delta * arc.speed;
            if (arc.progress > 1) arc.progress = 0;

            const point = arc.curve.getPoint(arc.progress);
            arc.pulse.position.copy(point);
            arc.pulse.material.opacity = 0.8 * (1.0 - Math.abs(arc.progress - 0.5) * 2);
          });

          // Starfield drift
          starfield.rotation.y += delta * 0.04;
          starfield.rotation.x += delta * 0.025;

          // Render
          composer.render();
        }

        animate();
        onWindowResize();
        isInitialized = true;
      } catch (error) {
        console.warn('Three.js initialization failed:', error);
        document.body.classList.add('no-webgl');
      }
    }

    // Initialize when ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        setTimeout(init, 100);
      });
    } else {
      setTimeout(init, 100);
    }
  }

  // ============================================================================
  // MAP NARRATIVE TIMELINE
  // ============================================================================
  function initMapNarrative() {
    const mapSection = document.querySelector('.rc-section-map');
    if (!mapSection) return;

    const klang = document.getElementById('rc-marker-klang');
    const klangLabel = document.getElementById('rc-label-klang');
    const sin = document.getElementById('rc-marker-sin');
    const routeOriginal = document.getElementById('rc-route-original');
    const routeAlt = document.getElementById('rc-route-alt');
    const aiBubble = document.getElementById('rc-map-ai-bubble');

    let played = false;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !played) {
            played = true;

            // Step 1: Show Port Klang risk (400ms)
            setTimeout(() => {
              if (klang) {
                klang.style.opacity = '1';
                klang.style.transition = 'opacity 0.5s ease';
              }
              if (klangLabel) klangLabel.classList.add('is-visible');
            }, 400);

            // Step 2: Show Singapore + routes (1400ms)
            setTimeout(() => {
              if (sin) {
                sin.style.opacity = '1';
                sin.style.transition = 'opacity 0.5s ease';
              }
              if (routeOriginal) {
                routeOriginal.style.opacity = '0.35';
                routeOriginal.style.transition = 'opacity 0.5s ease';
              }
              if (routeAlt) routeAlt.classList.add('is-visible');
            }, 1400);

            // Step 3: Show AI bubble (2400ms)
            setTimeout(() => {
              if (aiBubble) aiBubble.classList.add('is-visible');
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
  // MAP CANVAS BACKGROUND
  // ============================================================================
  function initMapCanvas() {
    const canvas = document.getElementById('rc-map-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const container = canvas.parentElement;

    function draw() {
      const rect = container.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw grid
      const gridSize = 52;
      ctx.strokeStyle = 'rgba(0, 255, 200, 0.04)';
      ctx.lineWidth = 1;

      for (let x = 0; x < canvas.width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }

      for (let y = 0; y < canvas.height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }

      // Draw dots (ports representation)
      const dotCount = 45;
      ctx.fillStyle = 'rgba(0, 228, 255, 0.25)';
      
      for (let i = 0; i < dotCount; i++) {
        const x = Math.random() * canvas.width;
        const y = Math.random() * canvas.height;
        const size = 1.5 + Math.random() * 1.5;
        
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    draw();

    // Redraw on resize (throttled)
    const resizeHandler = throttle(() => {
      draw();
    }, 250);

    window.addEventListener('resize', resizeHandler);
  }

  // ============================================================================
  // SIMULATION CARDS
  // ============================================================================
  function initSimulationCards() {
    const simCards = document.querySelectorAll('.rc-sim-card');
    
    simCards.forEach((card) => {
      card.addEventListener('mouseenter', () => {
        card.classList.add('is-hovered');
      });
      
      card.addEventListener('mouseleave', () => {
        card.classList.remove('is-hovered');
      });
    });
  }

  // ============================================================================
  // COUNT-UP ANIMATION (Impact Metrics)
  // ============================================================================
  function initCountUp() {
    if (isReducedMotion) return;

    const impactCards = document.querySelectorAll('.rc-impact-value[data-target]');
    
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !entry.target.classList.contains('counted')) {
            entry.target.classList.add('counted');
            
            const target = parseFloat(entry.target.getAttribute('data-target'));
            const duration = 800;
            const startTime = performance.now();
            
            function animate(currentTime) {
              const elapsed = currentTime - startTime;
              const progress = Math.min(elapsed / duration, 1);
              
              // Easing: ease-out
              const easeOut = 1 - Math.pow(1 - progress, 3);
              const current = target * easeOut;
              
              if (target >= 1 && target < 100) {
                entry.target.textContent = Math.round(current) + '%';
              } else if (target >= 100) {
                entry.target.textContent = current.toFixed(1) + '%';
              } else {
                entry.target.textContent = target + '%';
              }
              
              if (progress < 1) {
                requestAnimationFrame(animate);
              } else {
                if (target >= 1 && target < 100) {
                  entry.target.textContent = target + '%';
                } else if (target >= 100) {
                  entry.target.textContent = target + '%';
                }
              }
            }
            
            requestAnimationFrame(animate);
          }
        });
      },
      { threshold: 0.5 }
    );

    impactCards.forEach((card) => observer.observe(card));
  }

  // ============================================================================
  // SMOOTH SCROLL NAVIGATION
  // ============================================================================
  function initNavSmoothScroll() {
    const scrollLinks = document.querySelectorAll('[data-scroll]');
    
    scrollLinks.forEach((link) => {
      link.addEventListener('click', (e) => {
        const targetId = link.getAttribute('data-scroll');
        const targetElement = document.getElementById(targetId);
        
        if (targetElement) {
          e.preventDefault();
          
          const headerOffset = 136;
          const elementPosition = targetElement.getBoundingClientRect().top;
          const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

          window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
          });
        }
      });
    });
  }

  // ============================================================================
  // INITIALIZATION
  // ============================================================================
  function init() {
    console.log('%c🚀 RISKCAST FutureOS v2000 Initialized', 'color: #36e27b; font-size: 14px; font-weight: bold;');
    
    checkReducedMotion();
    detectWebGL();
    initAnimations();
    initMapNarrative();
    initMapCanvas();
    initSimulationCards();
    initCountUp();
    initNavSmoothScroll();
    
    // Globe initialization (wait for Three.js and dependencies to load)
    function isThreeReady() {
      return typeof THREE !== 'undefined' && 
             THREE.WebGLRenderer && 
             THREE.Scene && 
             THREE.PerspectiveCamera &&
             typeof THREE.EffectComposer !== 'undefined';
    }
    
    function tryInitGlobe() {
      if (isThreeReady()) {
        initGlobeV2000();
        return true;
      }
      return false;
    }
    
    // Try immediately if scripts are already loaded
    if (!tryInitGlobe()) {
      // Wait for window load to ensure all scripts are loaded
      if (document.readyState === 'loading') {
        window.addEventListener('load', () => {
          setTimeout(() => {
            if (!tryInitGlobe()) {
              // Retry with interval if still not ready
              let retries = 0;
              const maxRetries = 30; // 3 seconds max
              
              const checkThree = setInterval(() => {
                retries++;
                if (tryInitGlobe() || retries >= maxRetries) {
                  clearInterval(checkThree);
                  if (retries >= maxRetries && !isThreeReady()) {
                    console.warn('[RISKCAST v2000] Three.js dependencies not fully loaded, using fallback globe');
                  }
                }
              }, 100);
            }
          }, 200);
        });
      } else {
        // DOM already loaded, try with delay
        setTimeout(() => {
          if (!tryInitGlobe()) {
            let retries = 0;
            const maxRetries = 30;
            
            const checkThree = setInterval(() => {
              retries++;
              if (tryInitGlobe() || retries >= maxRetries) {
                clearInterval(checkThree);
              }
            }, 100);
          }
        }, 300);
      }
    }
  }

  // Start when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();





