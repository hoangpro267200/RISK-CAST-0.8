import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeAll, vi } from 'vitest';

afterEach(() => {
  cleanup();
  
  // CRITICAL: Clear localStorage to prevent cross-test pollution
  try {
    window.localStorage.clear();
  } catch {
    // ignore (private mode)
  }
});

beforeAll(() => {
  // matchMedia polyfill
  if (!window.matchMedia) {
    window.matchMedia = (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(() => false),
    });
  }

  // ResizeObserver polyfill
  if (!('ResizeObserver' in window)) {
    class MockResizeObserver {
      observe(_target: Element) {}
      unobserve(_target: Element) {}
      disconnect() {}
    }
    (window as any).ResizeObserver = MockResizeObserver;
  }

  // IntersectionObserver polyfill (deterministic)
  if (!('IntersectionObserver' in window)) {
    class MockIntersectionObserver implements IntersectionObserver {
      readonly root: Element | Document | null;
      readonly rootMargin: string;
      readonly thresholds: ReadonlyArray<number>;
      private readonly callback: IntersectionObserverCallback;

      constructor(callback: IntersectionObserverCallback, options?: IntersectionObserverInit) {
        this.callback = callback;
        this.root = options?.root ?? null;
        this.rootMargin = options?.rootMargin ?? '0px';
        const t = options?.threshold;
        this.thresholds = Array.isArray(t) ? t : [t ?? 0];
      }

      observe(target: Element): void {
        queueMicrotask(() => {
          const rect = target.getBoundingClientRect();
          const entry = {
            boundingClientRect: rect,
            intersectionRatio: 1,
            intersectionRect: rect,
            isIntersecting: true,
            rootBounds: null,
            target,
            time: Date.now(),
          } satisfies IntersectionObserverEntry;
          this.callback([entry], this);
        });
      }

      unobserve(_target: Element): void {}
      disconnect(): void {}
      takeRecords(): IntersectionObserverEntry[] {
        return [];
      }
    }
    (window as any).IntersectionObserver = MockIntersectionObserver;
  }

  // requestAnimationFrame polyfill
  if (!('requestAnimationFrame' in window)) {
    vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) =>
      window.setTimeout(() => cb(Date.now()), 0)
    );
  }
  if (!('cancelAnimationFrame' in window)) {
    vi.stubGlobal('cancelAnimationFrame', (id: number) => window.clearTimeout(id));
  }

  // DOM no-ops
  if (!('scrollTo' in window)) {
    (window as any).scrollTo = vi.fn();
  }
  if (!HTMLElement.prototype.scrollIntoView) {
    (HTMLElement.prototype as any).scrollIntoView = vi.fn();
  }
});

