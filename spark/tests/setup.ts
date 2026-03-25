import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";
import { _resetKVStore } from "../src/hooks/use-kv";

// jsdom polyfills for APIs that Radix UI and React components depend on
if (typeof window !== "undefined") {
  // matchMedia
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });

  // ResizeObserver (Radix ScrollArea)
  window.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;

  // scrollIntoView (used by AgentActivityFeed)
  Element.prototype.scrollIntoView = () => {};
}

afterEach(() => {
  cleanup();
  _resetKVStore();
});
