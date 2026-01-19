// futureos_globe_v900.js
// FINAL — No Crash, No Undefined, No Duplicate Pipeline

(function () {
  'use strict';
  
  console.log("[RISKCAST] Loading FutureOS Globe v900...");

  const container = document.getElementById('globe-v2000');
  if (!container) {
    console.warn("[RISKCAST] globe-v2000 container not found.");
    return;
  }

  // Wait for Three.js and Post-processing modules
  function initGlobe() {
    if (typeof THREE === 'undefined') {
      console.log('[RISKCAST] Waiting for THREE...');
      setTimeout(initGlobe, 100);
      return;
    }
    
    // Check for post-processing modules (ES modules)
    if (typeof window.EffectComposer === 'undefined' && typeof THREE.EffectComposer === 'undefined') {
      console.log('[RISKCAST] Waiting for post-processing modules...');
      setTimeout(initGlobe, 100);
      return;
    }
    
    console.log('[RISKCAST] All dependencies loaded, initializing globe...');

    // =============== BASIC SETUP ===============
    let scene, camera, renderer, composer, globe, halo;

    try {
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0x020405);
      scene.fog = new THREE.Fog(0x020405, 15, 25);

      const aspect = container.clientWidth / container.clientHeight;
      camera = new THREE.PerspectiveCamera(35, aspect, 0.1, 100);
      camera.position.set(0, 0, 6);

      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: false,
        powerPreference: "high-performance"
      });

      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setSize(container.clientWidth, container.clientHeight);
      renderer.setClearColor(0x020405, 1);
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.2;
      container.appendChild(renderer.domElement);
    } catch (e) {
      console.error("[RISKCAST] Renderer init failed:", e);
      return;
    }

    // =============== SHADER UNIFORMS SAFE ===============
    const uniforms = {
      u_time: { value: 0 },
      u_glowStrength: { value: 1.3 },
      u_intensity: { value: 1.0 }
    };

    // =============== SHADER MATERIAL ===============
    const vertex = `
      varying vec3 vWorldPosition;
      varying vec3 vNormal;
      void main() {
        vNormal = normalize(normalMatrix * normal);
        vec4 world = modelMatrix * vec4(position, 1.0);
        vWorldPosition = world.xyz;
        gl_Position = projectionMatrix * viewMatrix * world;
      }
    `;

    const fragment = `
      uniform float u_time;
      uniform float u_glowStrength;
      uniform float u_intensity;
      varying vec3 vWorldPosition;
      varying vec3 vNormal;

      void main() {
        vec3 viewDir = normalize(cameraPosition - vWorldPosition);
        float fresnel = pow(1.0 - max(dot(viewDir, vNormal), 0.0), 3.0);
        float glow = fresnel * u_glowStrength;

        vec3 base = vec3(0.0, 0.95, 0.85);
        vec3 finalColor = base + glow * vec3(0.0, 1.0, 1.0);

        float dist = length(vWorldPosition);
        float gradient = 1.0 - smoothstep(2.5, 3.0, dist);
        float breath = 0.7 + sin(u_time * 0.4) * 0.3;
        float alpha = (gradient * 0.25 + fresnel * 0.5) * breath * u_intensity;

        gl_FragColor = vec4(finalColor, alpha);
      }
    `;

    let material;
    try {
      material = new THREE.ShaderMaterial({
        vertexShader: vertex,
        fragmentShader: fragment,
        uniforms: uniforms,
        transparent: true,
        side: THREE.BackSide,
        blending: THREE.AdditiveBlending,
        depthWrite: false
      });
    } catch (e) {
      console.error("[RISKCAST] ShaderMaterial fail:", e);
      return;
    }

    // =============== GLOBE ===============
    const geo = new THREE.SphereGeometry(2.5, 128, 128);
    globe = new THREE.Mesh(geo, material);
    scene.add(globe);

    // Base sphere
    const baseGeo = new THREE.SphereGeometry(2.5, 64, 64);
    const baseMaterial = new THREE.MeshStandardMaterial({
      color: 0x0a1210,
      roughness: 0.9,
      metalness: 0.1,
      emissive: 0x001013,
      emissiveIntensity: 0.1
    });
    const baseSphere = new THREE.Mesh(baseGeo, baseMaterial);
    scene.add(baseSphere);

    // Halo
    halo = new THREE.Mesh(
      new THREE.SphereGeometry(2.9, 64, 64),
      new THREE.MeshBasicMaterial({ 
        color: 0x00fff7, 
        opacity: 0.12, 
        transparent: true,
        side: THREE.BackSide
      })
    );
    scene.add(halo);

    // =============== LIGHTING ===============
    const ambientLight = new THREE.AmbientLight(0x00f0ff, 0.15);
    scene.add(ambientLight);

    const pointLight1 = new THREE.PointLight(0x00f0ff, 0.8, 20);
    pointLight1.position.set(5, 5, 5);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0x36e27b, 0.6, 20);
    pointLight2.position.set(-5, -5, -5);
    scene.add(pointLight2);

    // =============== POST PROCESSING ===============
    try {
      // Check for ES modules (new way) or global (old way)
      const EffectComposerClass = window.EffectComposer || THREE.EffectComposer;
      const RenderPassClass = window.RenderPass || THREE.RenderPass;
      const UnrealBloomPassClass = window.UnrealBloomPass || THREE.UnrealBloomPass;
      
      if (EffectComposerClass && RenderPassClass && UnrealBloomPassClass) {
        
        const renderTarget = new THREE.WebGLRenderTarget(
          container.clientWidth,
          container.clientHeight,
          {
            minFilter: THREE.LinearFilter,
            magFilter: THREE.LinearFilter,
            format: THREE.RGBAFormat
          }
        );
        
        composer = new EffectComposerClass(renderer, renderTarget);
        
        const renderPass = new RenderPassClass(scene, camera);
        renderPass.clear = true;
        composer.addPass(renderPass);

        const bloom = new UnrealBloomPassClass(
          new THREE.Vector2(container.clientWidth, container.clientHeight),
          1.2,
          0.4,
          0.85
        );
        bloom.renderToScreen = true;
        composer.addPass(bloom);

        console.log("[RISKCAST] Post-processing enabled ✓");
      } else {
        throw new Error('Post-processing dependencies missing');
      }
    } catch (e) {
      console.warn("[RISKCAST] Post-processing disabled:", e);
      composer = null;
    }

    // =============== ANIMATION (SAFEST POSSIBLE) ===============
    const clock = new THREE.Clock();

    function animate() {
      requestAnimationFrame(animate);

      const elapsed = clock.getElapsedTime();
      const delta = clock.getDelta();

      // SAFE GUARD → không crash
      if (uniforms && uniforms.u_time) {
        uniforms.u_time.value = elapsed;
      }

      // Rotate
      globe.rotation.y += 0.05 * delta;
      baseSphere.rotation.y += 0.05 * delta;
      halo.rotation.y -= 0.03 * delta;

      // Render
      if (composer) {
        composer.render();
      } else {
        renderer.render(scene, camera);
      }
    }

    animate();

    // RESIZE
    function onResize() {
      const width = container.clientWidth;
      const height = container.clientHeight;
      
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);

      if (composer) {
        composer.setSize(width, height);
      }
    }

    window.addEventListener("resize", onResize);
    onResize();
  }

  // Start initialization - wait longer for ES modules to load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(initGlobe, 500);
    });
  } else {
    setTimeout(initGlobe, 500);
  }

})();
