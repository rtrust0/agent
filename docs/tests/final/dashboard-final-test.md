# 【dashboard】前后端联调测试报告

- 报告时间：2026-11-22
- 被测模块：工作台模块（前端 `src/apis` / `src/services` / 页面 ↔ 后端 `backend/app/modules`）
- 前端：Vue 3 + Pinia + axios（`src/apis/http.ts` 统一封装，baseURL `/api/v1`）
- 后端：FastAPI + SQLAlchemy async + 真实 SQLite（seed 数据）
- 联调链路：浏览器 → Vite dev server（`/api` 代理）→ uvicorn → SQLAlchemy → SQLite
- 测试环境：Node 22 + tsx + node:test（API 层）；Playwright Chromium（E2E）
- 结果：**API 联调 4 passed / 0 failed**；**E2E 1 passed / 0 failed**

## 一、联调接口

| # | 前端调用 | 后端接口 | 权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | `dashboardApi.summary` | `GET /api/v1/dashboard/stats` | dashboard:read | 用户/角色/权限总数 | ✅ |

## 二、API 层联调用例（前端 clients → 真实后端）

- `管理员工作台统计映射为 camelCase`
- `运营账号可见同一份统计（dashboard:read）`
- `只读账号可见工作台统计`
- `未登录访问工作台统计返回 401`

执行文件：`tests/api/dashboard.test.ts`（每个文件独立启动一个 uvicorn 实例 + 独立 SQLite 库）

## 三、E2E 用例（浏览器 → 前端 → 后端）

- `dashboard renders stats and permission chips from backend`

## 四、关键断言

- `total_users/total_roles/total_permissions` 映射为 camelCase，值为 3/3/71
- admin、ops、viewer 均可访问（三者都有 dashboard:read）
- 未登录访问返回 401
- E2E：统计卡片渲染 3/3/71，「当前身份权限（71 项）」可见，矩阵 4 列

## 五、契约差异与实现裁定

- 工作台统计为平台级聚合，不受数据范围过滤，仅由 `dashboard:read` 控制访问。
- 原 mock 的 `/dashboard/summary` 已替换为后端的 `/dashboard/stats`。
- 已移除 Vite mock 中间件，`/api` 由 Vite 代理到真实 FastAPI（默认 `http://127.0.0.1:8000`）。
- `mock/` 目录的删除被本机安全策略拒绝（安全删除失败），代码中已无任何引用，属遗留未清理文件。
- 图形验证码整体移除：后端 V3 登录契约只有 `username/password`，前端同步删除验证码字段与接口。
- 后端 snake_case 由 `src/apis/dto.ts` 统一映射为页面使用的 camelCase；分页参数 `page_size` ↔ `pageSize`。
- 角色创建为两步提交（`POST /roles` → `PUT /roles/{id}/permissions`），第二步失败会留下无权限角色。
- `Role.isSystem` 由 `code === 'super_admin'` 派生，后端仅保护该内置角色。
- 权限 `module` 由后端按权限码前缀派生，前端不再提交 module 字段。
- 联调修复：后端 `GET /users/me` 由 `UserRead` 调整为 `UserWithRolesRead`，前端可获取当前用户角色。

## 六、复现命令

```bash
# 1) 启动后端（首次会创建并 seed 数据库）
cd backend && .venv/Scripts/python.exe -m app.seed
cd backend && .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000

# 2) 启动前端（/api 代理到 127.0.0.1:8000）
npm run dev

# 3) 联调 API 测试（自动拉起后端实例，独立 seed 库）
npm run test:api

# 4) 模块 E2E（自动拉起后端 + Vite，重置 e2e.db）
npx playwright test -g "dashboard renders"
```

报告结果取自实际执行输出：API 38 passed（5 个文件）、E2E 12 passed。
