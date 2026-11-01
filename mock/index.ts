/**
 * mock 层入口：汇总各业务模块的 mock 接口定义。
 * 由 vite.config.ts 中的 mockApiPlugin 读取并注册到开发服务器中间件。
 */

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

export interface MockItem {
  url: string
  method: 'get' | 'post' | 'put' | 'delete'
  response: (body: Record<string, unknown>, query: URLSearchParams) => ApiResponse
}

import userMocks from './user'
import dashboardMocks from './dashboard'

const routes: MockItem[] = [...userMocks, ...dashboardMocks]

export default routes
