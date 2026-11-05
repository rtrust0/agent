import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { createMockHandler } from './mock'

/**
 * 本地 mock 中间件：拦截 `/api/*` 请求，交给内存 mock handler 处理。
 * handler 内做路由匹配、鉴权与三级权限拦截，前端无需后端即可独立开发与测试。
 */
export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'mock-api',
      configureServer(server) {
        const handler = createMockHandler()
        server.middlewares.use((req, res, next) => {
          if (req.url && req.url.startsWith('/api/')) {
            handler(req, res)
            return
          }
          next()
        })
      },
    },
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5174,
  },
})
