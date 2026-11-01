# 辰光 Vue 前端框架

基于 **Vue3 + TypeScript + Vite + Pinia + Vue Router** 的前端工程化分层框架，内置本地 mock 接口，前端无需后端即可独立开发与测试。

## 分层结构

```
src/
├── apis/           # 封装 axios 异步请求（http 实例 + 各模块接口）
├── services/       # 业务逻辑层（业务校验、数据加工）
├── router/         # 路由
├── store/          # Pinia 状态仓库
├── pages/          # 页面组件（路由级）
├── components/     # 公共组件
├── types/          # 全局类型定义
└── assets/         # 静态资源
mock/               # 本地 mock 接口定义（vite 中间件加载）
docs/tests/         # 测试报告
```

## 数据流

```
pages → store → services → apis → axios → mock（/api/*）
```

## 快速开始

```bash
npm install
npm run dev      # http://localhost:5174
npm run build    # 生产构建
npm run typecheck
```

## Mock 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/user/list` | 用户列表（分页） |
| GET | `/api/user/detail` | 用户详情 |
| POST | `/api/user/create` | 创建用户 |
| GET | `/api/dashboard/summary` | 仪表盘概览 |
