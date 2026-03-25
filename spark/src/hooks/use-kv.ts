/**
 * Local implementation of the @github/spark useKV hook.
 *
 * In the Spark runtime, `useKV` provides reactive persistent storage backed
 * by the platform's KV store.  For local development and testing, this
 * implementation uses an in-memory Map so the API surface is identical but
 * data does not survive a full page reload (which is acceptable for dev).
 *
 * When deployed to GitHub Spark, the Vite alias in vite.config.ts should
 * be removed so the real `@github/spark/hooks` module is resolved instead.
 */

import { useCallback, useRef, useSyncExternalStore } from "react";

type Updater<T> = T | ((prev: T) => T);

const store = new Map<string, unknown>();
const listeners = new Map<string, Set<() => void>>();

function getListeners(key: string): Set<() => void> {
  let set = listeners.get(key);
  if (!set) {
    set = new Set();
    listeners.set(key, set);
  }
  return set;
}

function notify(key: string) {
  const set = listeners.get(key);
  if (set) {
    set.forEach((fn) => fn());
  }
}

/**
 * Drop-in replacement for `@github/spark/hooks` useKV.
 *
 * Returns `[value, setValue, deleteValue]` -- the same tuple shape as the
 * Spark runtime hook.
 */
export function useKV<T>(
  key: string,
  defaultValue: T,
): [T, (update: Updater<T>) => void, () => void] {
  const defaultRef = useRef(defaultValue);

  const subscribe = useCallback(
    (callback: () => void) => {
      const set = getListeners(key);
      set.add(callback);
      return () => {
        set.delete(callback);
      };
    },
    [key],
  );

  const getSnapshot = useCallback((): T => {
    if (store.has(key)) {
      return store.get(key) as T;
    }
    return defaultRef.current;
  }, [key]);

  const value = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);

  const setValue = useCallback(
    (update: Updater<T>) => {
      const current = store.has(key) ? (store.get(key) as T) : defaultRef.current;
      const next = typeof update === "function" ? (update as (prev: T) => T)(current) : update;
      store.set(key, next);
      notify(key);
    },
    [key],
  );

  const deleteValue = useCallback(() => {
    store.delete(key);
    notify(key);
  }, [key]);

  return [value, setValue, deleteValue];
}

/** Reset all stored data. Useful for test teardown. */
export function _resetKVStore() {
  store.clear();
  listeners.clear();
}
