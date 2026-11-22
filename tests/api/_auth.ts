import { authApi } from '../../src/apis/auth'
import { setAuthToken } from '../../src/apis/http'
import type { AuthSession } from '../../src/types'

/** 以 seed 账号登录，并把 token 写入前端 http 客户端 */
export async function loginAs(username: string, password = '123456'): Promise<AuthSession> {
  const session = await authApi.login({ username, password })
  setAuthToken(session.token)
  return session
}

export function logout(): void {
  setAuthToken(null)
}

/** 断言异步调用抛出指定文案的错误 */
export async function expectReject(
  action: () => Promise<unknown>,
  expected: string | RegExp,
): Promise<string> {
  try {
    await action()
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    if (typeof expected === 'string') {
      if (!message.includes(expected)) {
        throw new Error(`期望错误包含「${expected}」，实际为「${message}」`)
      }
    } else if (!expected.test(message)) {
      throw new Error(`期望错误匹配 ${expected}，实际为「${message}」`)
    }
    return message
  }
  throw new Error('期望调用失败，但实际成功')
}
