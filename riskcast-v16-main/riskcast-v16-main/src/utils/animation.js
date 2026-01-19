/**
 * RiskCast V22 - Animation Utilities
 * ===================================
 * Reusable animation configurations and helpers
 * 
 * Spring ease: cubic-bezier(.22, 1.2, .36, 1)
 */

export const springEase = 'cubic-bezier(.22, 1.2, .36, 1)';
export const smoothEase = 'cubic-bezier(0.4, 0, 0.2, 1)';

export const fadeInStagger = (index, baseDelay = 0) => ({
  style: {
    animation: `fadeInUp 0.6s ${springEase} ${baseDelay + index * 0.1}s both`
  }
});

export const scaleIn = (delay = 0) => ({
  style: {
    animation: `scaleIn 0.5s ${springEase} ${delay}s both`
  }
});

export const slideInLeft = (delay = 0) => ({
  style: {
    animation: `slideInLeft 0.6s ${smoothEase} ${delay}s both`
  }
});

export const neonPulse = {
  animation: 'neonPulse 2s ease-in-out infinite'
};

// CSS keyframes to be added to global styles
export const keyframesCSS = `
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes neonPulse {
  0%, 100% {
    box-shadow: 0 0 20px rgba(79, 195, 247, 0.4), 0 0 40px rgba(79, 195, 247, 0.2);
  }
  50% {
    box-shadow: 0 0 30px rgba(79, 195, 247, 0.6), 0 0 60px rgba(79, 195, 247, 0.3);
  }
}
`;

export const hoverGlow = (color = '#4FC3F7') => ({
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  '&:hover': {
    boxShadow: `0 0 20px rgba(79, 195, 247, 0.4), 0 0 40px rgba(79, 195, 247, 0.2)`,
    transform: 'translateY(-2px)'
  }
});






