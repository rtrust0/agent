import { spawn } from 'node:child_process'
import { rmSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { configureHttp } from '../../src/apis/http'

/**
 * 真实后端测试夹具：
 * 1) 准备独立的 SQLite 文件库并执行后端 seed
 * 2) 启动 uvicorn（真实 FastAPI 进程）
 * 3) 把前端 apis 层的 baseURL 指向该实例
 * 4) 测试结束后终止进程并清理数据库
 */

const here = dirname(fileURLToPath(import.meta.url))
export const BACKEND_DIR = resolve(here, '../../backend')

function venvPython(): string {
  return process.platform === 'win32'
    ? resolve(BACKEND_DIR, '.venv/Scripts/python.exe')
    : resolve(BACKEND_DIR, '.venv/bin/python')
}

function backendEnv(dbName: string): NodeJS.ProcessEnv {
  return {
    ...process.env,
    DATABASE_URL: `sqlite+aiosqlite:///./${dbName}`,
    APP_ENV: 'test',
    PYTHONIOENCODING: 'utf-8',
  }
}

function runPython(args: string[], env: NodeJS.ProcessEnv): Promise<void> {
  return new Promise((resolvePromise, reject) => {
    const child = spawn(venvPython(), args, { cwd: BACKEND_DIR, env, stdio: 'ignore' })
    child.on('error', reject)
    child.on('exit', (code) => {
      if (code === 0) resolvePromise()
      else reject(new Error(`python ${args.join(' ')} exited with ${code}`))
    })
  })
}

async function waitForHealth(url: string, timeoutMs = 40_000): Promise<void> {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url)
      if (response.ok) return
    } catch {
      // 服务尚未启动
    }
    await new Promise((r) => setTimeout(r, 300))
  }
  throw new Error(`后端未在 ${timeoutMs}ms 内就绪：${url}`)
}

export interface TestBackend {
  baseUrl: string
  apiBaseUrl: string
  stop(): Promise<void>
}

export async function startBackend(options: {
  port: number
  dbName: string
}): Promise<TestBackend> {
  const { port, dbName } = options
  const dbPath = resolve(BACKEND_DIR, dbName)
  rmSync(dbPath, { force: true })

  const env = backendEnv(dbName)
  await runPython(['-m', 'app.seed'], env)

  const proc = spawn(
    venvPython(),
    [
      '-m',
      'uvicorn',
      'app.main:app',
      '--host',
      '127.0.0.1',
      '--port',
      String(port),
      '--log-level',
      'warning',
    ],
    { cwd: BACKEND_DIR, env, stdio: 'ignore' },
  )

  const baseUrl = `http://127.0.0.1:${port}`
  const apiBaseUrl = `${baseUrl}/api/v1`
  try {
    await waitForHealth(`${baseUrl}/health`)
  } catch (error) {
    proc.kill()
    throw error
  }

  configureHttp({ baseURL: apiBaseUrl })

  return {
    baseUrl,
    apiBaseUrl,
    async stop() {
      proc.kill()
      await new Promise((r) => setTimeout(r, 400))
      try {
        rmSync(dbPath, { force: true })
      } catch {
        // Windows 下文件可能仍被占用，忽略清理失败
      }
    },
  }
}
