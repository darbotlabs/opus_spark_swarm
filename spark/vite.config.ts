import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react-swc";
import { resolve } from "path";
import { defineConfig } from "vite";

const projectRoot = import.meta.dirname;

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": resolve(projectRoot, "src"),
      "@github/spark/hooks": resolve(projectRoot, "src/hooks/use-kv.ts"),
    },
  },
  server: {
    port: 5173,
  },
});
