import { fileURLToPath, URL } from 'node:url'
import { defineConfig, type PluginOption } from 'vite'
import vue from '@vitejs/plugin-vue'
import mockRoutes, { type MockItem } from './mock'

/**
 * 本地 mock 中间件插件：
 * 拦截 `/api/*` 请求，按 mock 目录中定义的路由返回模拟数据，
 * 让前端在无后端环境也能独立开发、联调与测试。
 */
function mockApiPlugin(routes: MockItem[]): PluginOption {
  return {
    name: 'mock-api',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (!req.url || !req.url.startsWith('/api/')) {
          return next()
        }

        const url = new URL(req.url, 'http://localhost')
        const method = (req.method ?? 'get').toLowerCase()
        const route = routes.find((r) => r.url === url.pathname && r.method === method)
        if (!route) {
          res.statusCode = 404
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ code: 404, message: `未匹配到 mock 接口: ${method.toUpperCase()} ${url.pathname}`, data: null }))
          return
        }

        let raw = ''
        req.on('data', (chunk) => {
          raw += chunk
        })
        req.on('end', () => {
          let body: Record<string, unknown> = {}
          try {
            body = raw ? JSON.parse(raw) : {}
          } catch {
            body = {}
          }
          const result = route.response(body, url.searchParams)
          res.statusCode = 200
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify(result))
        })
      })
    },
  }
}

export default defineConfig({
  plugins: [vue(), mockApiPlugin(mockRoutes)],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5174,
  },
})
