// futureos_globe_v2000_insane.js
// RISKCAST FutureOS — Orbital Risk Intelligence Core v2200 (Cinematic)

import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.161.0/build/three.module.js";
import { OrbitControls } from "https://cdn.jsdelivr.net/npm/three@0.161.0/examples/jsm/controls/OrbitControls.js";
import { EffectComposer } from "https://cdn.jsdelivr.net/npm/three@0.161.0/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "https://cdn.jsdelivr.net/npm/three@0.161.0/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "https://cdn.jsdelivr.net/npm/three@0.161.0/examples/jsm/postprocessing/UnrealBloomPass.js";

(() => {
  const canvas = document.getElementById("globe-v2000");
  if (!canvas) {
    console.warn("[RISKCAST] globe-v2000 canvas not found.");
    return;
  }

  const container = document.getElementById("globe-v2000-container") || canvas.parentElement;
  const getSize = () => {
    const target = container || canvas;
    return {
      width: target?.clientWidth || window.innerWidth * 0.55,
      height: target?.clientHeight || window.innerWidth * 0.55
    };
  };

  const GLOBE_SIZE = window.innerWidth * 0.28; // 28% radius → ~55% width
  let globeRadius = GLOBE_SIZE;
  let { width, height } = getSize();

  // =========================
  // 1. CORE THREE SETUP
  // =========================
  const scene = new THREE.Scene();
  scene.background = null;

  const camera = new THREE.PerspectiveCamera(
    36,
    width / Math.max(height, 1),
    Math.max(0.1, globeRadius * 0.002),
    globeRadius * 12
  );
  camera.position.set(0, globeRadius * 0.18, globeRadius * 2.4);

  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true
  });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.6));
  renderer.setSize(width, height, false);

  const controls = new OrbitControls(camera, canvas);
  controls.enablePan = false;
  controls.enableZoom = false;
  controls.enableDamping = true;
  controls.autoRotate = false;
  controls.target.set(0, 0, 0);
  controls.update();

  // =========================
  // 2. LIGHTING
  // =========================
  scene.add(new THREE.AmbientLight(0x0b1720, 0.9));

  const keyLight = new THREE.DirectionalLight(0x36e27b, 1.1);
  keyLight.position.set(globeRadius * 0.9, globeRadius * 1.4, globeRadius * 1.2);
  scene.add(keyLight);

  const rimLight = new THREE.DirectionalLight(0x00f0ff, 0.6);
  rimLight.position.set(-globeRadius, globeRadius * 0.5, -globeRadius);
  scene.add(rimLight);

  // =========================
  // 3. SHADERS — CORE GLOBE
  // =========================
  const coreUniforms = {
    u_time: { value: 0 },
    u_glowStrength: { value: 1.4 },
    u_intensity: { value: 1.0 },
    u_noiseScale: { value: 2.5 },
    u_scanlineIntensity: { value: 0.55 }
  };

  const coreVertex = `
    varying vec3 vWorldPosition;
    varying vec3 vNormal;

    void main() {
      vNormal = normalize(normalMatrix * normal);
      vec4 world = modelMatrix * vec4(position, 1.0);
      vWorldPosition = world.xyz;
      gl_Position = projectionMatrix * viewMatrix * world;
    }
  `;

  const coreFragment = `
    uniform float u_time;
    uniform float u_glowStrength;
    uniform float u_intensity;
    uniform float u_noiseScale;
    uniform float u_scanlineIntensity;

    varying vec3 vWorldPosition;
    varying vec3 vNormal;

    float hash(vec2 p) {
      return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
    }

    float noise(vec2 p) {
      vec2 i = floor(p);
      vec2 f = fract(p);
      float a = hash(i);
      float b = hash(i + vec2(1.0, 0.0));
      float c = hash(i + vec2(0.0, 1.0));
      float d = hash(i + vec2(1.0, 1.0));
      vec2 u = f * f * (3.0 - 2.0 * f);
      return mix(a, b, u.x) +
             (c - a) * u.y * (1.0 - u.x) +
             (d - b) * u.x * u.y;
    }

    void main() {
      vec3 viewDir = normalize(cameraPosition - vWorldPosition);
      float fresnel = pow(1.0 - max(dot(viewDir, vNormal), 0.0), 3.0);

      float lat = sin(vWorldPosition.y * 0.06);
      float lon = sin(atan(vWorldPosition.z, vWorldPosition.x) * 0.12);
      float grid = smoothstep(0.88, 0.96, abs(lat)) +
                   smoothstep(0.88, 0.96, abs(lon));

      float scan = sin(vWorldPosition.y * 0.32 - u_time * 4.5);
      scan = (scan * 0.5 + 0.5) * u_scanlineIntensity;

      float n = noise(vWorldPosition.xz * u_noiseScale + u_time * 0.8);
      float glitch = step(0.86, n) * 0.3;

      float glow = fresnel * u_glowStrength;
      glow += grid * 0.4;
      glow += scan * 0.22;
      glow += glitch;

      vec3 coreColor = vec3(0.02, 0.95, 0.8);
      vec3 edgeColor = vec3(0.0, 1.0, 1.0);
      vec3 color = mix(coreColor, edgeColor, glow);

      float alpha = clamp(0.25 + glow * u_intensity, 0.25, 1.0);
      gl_FragColor = vec4(color, alpha);
    }
  `;

  const coreMaterial = new THREE.ShaderMaterial({
    vertexShader: coreVertex,
    fragmentShader: coreFragment,
    uniforms: coreUniforms,
    transparent: true
  });

  const coreGlobe = new THREE.Mesh(
    new THREE.SphereGeometry(globeRadius, 64, 64),
    coreMaterial
  );
  scene.add(coreGlobe);

  // =========================
  // 4. NEON BREATHING GRID
  // =========================
  const gridUniforms = {
    u_time: { value: 0 },
    u_breathe: { value: 1.0 }
  };

  const gridVertex = `
    uniform float u_time;
    varying vec3 vPos;
    varying vec3 vNormal;

    float hash(vec3 p) {
      return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453123);
    }

    float noise(vec3 p) {
      vec3 i = floor(p);
      vec3 f = fract(p);
      float a = hash(i);
      float b = hash(i + vec3(1.0, 0.0, 0.0));
      float c = hash(i + vec3(0.0, 1.0, 0.0));
      float d = hash(i + vec3(1.0, 1.0, 0.0));
      float e = hash(i + vec3(0.0, 0.0, 1.0));
      float f2 = hash(i + vec3(1.0, 0.0, 1.0));
      float g = hash(i + vec3(0.0, 1.0, 1.0));
      float h = hash(i + vec3(1.0, 1.0, 1.0));
      vec3 u = f * f * (3.0 - 2.0 * f);
      return mix(mix(mix(a, b, u.x), mix(c, d, u.x), u.y),
                 mix(mix(e, f2, u.x), mix(g, h, u.x), u.y),
                 u.z);
    }

    void main() {
      float wobble = (sin(u_time * 0.6 + position.y * 0.02) * 3.0);
      float n = noise(normalize(position) * 1.8 + u_time * 0.4) * 3.5;
      vec3 displaced = position + normalize(position) * (wobble + n) * 0.003;
      vPos = displaced;
      vNormal = normalize(normalMatrix * normal);
      gl_Position = projectionMatrix * modelViewMatrix * vec4(displaced, 1.0);
    }
  `;

  const gridFragment = `
    uniform float u_time;
    uniform float u_breathe;
    varying vec3 vPos;
    varying vec3 vNormal;

    void main() {
      vec3 viewDir = normalize(cameraPosition - vPos);
      float fresnel = pow(1.0 - max(dot(viewDir, vNormal), 0.0), 3.0);
      float lat = abs(sin(vPos.y * 0.04));
      float lon = abs(sin(atan(vPos.z, vPos.x) * 6.0));
      float grid = smoothstep(0.85, 0.98, lat) + smoothstep(0.85, 0.98, lon);

      float breathe = 0.65 + 0.35 * sin(u_time * 1.4);
      float glow = (grid * breathe + fresnel * 0.5);
      vec3 color = mix(vec3(0.0, 0.5, 0.55), vec3(0.0, 0.94, 1.0), glow);
      float alpha = clamp(0.15 + glow * u_breathe, 0.15, 0.65);

      gl_FragColor = vec4(color, alpha);
    }
  `;

  const gridSphere = new THREE.Mesh(
    new THREE.SphereGeometry(globeRadius * 1.01, 64, 64),
    new THREE.ShaderMaterial({
      uniforms: gridUniforms,
      vertexShader: gridVertex,
      fragmentShader: gridFragment,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    })
  );
  scene.add(gridSphere);

  // =========================
  // 5. HOLOGRAM SHELL + AURA
  // =========================
  const shell = new THREE.Mesh(
    new THREE.SphereGeometry(globeRadius * 1.06, 64, 64),
    new THREE.MeshBasicMaterial({
      color: 0x36e27b,
      transparent: true,
      opacity: 0.16,
      side: THREE.BackSide
    })
  );
  scene.add(shell);

  const aura = new THREE.Mesh(
    new THREE.SphereGeometry(globeRadius * 1.05, 32, 32),
    new THREE.MeshBasicMaterial({
      color: 0xff3366,
      transparent: true,
      opacity: 0.08,
      depthWrite: false
    })
  );
  scene.add(aura);

  // =========================
  // 6. AI ORBIT PARTICLES
  // =========================
  const particleCount = 160;
  const orbitPositions = new Float32Array(particleCount * 3);
  const orbitRadii = new Float32Array(particleCount);
  const orbitSpeeds = new Float32Array(particleCount);
  const orbitInclinations = new Float32Array(particleCount);
  const orbitPhases = new Float32Array(particleCount);

  for (let i = 0; i < particleCount; i++) {
    orbitRadii[i] = globeRadius * (1.12 + Math.random() * 0.15);
    orbitSpeeds[i] = 0.18 + Math.random() * 0.35;
    orbitInclinations[i] = (Math.random() - 0.5) * 0.6;
    orbitPhases[i] = Math.random() * Math.PI * 2;
  }

  const orbitGeo = new THREE.BufferGeometry();
  orbitGeo.setAttribute("position", new THREE.BufferAttribute(orbitPositions, 3));

  const orbitMat = new THREE.PointsMaterial({
    color: 0x00fff7,
    size: Math.max(globeRadius * 0.004, 1.6),
    transparent: true,
    opacity: 0.9,
    depthWrite: false
  });

  const orbitPoints = new THREE.Points(orbitGeo, orbitMat);
  orbitPoints.matrixAutoUpdate = true;
  scene.add(orbitPoints);

  // =========================
  // 7. CRITICAL POINTS
  // =========================
  const criticalPoints = [];
  const criticalCount = THREE.MathUtils.randInt(3, 7);

  const spawnCriticalPoint = () => {
    const mesh = new THREE.Mesh(
      new THREE.SphereGeometry(4, 16, 16),
      new THREE.MeshBasicMaterial({ color: 0xff3366, transparent: true, opacity: 0.9 })
    );
    const dir = new THREE.Vector3().randomDirection();
    mesh.userData.dir = dir.clone();
    mesh.position.copy(dir.multiplyScalar(globeRadius * 1.02));
    mesh.userData.baseScale = 1;
    scene.add(mesh);
    return mesh;
  };

  for (let i = 0; i < criticalCount; i++) {
    criticalPoints.push(spawnCriticalPoint());
  }

  // =========================
  // 8. POST-PROCESSING PIPELINE
  // =========================
  const composer = new EffectComposer(renderer);
  const renderPass = new RenderPass(scene, camera);
  const bloomPass = new UnrealBloomPass(new THREE.Vector2(width, height), 0.8, 0.4, 0.85);
  composer.addPass(renderPass);
  composer.addPass(bloomPass);

  // =========================
  // 9. RESIZE + REBUILD
  // =========================
  const resizeParts = () => {
    ({ width, height } = getSize());
    renderer.setSize(width, height, false);
    camera.aspect = width / Math.max(height, 1);
    camera.far = globeRadius * 12;
    camera.updateProjectionMatrix();
    composer.setSize(width, height);
    bloomPass.setSize(width, height);
  };

  const rebuildGeometry = () => {
    coreGlobe.geometry.dispose();
    coreGlobe.geometry = new THREE.SphereGeometry(globeRadius, 64, 64);

    gridSphere.geometry.dispose();
    gridSphere.geometry = new THREE.SphereGeometry(globeRadius * 1.01, 64, 64);

    shell.geometry.dispose();
    shell.geometry = new THREE.SphereGeometry(globeRadius * 1.06, 64, 64);

    aura.geometry.dispose();
    aura.geometry = new THREE.SphereGeometry(globeRadius * 1.05, 32, 32);

    for (const point of criticalPoints) {
      const dir = point.userData.dir.clone().normalize();
      point.position.copy(dir.multiplyScalar(globeRadius * 1.02));
    }

    for (let i = 0; i < particleCount; i++) {
      orbitRadii[i] = globeRadius * (1.12 + Math.random() * 0.15);
    }
    orbitMat.size = Math.max(globeRadius * 0.004, 1.6);
  };

  const debounce = (fn, delay) => {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), delay);
    };
  };

  const handleResize = debounce(() => {
    const nextRadius = window.innerWidth * 0.28;
    if (Math.abs(nextRadius - globeRadius) > 1) {
      globeRadius = nextRadius;
      rebuildGeometry();
    }
    resizeParts();
  }, 200);

  resizeParts();

  // =========================
  // 10. ANIMATION LOOP
  // =========================
  const clock = new THREE.Clock();
  let frames = 0;
  let lastFpsCheck = performance.now();
  let polyReduced = false;

  const updateOrbits = (dt, elapsed) => {
    for (let i = 0; i < particleCount; i++) {
      orbitPhases[i] += orbitSpeeds[i] * dt;
      const theta = orbitPhases[i];
      const yTilt = Math.sin(theta * 0.6 + orbitInclinations[i]) * 0.4;
      const r = orbitRadii[i];
      const x = Math.cos(theta) * r;
      const y = Math.sin(yTilt) * r * 0.35;
      const z = Math.sin(theta) * r;
      orbitPositions[i * 3] = x;
      orbitPositions[i * 3 + 1] = y;
      orbitPositions[i * 3 + 2] = z;
    }
    orbitGeo.attributes.position.needsUpdate = true;
    orbitPoints.rotation.y = Math.sin(elapsed * 0.2) * 0.08;
  };

  const tick = () => {
    const dt = clock.getDelta();
    const elapsed = clock.getElapsedTime();

    coreUniforms.u_time.value = elapsed;
    gridUniforms.u_time.value = elapsed;
    gridUniforms.u_breathe.value = 0.9 + 0.1 * Math.sin(elapsed * 0.8);

    coreGlobe.rotation.y += 0.06 * dt;
    gridSphere.rotation.y += 0.12 * dt;
    shell.rotation.y -= 0.025 * dt;

    aura.scale.setScalar(1.02 + Math.sin(elapsed * 0.45) * 0.05);
    aura.material.opacity = 0.06 + (Math.sin(elapsed * 0.5) * 0.5 + 0.5) * 0.04;

    criticalPoints.forEach((p, idx) => {
      const pulse = 1 + Math.sin(elapsed * 0.5 + idx) * 0.2;
      p.scale.setScalar(p.userData.baseScale * pulse);
    });

    updateOrbits(dt, elapsed);

    controls.update();
    composer.render();

    frames += 1;
    const now = performance.now();
    if (now - lastFpsCheck > 1200) {
      const fps = (frames * 1000) / (now - lastFpsCheck);
      if (fps < 50 && !polyReduced) {
        polyReduced = true;
        gridSphere.geometry.dispose();
        gridSphere.geometry = new THREE.SphereGeometry(globeRadius * 1.01, 48, 48);
        coreGlobe.geometry.dispose();
        coreGlobe.geometry = new THREE.SphereGeometry(globeRadius, 48, 48);
        shell.geometry.dispose();
        shell.geometry = new THREE.SphereGeometry(globeRadius * 1.06, 48, 48);
        orbitGeo.setDrawRange(0, Math.floor(particleCount * 0.7));
        console.info("[RISKCAST] Performance guard: reduced poly for FPS stability.");
      }
      frames = 0;
      lastFpsCheck = now;
    }

    requestAnimationFrame(tick);
  };

  tick();
  window.addEventListener("resize", handleResize);

  console.log(
    "🚀 FutureOS Globe v2200 Ready\n- Imports fixed\n- Composer active\n- Neon grid shader initialized\n- Critical Points: OK\n- Aura Danger: OK"
  );
})();

