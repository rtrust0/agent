import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests/ui',
  timeout: 40_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:5174',
    headless: true,
    viewport: { width: 1440, height: 900 },
  },
  /**
   * 前后端真实联调：先启动 FastAPI（含 seed 的 e2e 库），再启动 Vite；
   * Vite 将 /api 代理到 127.0.0.1:8000，页面请求全部由真实后端处理。
   */
  webServer: [
    {
      command: 'node tests/e2e-server.mjs',
      url: 'http://127.0.0.1:8000/health',
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:5174',
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
})
