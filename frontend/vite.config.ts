import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { nodePolyfills } from "vite-plugin-node-polyfills";

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [
    react(),
    nodePolyfills({
      globals: {
        Buffer: true,
        global: true,
        process: true,
      },
      protocolImports: true,
    }),
  ],
  resolve: {
    alias: {
      stream: "stream-browserify",
      util: "util",
      zlib: resolve(__dirname, "src/shims/zlib.ts"),
    },
  },
  define: {
    "process.env": {},
  },
  optimizeDeps: {
    include: ["buffer", "process", "stream-browserify", "util", "browserify-zlib"],
  },
});