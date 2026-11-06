import axios, { type AxiosInstance } from 'axios'
import type { ApiResponse } from '@/types'

/**
 * axios 统一封装：
 * - 统一 baseURL、超时
 * - 请求拦截器注入 token
 * - 响应拦截器统一解包 ApiResponse 并处理业务错误码（401 清 token 跳登录、403 抛业务错误）
 */

const TOKEN_KEY = 'access_token'

const http: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => {
    const body = response.data as ApiResponse
    // 业务码约定：200 为成功
    if (body && body.code !== 200) {
      if (body.code === 401) {
        localStorage.removeItem(TOKEN_KEY)
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    // 解包 data，并用断言满足 axios 拦截器返回类型约束
    return body.data as unknown as typeof response
  },
  (error) => {
    return Promise.reject(error)
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
