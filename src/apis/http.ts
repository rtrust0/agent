import axios, { type AxiosInstance } from 'axios'
import type { ApiResponse } from '@/types'

/**
 * axios 统一封装：
 * - baseURL 指向 FastAPI（`/api/v1`，开发态由 Vite 代理到 127.0.0.1:8000）
 * - 请求拦截器注入 token
 * - 响应拦截器统一解包 ApiResponse 并处理业务错误码（401 清 token 跳登录、其余抛错）
 * - token 读写兼容浏览器与 Node 测试环境（无 localStorage 时使用内存值）
 */

export const TOKEN_KEY = 'access_token'

/** 默认指向同源 `/api/v1`；部署到独立域名时可通过 VITE_API_BASE_URL 覆盖 */
const DEFAULT_BASE_URL: string = import.meta.env?.VITE_API_BASE_URL ?? '/api/v1'

let baseURL: string = DEFAULT_BASE_URL
let memoryToken: string | null = null

function hasStorage(): boolean {
  return typeof localStorage !== 'undefined'
}

function hasWindow(): boolean {
  return typeof window !== 'undefined'
}

/** 测试或特殊部署时覆盖后端地址 */
export function configureHttp(options: { baseURL?: string }): void {
  if (!options.baseURL) return
  baseURL = options.baseURL
  http.defaults.baseURL = options.baseURL
}

/** 写入 token（同时持久化到 localStorage） */
export function setAuthToken(token: string | null): void {
  memoryToken = token
  if (!hasStorage()) return
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

/** 读取 token：内存优先，其次 localStorage */
export function getAuthToken(): string | null {
  if (memoryToken) return memoryToken
  return hasStorage() ? localStorage.getItem(TOKEN_KEY) : null
}

const http: AxiosInstance = axios.create({
  baseURL,
  timeout: 15000,
})

http.interceptors.request.use((config) => {
  const token = getAuthToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

function extractHttpErrorMessage(error: unknown): string | null {
  if (!axios.isAxiosError(error)) return null
  const data = error.response?.data as { detail?: unknown; message?: unknown } | undefined
  if (!data) return error.message
  if (typeof data.message === 'string') return data.message
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) {
    const first = data.detail[0] as { msg?: string; loc?: unknown[] } | undefined
    if (first?.msg) {
      const field = Array.isArray(first.loc) ? first.loc[first.loc.length - 1] : ''
      return field ? `${String(field)}: ${first.msg}` : first.msg
    }
  }
  return error.message
}

http.interceptors.response.use(
  (response) => {
    const body = response.data as ApiResponse
    // 业务码约定：200 为成功（HTTP 状态恒为 200）
    if (body && body.code !== 200) {
      if (body.code === 401) {
        setAuthToken(null)
        if (hasWindow() && window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    // 解包 data，并用断言满足 axios 拦截器返回类型约束
    return body.data as unknown as typeof response
  },
  (error) => {
    const message = extractHttpErrorMessage(error) ?? '网络异常，请稍后重试'
    return Promise.reject(new Error(message))
  },
)

/** 泛型 GET 请求，直接返回解包后的 data */
export function get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  return http.get(url, { params }) as unknown as Promise<T>
}

/** 泛型 POST 请求，直接返回解包后的 data */
export function post<T>(url: string, data?: Record<string, unknown>): Promise<T> {
  return http.post(url, data) as unknown as Promise<T>
}

/** 泛型 PUT 请求，直接返回解包后的 data */
export function put<T>(url: string, data?: Record<string, unknown>): Promise<T> {
  return http.put(url, data) as unknown as Promise<T>
}

/** 泛型 DELETE 请求，直接返回解包后的 data */
export function del<T>(url: string): Promise<T> {
  return http.delete(url) as unknown as Promise<T>
}

export default http
