/**
 * E2E 后端进程：重置 e2e 数据库 → 执行 seed → 启动 uvicorn。
 * 由 Playwright webServer 调用，保证每次 E2E 都从确定的种子数据开始。
 */
import { spawn, spawnSync } from 'node:child_process'
import { rmSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const backendDir = resolve(here, '../backend')
const python =
  process.platform === 'win32'
    ? resolve(backendDir, '.venv/Scripts/python.exe')
    : resolve(backendDir, '.venv/bin/python')

const env = { ...process.env, DATABASE_URL: 'sqlite+aiosqlite:///./e2e.db', PYTHONIOENCODING: 'utf-8' }

rmSync(resolve(backendDir, 'e2e.db'), { force: true })

const seed = spawnSync(python, ['-m', 'app.seed'], { cwd: backendDir, env, stdio: 'inherit' })
if (seed.status !== 0) {
  console.error('seed 失败，退出码', seed.status)
  process.exit(seed.status ?? 1)
}

const server = spawn(
  python,
  ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000', '--log-level', 'warning'],
  { cwd: backendDir, env, stdio: 'inherit' },
)

server.on('exit', (code) => process.exit(code ?? 0))
for (const signal of ['SIGTERM', 'SIGINT']) {
  process.on(signal, () => server.kill())
}
