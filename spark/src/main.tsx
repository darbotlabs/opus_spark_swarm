import { createRoot } from "react-dom/client";
import { ErrorBoundary } from "react-error-boundary";
import App from "./App";
import "./index.css";

function ErrorFallback({ error, resetErrorBoundary }: { error: unknown; resetErrorBoundary: () => void }) {
  if (import.meta.env.DEV) throw error;

  const message = error instanceof Error ? error.message : String(error);

  return (
    <div style={{ padding: "2rem", fontFamily: "Inter, sans-serif" }}>
      <h1>Something went wrong</h1>
      <pre style={{ color: "red", fontSize: "0.875rem" }}>{message}</pre>
      <button onClick={resetErrorBoundary} style={{ marginTop: "1rem" }}>
        Try Again
      </button>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <ErrorBoundary FallbackComponent={ErrorFallback}>
    <App />
  </ErrorBoundary>,
);
