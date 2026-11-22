# 【user】前后端联调测试报告

- 报告时间：2026-11-22
- 被测模块：用户模块（前端 `src/apis` / `src/services` / 页面 ↔ 后端 `backend/app/modules`）
- 前端：Vue 3 + Pinia + axios（`src/apis/http.ts` 统一封装，baseURL `/api/v1`）
- 后端：FastAPI + SQLAlchemy async + 真实 SQLite（seed 数据）
- 联调链路：浏览器 → Vite dev server（`/api` 代理）→ uvicorn → SQLAlchemy → SQLite
- 测试环境：Node 22 + tsx + node:test（API 层）；Playwright Chromium（E2E）
- 结果：**API 联调 9 passed / 0 failed**；**E2E 3 passed / 0 failed**

## 一、联调接口

| # | 前端调用 | 后端接口 | 权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | `userApi.listAll` | `GET /api/v1/users` | 登录态 | 分配角色弹窗全量列表 | ✅ |
| 2 | `userApi.search` | `GET /api/v1/users/search` | user:list | 分页/关键字，pageSize → page_size | ✅ |
| 3 | `userApi.create` | `POST /api/v1/users` | user:create | 创建用户，roleIds → role_ids | ✅ |
| 4 | `userApi.detail` | `GET /api/v1/users/{id}` | user:read | 详情 | ✅ |
| 5 | `userApi.assignRoles` | `PUT /api/v1/users/{id}/roles` | user:assign_roles | 分配角色 | ✅ |
| 6 | `userApi.readRoles` | `GET /api/v1/users/{id}/roles` | user:read_roles | 角色列表（补齐权限码） | ✅ |
| 7 | `userApi.remove` | `DELETE /api/v1/users/{id}` | user:delete | 删除 | ✅ |

## 二、API 层联调用例（前端 clients → 真实后端）

- `全量用户列表返回 seed 的 3 个账号`
- `分页参数从 camelCase 映射为后端 page_size`
- `关键字搜索命中单个用户`
- `创建用户并映射 roles → roleIds`
- `查看与调整用户角色`
- `详情映射 createdAt / dataScope 字段`
- `删除用户后搜索结果为空`
- `只读账号创建用户被后端拒绝（403）`
- `运营账号删除用户被后端拒绝（403）`

执行文件：`tests/api/user.test.ts`（每个文件独立启动一个 uvicorn 实例 + 独立 SQLite 库）

## 三、E2E 用例（浏览器 → 前端 → 后端）

- `viewer sees no create / delete / assign buttons on users page`
- `ops sees create but not delete / assign buttons on users page`
- `admin creates and deletes a user through the real backend`

## 四、关键断言

- `roles[]` 映射为 `roleIds[]`，`is_active/is_superuser/data_scope/created_at` 映射为 camelCase
- 分页参数 `pageSize=2` 在请求中变为 `page_size=2`，响应 `page_size` 回映为 `pageSize`
- viewer 创建用户被后端拒绝（403），ops 删除用户被拒绝（403）
- 页面按钮显隐与后端权限码一致：ops 可见「添加用户」、不可见「删除/分配角色」

## 五、契约差异与实现裁定

- `GET /users/{id}/roles` 返回精简角色（无权限码），前端 `readRoles` 会并发拉取 `/roles/{id}` 补齐。
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
npx playwright test -g "users page"
```

报告结果取自实际执行输出：API 38 passed（5 个文件）、E2E 12 passed。
