import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // In development, proxy API calls to FastAPI backend
    proxy: {
      "/api": "http://localhost:8000",
      "/assets": "http://localhost:8000",
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
