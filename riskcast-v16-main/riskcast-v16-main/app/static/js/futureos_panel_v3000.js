/**
 * FutureOS Panel v3000 - Subtle Tilt Effect
 * Optional: Adds subtle 3D tilt based on mouse position
 */

(function() {
  const panel = document.querySelector('.futureos-panel-container');
  
  if (!panel) return;

  let isHovering = false;
  const maxTilt = 2; // degrees
  const maxTranslate = 3; // pixels

  panel.addEventListener('mouseenter', () => {
    isHovering = true;
  });

  panel.addEventListener('mouseleave', () => {
    isHovering = false;
    // Reset to base transform
    panel.style.transform = 'rotateX(3deg) rotateY(0deg) translateY(0px)';
  });

  panel.addEventListener('mousemove', (e) => {
    if (!isHovering) return;

    const rect = panel.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    // Calculate mouse position relative to center (-1 to 1)
    const mouseX = (e.clientX - centerX) / (rect.width / 2);
    const mouseY = (e.clientY - centerY) / (rect.height / 2);

    // Calculate tilt (subtle)
    const tiltY = mouseX * maxTilt;
    const tiltX = -mouseY * maxTilt * 0.5; // Less vertical tilt
    const translateY = -mouseY * maxTranslate * 0.3;

    // Apply transform
    panel.style.transform = `
      rotateX(${3 + tiltX}deg) 
      rotateY(${tiltY}deg) 
      translateY(${translateY}px)
    `;

    // Subtle glow intensity based on mouse position
    const glowIntensity = 0.04 + Math.abs(mouseX) * 0.03;
    panel.style.boxShadow = `
      0 20px 60px rgba(0, 0, 0, 0.6),
      inset 0 0 40px rgba(0, 255, 255, ${glowIntensity}),
      inset 0 1px 0 rgba(255, 255, 255, 0.05)
    `;
  });

  // Smooth transition when mouse leaves
  panel.style.transition = 'transform 0.3s ease-out, box-shadow 0.3s ease-out';
})();





