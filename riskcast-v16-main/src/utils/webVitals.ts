/**
 * Web Vitals Monitoring (Phase 5 - Day 15)
 * 
 * CRITICAL: Monitor Core Web Vitals for performance optimization
 * - LCP (Largest Contentful Paint) - target: <2.5s
 * - FID (First Input Delay) - target: <100ms
 * - CLS (Cumulative Layout Shift) - target: <0.1
 */

/**
 * Report Web Vital metric
 */
export function reportWebVital(metric: {
  name: string;
  value: number;
  id: string;
  delta: number;
  entries: PerformanceEntry[];
}) {
  // Suppress verbose logging in development to reduce console noise
  // Only log in development if explicitly enabled via environment variable
  if (import.meta.env.MODE === 'development' && import.meta.env.VITE_DEBUG_WEB_VITALS === 'true') {
    console.log(`[Web Vital] ${metric.name}: ${metric.value.toFixed(2)}`);
  }
  
  // In production, send to analytics
  // Example: sendToAnalytics(metric.name, metric.value);
  
  // Check thresholds
  const thresholds: Record<string, { good: number; needsImprovement: number }> = {
    LCP: { good: 2500, needsImprovement: 4000 },
    FID: { good: 100, needsImprovement: 300 },
    CLS: { good: 0.1, needsImprovement: 0.25 },
    FCP: { good: 1800, needsImprovement: 3000 },
    TTFB: { good: 800, needsImprovement: 1800 },
  };
  
  const threshold = thresholds[metric.name];
  if (threshold) {
    // In development, suppress most performance warnings to reduce noise
    // This is especially important when server is slow or network is unstable
    const isDevelopment = import.meta.env.MODE === 'development';
    
    // In development, only warn for extremely poor performance (5x threshold)
    // This prevents console spam during development when server/network is slow
    if (isDevelopment) {
      // Only warn if performance is extremely poor (likely a real issue, not just slow server)
      if (metric.value > threshold.needsImprovement * 5) {
        console.warn(
          `[Performance] ${metric.name} is extremely poor: ${metric.value.toFixed(2)}ms (target: <${threshold.good}ms). ` +
          `This may indicate a real performance issue.`
        );
      }
      // Suppress all other warnings in development
      return;
    }
    
    // In production, show warnings for poor performance
    if (metric.value > threshold.needsImprovement) {
      console.warn(`[Performance] ${metric.name} is poor: ${metric.value.toFixed(2)} (target: <${threshold.good})`);
    } else if (metric.value > threshold.good) {
      console.warn(`[Performance] ${metric.name} needs improvement: ${metric.value.toFixed(2)} (target: <${threshold.good})`);
    }
  }
}

/**
 * Initialize Web Vitals monitoring
 * 
 * Call this in App.tsx or main entry point
 */
export function initWebVitals() {
  // Only load web-vitals in browser
  if (typeof window === 'undefined') return;
  
  // Dynamically import web-vitals library
  import('web-vitals').then(({ onCLS, onFID, onLCP, onFCP, onTTFB }) => {
    onCLS(reportWebVital);
    onFID(reportWebVital);
    onLCP(reportWebVital);
    onFCP(reportWebVital);
    onTTFB(reportWebVital);
  }).catch((error) => {
    console.warn('[Web Vitals] Failed to load web-vitals library:', error);
  });
}
