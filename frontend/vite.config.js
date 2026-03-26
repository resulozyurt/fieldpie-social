import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
      "/assets": "http://localhost:8000",
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    assetsDir: "ui-assets",  // /assets/ yerine /ui-assets/ kullan — backend /assets ile çakışmaz
  },
});