import { describe, it, expect } from "vitest";
import { renderHook } from "@testing-library/react";
import { useIsMobile } from "../../src/hooks/use-mobile";

describe("useIsMobile", () => {
  it("returns a boolean", () => {
    const { result } = renderHook(() => useIsMobile());
    expect(typeof result.current).toBe("boolean");
  });

  it("returns false for wide viewports (default jsdom is 1024px)", () => {
    const { result } = renderHook(() => useIsMobile());
    // jsdom default innerWidth is 1024
    expect(result.current).toBe(false);
  });
});
