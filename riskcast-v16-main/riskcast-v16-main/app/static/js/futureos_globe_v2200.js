import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.161.0/build/three.module.js";
import { OrbitControls } from "https://cdn.jsdelivr.net/npm/three@0.161.0/examples/jsm/controls/OrbitControls.js";
import { EffectComposer } from "https://cdn.jsdelivr.net/npm/three@0.161.0/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "https://cdn.jsdelivr.net/npm/three@0.161.0/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "https://cdn.jsdelivr.net/npm/three@0.161.0/examples/jsm/postprocessing/UnrealBloomPass.js";

function initGlobe() {
  const container = document.getElementById("globe-v2200");
  if (!container) {
    return console.error("globe container not found");
  }

  if (container.clientWidth === 0 || container.clientHeight === 0) {
    requestAnimationFrame(initGlobe);
    return;
  }

  const width = container.clientWidth;
  const height = container.clientHeight;

  const scene = new THREE.Scene();
  const radius = Math.min(width, height) * 0.4;
  const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 1000);
  // Camera: hơi nghiêng để thấy rõ continents (Africa/Europe/Americas)
  camera.position.set(radius * 2.2, radius * 1.8, radius * 3.2);
  camera.lookAt(0, 0, 0);

  // Lighting for planet shading - Sun simulation
  const ambientLight = new THREE.AmbientLight(0x4a90e2, 0.12); // Soft blue ambient
  scene.add(ambientLight);
  
  // Sun directional light (fixed position, Earth rotates under it)
  const sunLight = new THREE.DirectionalLight(0xffffff, 1.4);
  sunLight.position.set(radius * 5, radius * 3, radius * 5);
  sunLight.castShadow = false;
  scene.add(sunLight);
  
  // Rim light for depth (from camera side)
  const rimLight = new THREE.DirectionalLight(0x6bb6ff, 0.6);
  rimLight.position.set(-radius * 3, radius * 2, -radius * 4);
  scene.add(rimLight);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  renderer.setSize(width, height);
  container.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableZoom = false;

  // ResizeObserver
  new ResizeObserver(() => {
    const newWidth = container.clientWidth;
    const newHeight = container.clientHeight;
    renderer.setSize(newWidth, newHeight);
    camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
    
    // Maintain camera angle on resize
    const newRadius = Math.min(newWidth, newHeight) * 0.4;
    camera.position.set(newRadius * 2.2, newRadius * 1.8, newRadius * 3.2);
    camera.lookAt(0, 0, 0);
  }).observe(container);

  // Layer A: dark surface via dot field (no textures)
  function createDotEarth(r) {
    const group = new THREE.Group();
    const count = 16000;

    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
        const u = Math.random();
        const v = Math.random();
        const theta = u * 2 * Math.PI;
        const phi = Math.acos(2 * v - 1);
        const x = r * Math.sin(phi) * Math.cos(theta);
        const y = r * Math.cos(phi);
        const z = r * Math.sin(phi) * Math.sin(theta);
        positions[i * 3] = x;
        positions[i * 3 + 1] = y;
        positions[i * 3 + 2] = z;
    }

    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
        size: 1.0,
        color: 0x06181c,
        transparent: true,
        opacity: 0.9,
        depthWrite: false
    });

    const points = new THREE.Points(geometry, material);
    group.add(points);
    group.userData.material = material;
    return group;
  }

  // Earth grid (lat/long) with 23.5° tilt (Layer B)
  function createEarthGrid(r) {
    const group = new THREE.Group();
    const latLines = 16;
    const lonLines = 24;
    const latSegments = 128;

    // latitude rings
    for (let i = 1; i < latLines; i++) {
        const lat = (i / latLines) * Math.PI - Math.PI / 2;
        const ringR = Math.cos(lat) * r;
        const y = Math.sin(lat) * r;

        const positions = [];
        for (let s = 0; s <= latSegments; s++) {
            const theta = (s / latSegments) * Math.PI * 2;
            positions.push(
                ringR * Math.cos(theta),
                0,
                ringR * Math.sin(theta)
            );
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));

        const material = new THREE.LineBasicMaterial({
            color: 0x00faff,
            transparent: true,
            opacity: 0.18
        });

        const circle = new THREE.LineLoop(geometry, material);
        circle.rotation.x = Math.PI / 2;
        circle.position.y = y;
        group.add(circle);
    }

    // longitude lines
    for (let i = 0; i < lonLines; i++) {
        const lon = (i / lonLines) * Math.PI * 2;
        const points = [];
        for (let j = 0; j <= 64; j++) {
            const lat = (j / 64) * Math.PI - Math.PI / 2;
            const x = r * Math.cos(lat) * Math.cos(lon);
            const y = r * Math.sin(lat);
            const z = r * Math.cos(lat) * Math.sin(lon);
            points.push(new THREE.Vector3(x, y, z));
        }
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const material = new THREE.LineBasicMaterial({
            color: 0x00faff,
            transparent: true,
            opacity: 0.18
        });
        const line = new THREE.Line(geometry, material);
        group.add(line);
    }

    // earth axial tilt 23.5°
    group.rotation.z = THREE.MathUtils.degToRad(23.5);
    return group;
  }

  const earthGroup = new THREE.Group();
  scene.add(earthGroup);

  // Load Earth textures with fallback
  const textureLoader = new THREE.TextureLoader();
  
  // Create fallback procedural textures
  function createFallbackTexture(size = 512, color = 0x1a3a4a) {
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    
    // Create gradient background
    const gradient = ctx.createRadialGradient(size/2, size/2, 0, size/2, size/2, size/2);
    gradient.addColorStop(0, `rgba(${(color >> 16) & 0xff}, ${(color >> 8) & 0xff}, ${color & 0xff}, 1)`);
    gradient.addColorStop(1, `rgba(${((color >> 16) & 0xff) * 0.5}, ${((color >> 8) & 0xff) * 0.5}, ${(color & 0xff) * 0.5}, 1)`);
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, size, size);
    
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    return texture;
  }
  
  // Initialize with fallback textures
  const earthDayTexture = createFallbackTexture(512, 0x2a5a6a);
  const earthNightTexture = createFallbackTexture(512, 0x0a1a2a);

  // CORE: Real Earth sphere with day/night shader
  const earthGeometry = new THREE.SphereGeometry(radius * 0.96, 128, 64);
  
  // Earth shader material - blends day/night based on sun position
  const earthMaterial = new THREE.ShaderMaterial({
    uniforms: {
      dayTexture: { value: earthDayTexture },
      nightTexture: { value: earthNightTexture },
      sunDirection: { value: new THREE.Vector3(1, 0.5, 1).normalize() },
      ambientIntensity: { value: 0.12 },
      sunIntensity: { value: 1.4 },
      uCameraPosition: { value: camera.position }
    },
    vertexShader: `
      varying vec3 vWorldPosition;
      varying vec3 vNormal;
      varying vec2 vUv;
      varying vec3 vViewPosition;
      
      void main() {
        vWorldPosition = (modelMatrix * vec4(position, 1.0)).xyz;
        vNormal = normalize(normalMatrix * normal);
        vUv = uv;
        vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
        vViewPosition = -mvPosition.xyz;
        gl_Position = projectionMatrix * mvPosition;
      }
    `,
    fragmentShader: `
      uniform sampler2D dayTexture;
      uniform sampler2D nightTexture;
      uniform vec3 sunDirection;
      uniform vec3 uCameraPosition;
      uniform float ambientIntensity;
      uniform float sunIntensity;
      
      varying vec3 vWorldPosition;
      varying vec3 vNormal;
      varying vec2 vUv;
      varying vec3 vViewPosition;
      
      void main() {
        vec3 normal = normalize(vNormal);
        
        // Calculate sun lighting (dot product with normal)
        float sunDot = max(dot(normal, sunDirection), 0.0);
        
        // Day side (bright) vs night side (dark)
        float dayNightMix = smoothstep(-0.2, 0.3, sunDot);
        
        // Sample textures
        vec3 dayColor = texture2D(dayTexture, vUv).rgb;
        vec3 nightColor = texture2D(nightTexture, vUv).rgb;
        
        // Enhance continent brightness (continents are brighter in texture)
        float continentGlow = smoothstep(0.15, 0.4, dayColor.r);
        
        // Make continents brighter - TĂNG CƯỜNG GLOW
        dayColor += vec3(0.15, 0.18, 0.22) * continentGlow; // Tăng từ 0.08, 0.1, 0.12
        
        // Continent edge glow - MẠNH HƠN - WOW FACTOR
        vec2 texelSize = vec2(1.0 / 2048.0, 1.0 / 1024.0);
        float edge = abs(texture2D(dayTexture, vUv + vec2(texelSize.x, 0.0)).r - dayColor.r) +
                     abs(texture2D(dayTexture, vUv + vec2(0.0, texelSize.y)).r - dayColor.r);
        float edgeGlow = smoothstep(0.1, 0.3, edge) * 0.25; // Tăng từ 0.12 lên 0.25
        dayColor += vec3(0.3, 0.5, 0.6) * edgeGlow; // Tăng intensity của cyan glow
        
        // Blend day and night
        vec3 finalColor = mix(nightColor, dayColor, dayNightMix);
        
        // Add subtle lighting variation
        float lighting = ambientIntensity + sunDot * sunIntensity;
        finalColor *= lighting;
        
        // Rim light effect (for depth) - use view position from vertex shader
        vec3 viewDir = normalize(vViewPosition);
        float rim = pow(1.0 - max(dot(viewDir, normal), 0.0), 2.5);
        finalColor += vec3(0.15, 0.25, 0.35) * rim * 0.25;
        
        // Slight desaturation for cinematic look
        float gray = dot(finalColor, vec3(0.299, 0.587, 0.114));
        finalColor = mix(vec3(gray), finalColor, 0.88);
        
        gl_FragColor = vec4(finalColor, 1.0);
      }
    `,
    side: THREE.FrontSide,
    depthWrite: true
  });
  
  const coreSphere = new THREE.Mesh(earthGeometry, earthMaterial);
  earthGroup.add(coreSphere);
  
  // Store sun direction for animation
  const sunDirection = earthMaterial.uniforms.sunDirection.value;
  
  // Try to load real textures, replace fallback if successful
  textureLoader.load(
    'https://threejs.org/examples/textures/planets/earth_atmos_2048.jpg',
    (texture) => {
      console.log('[Globe] Earth day texture loaded');
      texture.colorSpace = THREE.SRGBColorSpace;
      earthMaterial.uniforms.dayTexture.value = texture;
      earthMaterial.needsUpdate = true;
    },
    undefined,
    (err) => {
      console.warn('[Globe] Failed to load Earth day texture, using fallback:', err);
    }
  );
  
  textureLoader.load(
    'https://threejs.org/examples/textures/planets/earth_night_2048.jpg',
    (texture) => {
      console.log('[Globe] Earth night texture loaded');
      texture.colorSpace = THREE.SRGBColorSpace;
      earthMaterial.uniforms.nightTexture.value = texture;
      earthMaterial.needsUpdate = true;
    },
    undefined,
    (err) => {
      console.warn('[Globe] Failed to load Earth night texture, using fallback:', err);
    }
  );

  // Layer B: grid - giảm opacity để clean hơn
  const latLonGrid = createEarthGrid(radius);
  // Giảm opacity của grid để không lộn xộn
  latLonGrid.traverse((obj) => {
    if (obj.material) {
      obj.material.opacity = 0.08; // Giảm từ 0.18 xuống 0.08
    }
  });
  earthGroup.add(latLonGrid);
  const gridMats = [];
  latLonGrid.traverse((obj) => {
    if (obj.material) gridMats.push(obj.material);
  });

  // ATMOSPHERE: Cinematic atmospheric glow (replaces old fresnel)
  const atmosphereGeometry = new THREE.SphereGeometry(radius * 1.02, 128, 64);
  const atmosphereMaterial = new THREE.ShaderMaterial({
    uniforms: {
      atmosphereColor: { value: new THREE.Color(0x4a90e2) }, // Subtle blue
      rimColor: { value: new THREE.Color(0x6bb6ff) }, // Cyan rim
      sunDirection: { value: sunDirection }
    },
        vertexShader: `
      varying vec3 vNormal;
      varying vec3 vViewPosition;
      
          void main() {
        vNormal = normalize(normalMatrix * normal);
        vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
        vViewPosition = -mvPosition.xyz;
        gl_Position = projectionMatrix * mvPosition;
          }
        `,
        fragmentShader: `
      uniform vec3 atmosphereColor;
      uniform vec3 rimColor;
      uniform vec3 sunDirection;
      
      varying vec3 vNormal;
      varying vec3 vViewPosition;
      
          void main() {
        vec3 normal = normalize(vNormal);
        vec3 viewDir = normalize(vViewPosition);
        
        // Fresnel effect (rim glow)
        float fresnel = pow(1.0 - max(dot(viewDir, normal), 0.0), 2.0);
        
        // Sun-facing glow
        float sunGlow = max(dot(normal, sunDirection), 0.0);
        
        // Combine atmosphere colors - TĂNG CƯỜNG GLOW
        vec3 color = mix(atmosphereColor, rimColor, fresnel * 0.8);
        color += rimColor * sunGlow * 0.5;
        color *= 1.3; // Tăng brightness
        
        // Tăng opacity để rõ hơn - WOW FACTOR
        float alpha = fresnel * 0.4 + sunGlow * 0.25;
        alpha = clamp(alpha, 0.0, 0.6); // Tăng max từ 0.4 lên 0.6
        
        gl_FragColor = vec4(color, alpha);
      }
    `,
    transparent: true,
    side: THREE.BackSide,
    depthWrite: false,
    blending: THREE.AdditiveBlending
  });
  
  const atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
  earthGroup.add(atmosphere);
  
  // Loại bỏ darkCore, aura để globe clean hơn

  // Warning points
  function addWarning(lat, lon) {
    const p = new THREE.Mesh(
        new THREE.SphereGeometry(4, 16, 16),
        new THREE.MeshBasicMaterial({ color: 0xff3366 })
    );

    const phi = (90 - lat) * Math.PI/180;
    const theta = (lon + 180) * Math.PI/180;

    p.position.set(
        radius * Math.sin(phi) * Math.cos(theta),
        radius * Math.cos(phi),
        radius * Math.sin(phi) * Math.sin(theta)
    );

    earthGroup.add(p);
  }

  addWarning(14, 108);
  addWarning(35, 139);
  addWarning(-33, 151);

  // Layer C: Network nodes (major ports/cities) - reduced count for performance
  const networkNodes = [];
  const nodePositions = [
    { lat: 40.7, lon: -74.0, name: 'NYC' },      // New York
    { lat: 51.5, lon: -0.1, name: 'London' },   // London
    { lat: 35.7, lon: 139.8, name: 'Tokyo' },   // Tokyo
    { lat: 1.3, lon: 103.8, name: 'Singapore' }, // Singapore
    { lat: 22.3, lon: 114.2, name: 'Hong Kong' }, // Hong Kong
    { lat: 31.2, lon: 121.5, name: 'Shanghai' }, // Shanghai
    { lat: -33.9, lon: 151.2, name: 'Sydney' },  // Sydney
    { lat: -23.5, lon: -46.6, name: 'Sao Paulo' }, // Sao Paulo
    { lat: 25.0, lon: 55.3, name: 'Dubai' },     // Dubai
    { lat: 19.1, lon: 72.9, name: 'Mumbai' },   // Mumbai
    { lat: 50.1, lon: 8.7, name: 'Frankfurt' },  // Frankfurt
    { lat: 52.5, lon: 13.4, name: 'Berlin' },   // Berlin
  ];
  
  function createNetworkNode(lat, lon, r) {
    const phi = (90 - lat) * Math.PI / 180;
    const theta = (lon + 180) * Math.PI / 180;
        const x = r * Math.sin(phi) * Math.cos(theta);
        const y = r * Math.cos(phi);
        const z = r * Math.sin(phi) * Math.sin(theta);
    
    // Network nodes - LỚN HƠN và SÁNG HƠN - WOW FACTOR
    const node = new THREE.Mesh(
      new THREE.SphereGeometry(3.5, 16, 16), // Tăng từ 2.5 lên 3.5, segments từ 12 lên 16
      new THREE.MeshBasicMaterial({ 
        color: 0x00f0ff,
        transparent: true,
        opacity: 1.0, // Tăng từ 0.9 lên 1.0
        emissive: 0x00f0ff, // Thêm emissive để sáng hơn
        emissiveIntensity: 0.8
      })
    );
    node.position.set(x, y, z);
    return { mesh: node, position: new THREE.Vector3(x, y, z) };
  }
  
  const networkGroup = new THREE.Group();
  nodePositions.forEach(node => {
    const nodeObj = createNetworkNode(node.lat, node.lon, radius * 1.005);
    networkNodes.push(nodeObj);
    networkGroup.add(nodeObj.mesh);
  });
  earthGroup.add(networkGroup);
  
  // Network arcs (great-circle paths connecting nodes)
  function createNetworkArc(startPos, endPos, r, color = 0x00f0ff) {
    const points = [];
    const segments = 48; // Reduced for performance
    
    // Normalize start and end positions
    const start = startPos.clone().normalize();
    const end = endPos.clone().normalize();
    
    // Great circle interpolation
    for (let i = 0; i <= segments; i++) {
      const t = i / segments;
      const angle = Math.acos(Math.max(-1, Math.min(1, start.dot(end))));
      const sinAngle = Math.sin(angle);
      
      let point;
      if (sinAngle < 0.001) {
        // Points are too close, use linear interpolation
        point = start.clone().lerp(end, t);
        point.normalize();
      } else {
        // Great circle path
        const a = Math.sin((1 - t) * angle) / sinAngle;
        const b = Math.sin(t * angle) / sinAngle;
        point = new THREE.Vector3();
        point.addScaledVector(start, a);
        point.addScaledVector(end, b);
        point.normalize();
      }
      
      // Arc elevation for visual appeal (curved above sphere)
      const elevation = 0.15 * Math.sin(t * Math.PI);
      point.multiplyScalar(r * (1.0 + elevation));
      points.push(point);
    }
    
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    
    // Network arc material with STRONG glow - WOW FACTOR
    const material = new THREE.LineBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0.75, // Tăng từ 0.5 lên 0.75 để sáng hơn
      linewidth: 2 // Tăng linewidth để rõ hơn
    });
    
    const line = new THREE.Line(geometry, material);
    
    // Add subtle glow effect via shader (optional enhancement)
    return line;
  }
  
  // Create network connections (selective, not all-to-all)
  const networkArcs = new THREE.Group();
  const connectionPairs = [
    [0, 1], [0, 2], [1, 2], [2, 3], [3, 4], [3, 5],
    [4, 5], [5, 6], [1, 10], [10, 11], [7, 8], [8, 9]
  ];
  
  connectionPairs.forEach(([i, j]) => {
    if (i < networkNodes.length && j < networkNodes.length) {
      const arc = createNetworkArc(
        networkNodes[i].position,
        networkNodes[j].position,
        radius,
        0x00f0ff
      );
      networkArcs.add(arc);
    }
  });
  earthGroup.add(networkArcs);
  
  // Store node materials for animation
  const nodeMats = [];
  networkGroup.traverse((obj) => {
    if (obj.material) nodeMats.push(obj.material);
  });

  // Loại bỏ halo, haze, depthRing để globe clean hơn - chỉ giữ atmosphere

  // Orbit particles - giảm số lượng để clean hơn
  const orbitCount = 80; // Giảm từ 140 xuống 80
  const orbitPositions = new Float32Array(orbitCount * 3);
  const orbitRadii = new Float32Array(orbitCount);
  const orbitAngles = new Float32Array(orbitCount);
  const orbitSpeeds = new Float32Array(orbitCount);

  for (let i = 0; i < orbitCount; i++) {
    orbitRadii[i] = radius * (1.08 + Math.random() * 0.08);
    orbitAngles[i] = Math.random() * Math.PI * 2;
    orbitSpeeds[i] = 0.0006 + Math.random() * 0.0014;
  }

  const orbitGeo = new THREE.BufferGeometry();
  orbitGeo.setAttribute("position", new THREE.BufferAttribute(orbitPositions, 3));
  const orbitMat = new THREE.PointsMaterial({
    color: 0x00f8ff,
    size: 1.4,
    transparent: true,
    opacity: 0.8,
    depthWrite: false
  });
  const orbitPoints = new THREE.Points(orbitGeo, orbitMat);
  scene.add(orbitPoints);

  // Bloom composer - TĂNG CƯỜNG BLOOM - WOW FACTOR
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  // Tăng bloom intensity để network lines và nodes sáng hơn
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(width, height), 1.2, 0.5, 1.0));

  function animate() {
    requestAnimationFrame(animate);
    earthGroup.rotation.y += 0.0009;
    coreSphere.rotation.y += 0.0008; // Core rotates with planet
    atmosphere.rotation.y += 0.0008; // Atmosphere rotates with Earth
    latLonGrid.rotation.y += 0.0008;
    networkGroup.rotation.y += 0.0008; // Network nodes rotate with Earth
    networkArcs.rotation.y += 0.0008; // Network arcs rotate with Earth
    
    // Update sun direction in shader (sun stays fixed, Earth rotates)
    // Sun direction rotates opposite to Earth rotation for day/night cycle
    const sunAngle = -earthGroup.rotation.y * 0.3; // Slower sun movement
    sunDirection.set(
      Math.cos(sunAngle) * 0.8,
      0.5,
      Math.sin(sunAngle) * 0.8
    ).normalize();
    
    // Update camera position in shader for rim light
    if (earthMaterial.uniforms) {
      earthMaterial.uniforms.uCameraPosition.value.copy(camera.position);
      earthMaterial.uniforms.sunDirection.value.copy(sunDirection);
    }
    
    // Update atmosphere shader sun direction
    if (atmosphereMaterial.uniforms) {
      atmosphereMaterial.uniforms.sunDirection.value.copy(sunDirection);
    }

    for (let i = 0; i < orbitCount; i++) {
      orbitAngles[i] += orbitSpeeds[i];
      const r = orbitRadii[i];
      const angle = orbitAngles[i];
      orbitPositions[i * 3] = Math.cos(angle) * r;
      orbitPositions[i * 3 + 1] = Math.sin(angle * 0.45) * r * 0.25;
      orbitPositions[i * 3 + 2] = Math.sin(angle) * r;
    }
    orbitGeo.attributes.position.needsUpdate = true;

    // Tăng cường pulsing - WOW FACTOR
    const t = performance.now() * 0.001;
    const pulse = 0.85 + Math.sin(t * 2.0) * 0.15; // Tăng amplitude
    
    // Network nodes pulse - MẠNH HƠN và ẤN TƯỢNG HƠN
    nodeMats.forEach((m, idx) => {
      const jitter = 0.15 * Math.sin(t * 2.5 + idx * 0.7); // Tăng jitter
      m.opacity = 0.9 + jitter; // Tăng base opacity
      // Thêm scale animation cho nodes
      const node = networkGroup.children[idx];
      if (node) {
        const scale = 1.0 + 0.1 * Math.sin(t * 2.0 + idx * 0.5);
        node.scale.set(scale, scale, scale);
      }
    });
    
    // Grid opacity - giữ ổn định, không pulse
    gridMats.forEach((m) => {
      m.opacity = 0.08; // Giữ opacity ổn định
    });

    controls.update();
    composer.render();
  }
  animate();
}

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", initGlobe);
