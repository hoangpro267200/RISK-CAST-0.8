import { useEffect, useRef, useState, RefObject } from 'react';

export interface ContainerSize {
  width: number;
  height: number;
  ready: boolean;
}

/**
 * Hook to track container dimensions using ResizeObserver.
 * Only returns ready=true when width > 0 and height > 0.
 * Automatically handles resize events and visibility changes.
 */
export function useContainerSize<T extends HTMLElement = HTMLDivElement>(
  enabled = true
): [RefObject<T>, ContainerSize] {
  const ref = useRef<T>(null);
  const [size, setSize] = useState<ContainerSize>({
    width: 0,
    height: 0,
    ready: false,
  });

  useEffect(() => {
    if (!enabled) {
      setSize({ width: 0, height: 0, ready: false });
      return;
    }

    const element = ref.current;
    if (!element) {
      setSize({ width: 0, height: 0, ready: false });
      return;
    }

    // Initial measurement
    const updateSize = () => {
      const rect = element.getBoundingClientRect();
      const width = Math.max(0, Math.floor(rect.width));
      const height = Math.max(0, Math.floor(rect.height));
      const ready = width > 0 && height > 0;

      setSize({ width, height, ready });
    };

    // Initial check
    updateSize();

    // Use ResizeObserver for efficient size tracking
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.target === element) {
          updateSize();
          break;
        }
      }
    });

    resizeObserver.observe(element);

    // Use IntersectionObserver to detect when element becomes visible (e.g., tab switches)
    const intersectionObserver = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.target === element && entry.isIntersecting) {
            // Element became visible, update size after layout settles
            requestAnimationFrame(() => {
              requestAnimationFrame(updateSize);
            });
          }
        }
      },
      { threshold: 0.01 } // Trigger when any part becomes visible
    );

    intersectionObserver.observe(element);

    // Also listen for document visibility changes (e.g., browser tab switches)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        // Delay slightly to allow layout to settle after becoming visible
        requestAnimationFrame(() => {
          requestAnimationFrame(updateSize);
        });
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      resizeObserver.disconnect();
      intersectionObserver.disconnect();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [enabled]);

  return [ref, size];
}

