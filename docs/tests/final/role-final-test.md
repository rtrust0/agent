# 【role】前后端联调测试报告

- 报告时间：2026-11-22
- 被测模块：角色模块（前端 `src/apis` / `src/services` / 页面 ↔ 后端 `backend/app/modules`）
- 前端：Vue 3 + Pinia + axios（`src/apis/http.ts` 统一封装，baseURL `/api/v1`）
- 后端：FastAPI + SQLAlchemy async + 真实 SQLite（seed 数据）
- 联调链路：浏览器 → Vite dev server（`/api` 代理）→ uvicorn → SQLAlchemy → SQLite
- 测试环境：Node 22 + tsx + node:test（API 层）；Playwright Chromium（E2E）
- 结果：**API 联调 8 passed / 0 failed**；**E2E 1 passed / 0 failed**

## 一、联调接口

| # | 前端调用 | 后端接口 | 权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | `roleApi.listAll` | `GET /api/v1/roles/` | 登录态 | 角色 + 权限码集合 | ✅ |
| 2 | `roleApi.search` | `GET /api/v1/roles/search` | role:list | 分页/关键字 | ✅ |
| 3 | `roleApi.create` | `POST /api/v1/roles` | role:create | 创建（不含权限码） | ✅ |
| 4 | `roleApi.assignPermissions` | `PUT /api/v1/roles/{id}/permissions` | role:assign_permissions | 按权限码 → 权限 ID 分配 | ✅ |
| 5 | `roleApi.update` | `PUT /api/v1/roles/{id}` | role:update | 更新名称/描述 | ✅ |
| 6 | `roleApi.remove` | `DELETE /api/v1/roles/{id}` | role:delete | 删除 + 内置角色保护 | ✅ |

## 二、API 层联调用例（前端 clients → 真实后端）

- `角色列表映射 permissions → permissionCodes 与 isSystem`
- `分页搜索角色`
- `创建角色并按权限码分配权限（两步提交）`
- `分配权限后权限码集合更新`
- `更新角色名称（角色码保持不变）`
- `删除角色后列表恢复为 3 个`
- `角色不存在返回 404 文案`
- `只读账号创建角色被拒绝（403）`

执行文件：`tests/api/role.test.ts`（每个文件独立启动一个 uvicorn 实例 + 独立 SQLite 库）

## 三、E2E 用例（浏览器 → 前端 → 后端）

- `admin sees role action buttons`

## 四、关键断言

- `permissions[]` 映射为 `permissionCodes[]`；`super_admin` 标记为内置且含 71 个权限码
- 创建角色时携带 2 个权限码，落地后权限集合一致
- 更新角色传入 `code` 被后端忽略，角色码保持不变（页面编辑态已置灰）
- viewer 创建角色返回 403

## 五、契约差异与实现裁定

- 后端仅保护 `super_admin` 不可删除，`ops_admin`/`viewer` 在 UI 上可编辑删除，如需保护应在后端补充。
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
npx playwright test -g "role action buttons"
```

报告结果取自实际执行输出：API 38 passed（5 个文件）、E2E 12 passed。
