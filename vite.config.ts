import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

/**
 * 前后端联调配置：
 * `/api/*` 反向代理到 FastAPI（默认 http://127.0.0.1:8000），
 * 前端不再内置 mock，所有请求由真实后端执行业务逻辑后返回。
 */
const BACKEND_TARGET = process.env.VITE_PROXY_TARGET ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: BACKEND_TARGET,
        changeOrigin: true,
      },
      '/health': {
        target: BACKEND_TARGET,
        changeOrigin: true,
      },
    },
  },
})
