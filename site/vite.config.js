import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// the landing page builds into ../docs, which GitHub Pages serves from the main branch
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: { outDir: "../docs", emptyOutDir: true },
});
