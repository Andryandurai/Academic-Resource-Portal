import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: false,
    open: false,
    // Vite's default host is the string "localhost". Since Node 17 stopped
    // reordering DNS results that resolves to ::1 on Windows, so the dev server
    // binds IPv6 only — http://127.0.0.1:5173 then refuses the connection while
    // http://localhost:5173 works, which reads as "the app is broken".
    // `host: true` binds every interface, the only way to serve both loopback
    // families (Vite takes a single host, not a list).
    host: true,
    proxy: {
      // Proxying in development means the browser sees one origin, so the dev
      // setup exercises the same same-origin path production uses and CORS is
      // never load-bearing.
      "/api": {
        target: process.env.VITE_API_PROXY ?? "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    target: "es2022",
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: { react: ["react", "react-dom", "react-router-dom"] },
      },
    },
  },
});
