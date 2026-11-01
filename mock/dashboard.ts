import type { MockItem } from './index'

const dashboardMocks: MockItem[] = [
  {
    url: '/api/dashboard/summary',
    method: 'get',
    response: () => ({
      code: 200,
      message: 'ok',
      data: {
        totalUsers: 128,
        totalAgents: 36,
        totalModels: 12,
        totalPrompts: 48,
        activeToday: 23,
        trend: [
          { date: '2026-10-26', count: 12 },
          { date: '2026-10-27', count: 18 },
          { date: '2026-10-28', count: 15 },
          { date: '2026-10-29', count: 22 },
          { date: '2026-10-30', count: 26 },
          { date: '2026-10-31', count: 20 },
          { date: '2026-11-01', count: 23 },
        ],
      },
    }),
  },
]

export default dashboardMocks
