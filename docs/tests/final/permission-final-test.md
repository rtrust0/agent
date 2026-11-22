# 【permission】前后端联调测试报告

- 报告时间：2026-11-22
- 被测模块：权限模块（前端 `src/apis` / `src/services` / 页面 ↔ 后端 `backend/app/modules`）
- 前端：Vue 3 + Pinia + axios（`src/apis/http.ts` 统一封装，baseURL `/api/v1`）
- 后端：FastAPI + SQLAlchemy async + 真实 SQLite（seed 数据）
- 联调链路：浏览器 → Vite dev server（`/api` 代理）→ uvicorn → SQLAlchemy → SQLite
- 测试环境：Node 22 + tsx + node:test（API 层）；Playwright Chromium（E2E）
- 结果：**API 联调 9 passed / 0 failed**；**E2E 1 passed / 0 failed**

## 一、联调接口

| # | 前端调用 | 后端接口 | 权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | `permissionApi.listAll` | `GET /api/v1/permissions/` | 登录态 | 71 条 / 14 个模块 | ✅ |
| 2 | `permissionApi.search` | `GET /api/v1/permissions/search` | permission:list | 分页/关键字 | ✅ |
| 3 | `permissionApi.create` | `POST /api/v1/permissions` | permission:create | 创建（module 由 code 派生） | ✅ |
| 4 | `permissionApi.update` | `PUT /api/v1/permissions/{id}` | permission:update | 更新名称 | ✅ |
| 5 | `permissionApi.remove` | `DELETE /api/v1/permissions/{id}` | permission:delete | 删除 | ✅ |

## 二、API 层联调用例（前端 clients → 真实后端）

- `权限目录 71 条、14 个模块（module 由后端派生）`
- `分页搜索权限码`
- `权限详情返回名称与模块`
- `创建权限时模块由权限码前缀自动派生`
- `权限码格式非法被后端拒绝`
- `权限码重复被后端拒绝`
- `更新权限名称（权限码不可改）`
- `删除权限后详情返回 404`
- `只读账号创建权限被拒绝（403）`

执行文件：`tests/api/permission.test.ts`（每个文件独立启动一个 uvicorn 实例 + 独立 SQLite 库）

## 三、E2E 用例（浏览器 → 前端 → 后端）

- `viewer permissions page renders backend matrix（71 权限 / 14 模块）`

## 四、关键断言

- 权限目录 71 条、14 个模块，首条模块为 `user`
- `agent:` 前缀共 8 条，搜索分页 total 正确
- 创建 `report:read` 后 `module=report`（前端传入的 module 被忽略）
- 非法权限码 `Bad Code` 与重复权限码分别返回 400 文案
- 权限矩阵 E2E：4 列（权限码 + 3 角色）、71 条权限行、14 个模块分组行

## 五、契约差异与实现裁定

- 删除被角色引用的权限在后端会级联移除授权（与原 mock 的「不可删除」不同），页面提示语已同步修改。
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
npx playwright test -g "matrix"
```

报告结果取自实际执行输出：API 38 passed（5 个文件）、E2E 12 passed。
