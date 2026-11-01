import type { MockItem } from './index'

export interface MockUser {
  id: number
  name: string
  email: string
  role: string
  status: 'active' | 'disabled'
  createdAt: string
}

const users: MockUser[] = [
  { id: 1, name: '张三', email: 'zhangsan@example.com', role: 'admin', status: 'active', createdAt: '2026-09-01 10:00:00' },
  { id: 2, name: '李四', email: 'lisi@example.com', role: 'operator', status: 'active', createdAt: '2026-09-02 11:30:00' },
  { id: 3, name: '王五', email: 'wangwu@example.com', role: 'operator', status: 'disabled', createdAt: '2026-09-03 14:20:00' },
  { id: 4, name: '赵六', email: 'zhaoliu@example.com', role: 'viewer', status: 'active', createdAt: '2026-09-04 09:10:00' },
  { id: 5, name: '孙七', email: 'sunqi@example.com', role: 'viewer', status: 'active', createdAt: '2026-09-05 16:45:00' },
]

const userMocks: MockItem[] = [
  {
    url: '/api/user/list',
    method: 'get',
    response: (_body, query) => {
      const page = Number(query.get('page') ?? 1)
      const pageSize = Number(query.get('pageSize') ?? 10)
      const start = (page - 1) * pageSize
      const list = users.slice(start, start + pageSize)
      return {
        code: 200,
        message: 'ok',
        data: { list, total: users.length, page, pageSize },
      }
    },
  },
  {
    url: '/api/user/detail',
    method: 'get',
    response: (_body, query) => {
      const id = Number(query.get('id'))
      const user = users.find((u) => u.id === id)
      if (!user) {
        return { code: 404, message: '用户不存在', data: null }
      }
      return { code: 200, message: 'ok', data: user }
    },
  },
  {
    url: '/api/user/create',
    method: 'post',
    response: (body) => {
      const nextId = Math.max(...users.map((u) => u.id)) + 1
      const user: MockUser = {
        id: nextId,
        name: String(body.name ?? ''),
        email: String(body.email ?? ''),
        role: String(body.role ?? 'viewer'),
        status: 'active',
        createdAt: new Date().toISOString().replace('T', ' ').slice(0, 19),
      }
      users.push(user)
      return { code: 200, message: '创建成功', data: user }
    },
  },
]

export default userMocks
