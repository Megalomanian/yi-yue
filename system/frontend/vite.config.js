import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
export default defineConfig({
  plugins: [vue()],
  test: { include: ["src/**/*.test.js"] },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          charts: ["echarts"],
          ui: ["element-plus"],
          mobile: ["vant"],
          vue: ["vue"],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8080", "/v3": "http://127.0.0.1:8080" },
  },
});
