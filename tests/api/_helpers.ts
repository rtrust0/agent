import { createServer } from 'node:http'
import { createMockHandler, createSeed } from '../../mock/index'

/**
 * 启动一个绑定本地回环端口（0 端口）的 HTTP 服务，包装 mock handler，
 * 供 API 测试用原生 fetch 直接驱动内存 mock，无需启动 Vite dev server。
 */
export interface MockServer {
  baseUrl: string
  close: () => Promise<void>
}

export function startMockServer(seed = createSeed()): Promise<MockServer> {
  const handler = createMockHandler(seed)
  const server = createServer(handler)

  return new Promise((resolve, reject) => {
    server.once('error', reject)
    server.listen(0, '127.0.0.1', () => {
      const addr = server.address()
      const port = typeof addr === 'object' && addr ? addr.port : 0
      resolve({
        baseUrl: `http://127.0.0.1:${port}`,
        close: () =>
          new Promise<void>((res, rej) => server.close((err) => (err ? rej(err) : res()))),
      })
    })
  })
}
