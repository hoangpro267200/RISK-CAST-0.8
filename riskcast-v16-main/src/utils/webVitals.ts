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
  // Log in development
  if (process.env.NODE_ENV === 'development') {
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
