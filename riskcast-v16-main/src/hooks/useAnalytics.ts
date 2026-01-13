import { useCallback } from 'react';

export interface AnalyticsClient {
  track(event: string, properties?: Record<string, unknown>): void;
}

class NoopAnalytics implements AnalyticsClient {
  track(_event: string, _properties?: Record<string, unknown>): void {}
}

let analyticsClient: AnalyticsClient = new NoopAnalytics();

export function setAnalyticsClient(client: AnalyticsClient): void {
  analyticsClient = client;
}

export function getAnalyticsClient(): AnalyticsClient {
  return analyticsClient;
}

export function useAnalytics() {
  const trackEvent = useCallback((event: string, properties?: Record<string, unknown>) => {
    getAnalyticsClient().track(event, properties);
  }, []);

  const trackPageView = useCallback((view: 'executive' | 'analyst') => trackEvent('page_view', { view }), [trackEvent]);
  const trackLayerClick = useCallback((layerName: string) => trackEvent('layer_click', { layerName }), [trackEvent]);
  const trackDrawerOpen = useCallback((context: string) => trackEvent('drawer_open', { context }), [trackEvent]);

  return { trackEvent, trackPageView, trackLayerClick, trackDrawerOpen };
}

