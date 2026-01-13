import { useEffect, useMemo, useState } from 'react';

type Breakpoint = 'mobile' | 'tablet' | 'desktop';

function getBreakpoint(width: number): Breakpoint {
  if (width < 640) return 'mobile';
  if (width < 1024) return 'tablet';
  return 'desktop';
}

export function useResponsiveLayout() {
  const [width, setWidth] = useState<number>(() => (typeof window !== 'undefined' ? window.innerWidth : 1200));

  useEffect(() => {
    const onResize = () => setWidth(window.innerWidth);
    window.addEventListener('resize', onResize, { passive: true });
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const breakpoint = useMemo(() => getBreakpoint(width), [width]);

  const containerPadding = useMemo(() => {
    switch (breakpoint) {
      case 'mobile':
        return 'px-4';
      case 'tablet':
        return 'px-6';
      default:
        return 'px-10';
    }
  }, [breakpoint]);

  const chartHeight = useMemo(() => {
    switch (breakpoint) {
      case 'mobile':
        return 280;
      case 'tablet':
        return 340;
      default:
        return 420;
    }
  }, [breakpoint]);

  return { width, breakpoint, containerPadding, chartHeight };
}




