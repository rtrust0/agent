# 【auth】前后端联调测试报告

- 报告时间：2026-11-22
- 被测模块：认证模块（前端 `src/apis` / `src/services` / 页面 ↔ 后端 `backend/app/modules`）
- 前端：Vue 3 + Pinia + axios（`src/apis/http.ts` 统一封装，baseURL `/api/v1`）
- 后端：FastAPI + SQLAlchemy async + 真实 SQLite（seed 数据）
- 联调链路：浏览器 → Vite dev server（`/api` 代理）→ uvicorn → SQLAlchemy → SQLite
- 测试环境：Node 22 + tsx + node:test（API 层）；Playwright Chromium（E2E）
- 结果：**API 联调 8 passed / 0 failed**；**E2E 6 passed / 0 failed**

## 一、联调接口

| # | 前端调用 | 后端接口 | 权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | `authApi.login` | `POST /api/v1/auth/login` | 公开 | 登录成功 / 密码错误 401 | ✅ |
| 2 | `authApi.mePermissions` | `GET /api/v1/users/me/permissions` | 登录态 | 71/45/23 权限码，超管全量 | ✅ |
| 3 | `authApi.me` | `GET /api/v1/users/me` | 登录态 | 当前用户 + 角色 | ✅ |

## 二、API 层联调用例（前端 clients → 真实后端）

- `管理员通过真实后端登录成功`
- `登录后可拉取 71 个权限码且按字典序返回`
- `me 返回带角色的用户信息`
- `只读账号权限码为 23 个且不含写权限`
- `运营账号权限码为 45 个（含审批授权）`
- `密码错误由后端返回业务码 401`
- `未登录访问受保护接口返回 401`
- `退出登录后 token 被清空`

执行文件：`tests/api/auth.test.ts`（每个文件独立启动一个 uvicorn 实例 + 独立 SQLite 库）

## 三、E2E 用例（浏览器 → 前端 → 后端）

- `admin sees all system menu items`
- `viewer menu hides write / system modules`
- `ops is redirected to /403 for an unauthorized system route`
- `unauthenticated access redirects to login with redirect query`
- `logout then login as viewer shrinks menu without reload`
- `identity switch recomputes menu and user box`

## 四、关键断言

- admin 登录返回 token，`isSuperuser=true`、`dataScope=all`
- 超管权限码 71 个且按字典序返回；ops 45 个；viewer 23 个
- 密码错误返回业务码 401（`用户名或密码错误`），不会误判为 400
- 无 token 访问 `/users/me` 返回 401，并触发前端清 token 逻辑

## 五、契约差异与实现裁定

- 登录失败沿用后端业务码 401；原 mock 为 400，前端仅提示 message，不受影响。
- 身份切换（admin → viewer）不复用旧权限缓存：`store/permission.ts` 以 token 为键，切换后重拉。
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
npx playwright test -g "menu"
```

报告结果取自实际执行输出：API 38 passed（5 个文件）、E2E 12 passed。
