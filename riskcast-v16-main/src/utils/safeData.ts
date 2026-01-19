export function safeNumber(value: unknown, fallback = 0): number {
  const n = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(n) ? n : fallback;
}

export function safeString(value: unknown, fallback = ''): string {
  if (typeof value === 'string') return value;
  if (value === null || value === undefined) return fallback;
  return String(value);
}

export function safeArray<T>(value: unknown, fallback: T[] = []): T[] {
  return Array.isArray(value) ? (value as T[]) : fallback;
}

export function clampNumber(n: number, min: number, max: number): number {
  if (!Number.isFinite(n)) return min;
  return Math.min(max, Math.max(min, n));
}

export function safeFiniteNumber(value: unknown): number | null {
  const n = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(n) ? n : null;
}

export function safeOptionalNumber(value: unknown): number | undefined {
  const n = safeFiniteNumber(value);
  return n === null ? undefined : n;
}

export function safeRatio01(value: unknown, fallback = 0): number {
  const n = safeNumber(value, fallback);
  return clampNumber(n, 0, 1);
}

export function safePercent100(value: unknown, fallback = 0): number {
  const n = safeNumber(value, fallback);
  return clampNumber(n, 0, 100);
}




