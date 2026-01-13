import { RefObject, useEffect, useState } from 'react';

export function useChartReady(ref: RefObject<HTMLElement>, enabled = true) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!enabled) {
      setReady(false);
      return;
    }

    let raf = 0;

    const tick = () => {
      const node = ref.current;
      if (!node) return;

      const { width, height } = node.getBoundingClientRect();
      if (width > 0 && height > 0) {
        setReady(true);
        return;
      }

      raf = requestAnimationFrame(tick);
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [ref, enabled]);

  return ready;
}

