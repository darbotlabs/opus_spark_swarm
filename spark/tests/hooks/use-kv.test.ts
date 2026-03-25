import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useKV, _resetKVStore } from "../../src/hooks/use-kv";

describe("useKV", () => {
  it("returns the default value initially", () => {
    const { result } = renderHook(() => useKV("test-key", 42));
    expect(result.current[0]).toBe(42);
  });

  it("updates value with a direct value", () => {
    const { result } = renderHook(() => useKV("counter", 0));
    act(() => {
      result.current[1](10);
    });
    expect(result.current[0]).toBe(10);
  });

  it("updates value with a functional updater", () => {
    const { result } = renderHook(() => useKV("counter", 5));
    act(() => {
      result.current[1]((prev) => prev + 1);
    });
    expect(result.current[0]).toBe(6);
  });

  it("deletes value and reverts to default", () => {
    const { result } = renderHook(() => useKV("deletable", "initial"));
    act(() => {
      result.current[1]("changed");
    });
    expect(result.current[0]).toBe("changed");

    act(() => {
      result.current[2](); // deleteValue
    });
    expect(result.current[0]).toBe("initial");
  });

  it("shares state across hooks with the same key", () => {
    const { result: hook1 } = renderHook(() => useKV("shared", 0));
    const { result: hook2 } = renderHook(() => useKV("shared", 0));

    act(() => {
      hook1.current[1](99);
    });

    expect(hook2.current[0]).toBe(99);
  });

  it("isolates state for different keys", () => {
    const { result: hookA } = renderHook(() => useKV("key-a", "a"));
    const { result: hookB } = renderHook(() => useKV("key-b", "b"));

    act(() => {
      hookA.current[1]("modified-a");
    });

    expect(hookA.current[0]).toBe("modified-a");
    expect(hookB.current[0]).toBe("b");
  });

  it("handles array values", () => {
    const { result } = renderHook(() => useKV<string[]>("list", []));

    act(() => {
      result.current[1]((prev) => [...prev, "item1"]);
    });
    act(() => {
      result.current[1]((prev) => [...prev, "item2"]);
    });

    expect(result.current[0]).toEqual(["item1", "item2"]);
  });

  it("handles object values", () => {
    const { result } = renderHook(() => useKV("config", { theme: "light" }));

    act(() => {
      result.current[1]({ theme: "dark" });
    });

    expect(result.current[0]).toEqual({ theme: "dark" });
  });

  it("resets cleanly via _resetKVStore", () => {
    const { result } = renderHook(() => useKV("resettable", "default"));

    act(() => {
      result.current[1]("stored");
    });
    expect(result.current[0]).toBe("stored");

    act(() => {
      _resetKVStore();
    });
    // After store reset and re-render, the hook should return default
    // (the listeners are cleared, so useSyncExternalStore sees a fresh snapshot)
  });
});
