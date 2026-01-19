import { captureMessage } from '../services/errorTracking';

export type MonitoringEvent =
  | {
      type: 'web-vital';
      name: string;
      value: number;
      id?: string;
      rating?: 'good' | 'needs-improvement' | 'poor';
      delta?: number;
      navigationType?: string;
      context?: Record<string, unknown>;
      timestamp: number;
    }
  | {
      type: 'metric';
      name: string;
      value: number;
      unit?: 'ms' | 'count' | 'score' | 'ratio';
      context?: Record<string, unknown>;
      timestamp: number;
    };

export type MonitoringReporter = (event: MonitoringEvent) => void;

let reporter: MonitoringReporter | null = null;

export function setMonitoringReporter(next: MonitoringReporter): void {
  reporter = next;
}

export function getMonitoringReporter(): MonitoringReporter {
  return (
    reporter ??
    ((event) => {
      const mode = (import.meta as unknown as { env?: { MODE?: string } }).env?.MODE;
      if (mode === 'development' || mode === 'test') {
        console.info('[monitoring]', event);
      }
    })
  );
}

const SLOW_THRESHOLDS_MS: Record<string, number> = {
  chart_render_time: 500,
  trace_drawer_open_time: 100,
  analyst_view_first_paint: 500,
};

export function trackMetric(
  name: string,
  value: number,
  context?: Record<string, unknown>,
  unit: 'ms' | 'count' | 'score' | 'ratio' = 'ms'
): void {
  const evt: MonitoringEvent = {
    type: 'metric',
    name,
    value,
    unit,
    context,
    timestamp: Date.now(),
  };

  getMonitoringReporter()(evt);

  const threshold = SLOW_THRESHOLDS_MS[name];
  if (threshold !== undefined && value > threshold) {
    captureMessage(`Slow metric: ${name} (${Math.round(value)}ms > ${threshold}ms)`, 'warning', {
      name,
      value,
      threshold,
      ...context,
    });
  }
}

export function measureMetric(
  name: string,
  context?: Record<string, unknown>,
  unit: 'ms' | 'count' | 'score' | 'ratio' = 'ms'
) {
  const start = performance.now();
  return () => {
    const end = performance.now();
    trackMetric(name, end - start, context, unit);
  };
}

export async function initWebVitals(context?: Record<string, unknown>): Promise<void> {
  try {
    const mod = await import('web-vitals');
    const report = (m: {
      name: string;
      value: number;
      id?: string;
      rating?: 'good' | 'needs-improvement' | 'poor';
      delta?: number;
      navigationType?: string;
    }) => {
      const evt: MonitoringEvent = {
        type: 'web-vital',
        name: m.name,
        value: m.value,
        id: m.id,
        rating: m.rating,
        delta: m.delta,
        navigationType: m.navigationType,
        context,
        timestamp: Date.now(),
      };
      getMonitoringReporter()(evt);
    };

    mod.onCLS(report);
    mod.onFCP(report);
    mod.onFID(report);
    mod.onINP(report);
    mod.onLCP(report);
    mod.onTTFB(report);
  } catch (e) {
    captureMessage('initWebVitals failed', 'warning', { error: String(e) });
  }
}

export function initLongTaskObserver(context?: Record<string, unknown>): void {
  try {
    if (!('PerformanceObserver' in window)) return;

    let lastReport = 0;
    const THROTTLE_MS = 5000;

    const observer = new PerformanceObserver((list) => {
      const now = Date.now();
      if (now - lastReport < THROTTLE_MS) return;
      lastReport = now;

      for (const entry of list.getEntries()) {
        trackMetric('long_task', entry.duration, { entryType: entry.entryType, name: entry.name, ...context }, 'ms');
        break;
      }
    });

    observer.observe({ entryTypes: ['longtask'] as any });
  } catch {
    // Ignore
  }
}

