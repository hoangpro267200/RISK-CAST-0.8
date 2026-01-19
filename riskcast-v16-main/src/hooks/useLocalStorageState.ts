import { useCallback, useEffect, useMemo, useState } from 'react';

type Validator<T> = (value: unknown) => value is T;

type Options<T> = {
  serialize?: (value: T) => string;
  deserialize?: (raw: string) => unknown;
  validate?: Validator<T>;
};

function safeLocalStorageGet(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeLocalStorageSet(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // ignore
  }
}

function safeLocalStorageRemove(key: string): void {
  try {
    window.localStorage.removeItem(key);
  } catch {
    // ignore
  }
}

export function useLocalStorageState<T>(key: string, initialValue: T, options?: Options<T>) {
  const serialize = useMemo(() => options?.serialize ?? ((v: T) => JSON.stringify(v)), [options?.serialize]);
  const deserialize = useMemo(
    () => options?.deserialize ?? ((raw: string) => JSON.parse(raw) as unknown),
    [options?.deserialize]
  );
  const validate = options?.validate;

  const read = useCallback((): T => {
    if (typeof window === 'undefined') return initialValue;

    const raw = safeLocalStorageGet(key);
    if (raw === null) return initialValue;

    let parsed: unknown;
    try {
      parsed = deserialize(raw);
    } catch {
      parsed = raw;
    }

    if (validate && !validate(parsed)) return initialValue;
    return parsed as T;
  }, [deserialize, initialValue, key, validate]);

  const [value, setValueInternal] = useState<T>(() => read());

  const setValue = useCallback(
    (next: T) => {
      setValueInternal(next);
      safeLocalStorageSet(key, serialize(next));
    },
    [key, serialize]
  );

  const remove = useCallback(() => {
    safeLocalStorageRemove(key);
    setValueInternal(initialValue);
  }, [initialValue, key]);

  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key !== key) return;
      setValueInternal(read());
    };

    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, [key, read]);

  return [value, setValue, remove] as const;
}

