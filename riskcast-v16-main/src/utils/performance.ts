/**
 * Performance Utilities (Phase 5)
 * 
 * CRITICAL: Web Vitals monitoring and performance optimization helpers
 */

/**
 * Report Web Vitals to analytics
 * 
 * Measures:
 * - LCP (Largest Contentful Paint) - should be <2.5s
 * - FID (First Input Delay) - should be <100ms
 * - CLS (Cumulative Layout Shift) - should be <0.1
 */
export function reportWebVitals(metric: {
  name: string;
  value: number;
  id: string;
  delta: number;
  entries: PerformanceEntry[];
}) {
  // In production, send to analytics service
  if (process.env.NODE_ENV === 'production') {
    // Example: send to analytics
    // analytics.track('web_vital', {
    //   name: metric.name,
    //   value: metric.value,
    //   id: metric.id,
    // });
  } else {
    // In development, log to console
    console.log('[Web Vital]', metric.name, ':', metric.value.toFixed(2));
  }
}

/**
 * Lazy load component with error boundary
 * Note: This requires React import, but we avoid it here to keep utils lightweight
 * Use React.lazy directly in components instead
 */

/**
 * Preload component for faster navigation
 */
export function preloadComponent(importFn: () => Promise<any>): void {
  // Preload on hover or after initial load
  if (typeof window !== 'undefined') {
    setTimeout(() => {
      importFn().catch(() => {
        // Silently fail preload
      });
    }, 2000); // Preload after 2s
  }
}

/**
 * Measure component render time
 */
export function measureRenderTime(componentName: string): () => void {
  const start = performance.now();
  
  return () => {
    const end = performance.now();
    const duration = end - start;
    
    if (duration > 100) {
      console.warn(`[Performance] ${componentName} took ${duration.toFixed(2)}ms to render`);
    }
    
    // Report to analytics if needed
    if (process.env.NODE_ENV === 'production' && duration > 200) {
      // Report slow renders
    }
  };
}
