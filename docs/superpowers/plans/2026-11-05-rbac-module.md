# RBAC 权限管理模块 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `chenguang-vue`（Vue 3 前端框架）内落地完整 RBAC 权限管理模块——登录 + 后台布局 + 工作台 + 用户/角色/权限三页（含权限矩阵）+ 403 页 + 菜单/按钮/路由三级权限控制，纯 Mock 数据源，全接口测试 + UI 关键路径测试 + 测试报告。

**Architecture:** mock 层重构为「内存数据库 + 种子数据 + 可独立测试的 `createMockHandler`」；Vite 插件只做转发，测试用 Node 内置 `node --test` 驱动同款 handler。前端严格沿用 `apis → services → store → pages` 分层，新增后台布局、权限组合式函数与指令、路由守卫，UI 用原生 Vue + CSS 设计令牌手写。

**Tech Stack:** Vue 3 + TypeScript（strict）+ Vite 6 + Pinia + Vue Router 4 + axios；Node 内置测试运行器 + 原生 fetch（API 测试，经 `tsx` 加载 TS）；Playwright（UI 关键路径）。测试专用 devDependencies：`@playwright/test`、`tsx`。

**Spec:** `docs/spec/rbac-prd.md`（本计划从其逐条展开）

## Global Constraints

- 权限码格式 `模块:操作` 全小写，共 22 个，逐字：`user:list`, `user:read`, `user:create`, `user:update`, `user:delete`, `user:assign_roles`, `user:read_roles`, `role:list`, `role:read`, `role:create`, `role:update`, `role:delete`, `role:assign_permissions`, `permission:list`, `permission:read`, `permission:create`, `permission:update`, `permission:delete`, `system:api_keys`, `system:audit`, `system:alerts`, `system:settings`。
- 响应统一 `{ code, message, data }`；`code` 取值：`200` 成功、`400` 参数校验失败、`401` 未登录/token 无效、`403` 无权限、`404` 资源不存在；mock 始终返回 HTTP 200，业务码在 `code` 字段。
- 鉴权分三档：`open`（无需登录）、`login`（需有效 token，无权限码）、`<permission-code>`（需对应权限码）。请求头 `Authorization: Bearer <token>`。
- 授权规则：`is_superuser` 直接放行全部；否则取用户所有角色权限码并集判断。前端 `hasPerm(code)` 同规则（`isSuperuser` 短路 true）。
- 种子角色（逐字）：`super_admin`（全部 22 项，`isSystem=true`）、`ops_admin`（`user:list user:read user:create user:update user:read_roles role:list role:read role:create role:update permission:list permission:read`）、`viewer`（`user:list user:read user:read_roles role:list role:read permission:list permission:read`）。
- 演示账号密码统一 `123456`：`admin`（super_admin，superuser）、`ops`（ops_admin）、`viewer`（viewer）。
- 开发服务器端口 `5174`；接口统一前缀 `/api`。
- 前端页面路由：`/login`、`/403`、`/`（工作台）、`/system/users`、`/system/roles`、`/system/permissions`、`/system/api-keys`、`/system/audit`、`/system/alerts`、`/system/settings`。
- 菜单权限码映射（逐字）：用户管理 `user:list`、角色管理 `role:list`、权限管理 `permission:list`、API 密钥 `system:api_keys`、审计日志 `system:audit`、告警规则 `system:alerts`、系统配置 `system:settings`。
- 按钮权限码映射见 PRD 5.2（逐字：用户页 `user:create`/`user:assign_roles`/`user:delete`；角色页 `role:create`/`role:update`/`role:assign_permissions`/`role:delete`；权限页 `permission:create`/`permission:update`/`permission:delete`）。
- 不新增运行/开发依赖（仅测试 devDeps `@playwright/test`、`tsx`）；UI 不用组件库，内联 SVG 图标。
- 现有 `mock/user.ts`、`mock/dashboard.ts`、`mock/index.ts`、`src/pages/Home.vue`、`src/pages/About.vue`、`src/pages/UserList.vue`、`src/components/AppHeader.vue` 被本模块替换或删除。

## Review Focus

1. **无任何角色/权限的用户访问受保护接口** → 期望返回 `403`，而非因访问空集合报错。归属 Task 3：`test_open_roles_read_roles` 之外，在 Task 2 增加「新创建无角色用户读角色」用例断言空集返回。
2. **超管即使角色不含某权限码也放行** → 期望 `is_superuser` 短路。归属 Task 2：`test_superuser_bypasses`（构造 superuser、权限码为空时访问需权限接口仍 200）。
3. **跨账号权限缓存复用** → 前端 `permission` store 按 token 键控，切换身份后必须重拉，退出清空。归属 Task 9：`hasPerm` 以当前 token 的集合为准；Task 16 用 Playwright 切身份验证菜单重算。
4. **三个全量列举接口仍无需权限码（但需登录）** → `GET /api/users`、`/api/roles/`、`/api/permissions/` 不得要求权限码。归属 Task 4：`test_list_routes_require_login_not_permission`（登录用户 200、未登录 401、无权限码用户仍 200）。
5. **未登录访问受保护路由与 403 页面** → 路由守卫对无权限码用户跳 `/403`、未登录跳 `/login`。归属 Task 12 + Task 16（Playwright 直连无权路由落 `/403`）。
6. **权限码去重与排序** → `/users/me/permissions` 返回去重且排序的列表。归属 Task 2：`test_me_permissions_dedup_sorted`。

---

## File Structure

```
mock/
  types.ts            # MockPermission/MockRole/MockUser/MockSession/MockDb/ApiResponse/Route 类型
  seed.ts             # 22 权限码、3 角色、6 用户种子 + createSeed() + getUserPermissionCodes()
  handler.ts          # createMockHandler(seed?) + 路由匹配 + 鉴权/权限拦截
  routes/auth.ts      # captcha/login/users/me/users/me/permissions
  routes/user.ts      # 用户 7 接口
  routes/role.ts      # 角色 7 接口
  routes/permission.ts# 权限 6 接口
  routes/dashboard.ts # summary
  index.ts            # 汇总 export createMockHandler / createSeed（供 vite 与测试）
src/
  types/index.ts      # 重写：User/Role/Permission/AuthSession/Captcha/PageResult/DashboardSummary/ApiResponse
  apis/http.ts        # 扩展 get/post/put/del + 401/403 拦截
  apis/auth.ts user.ts role.ts permission.ts dashboard.ts index.ts
  services/auth.service.ts user.service.ts role.service.ts permission.service.ts dashboard.service.ts index.ts
  store/auth.ts permission.ts user.ts role.ts permission.ts index.ts
  composables/usePermission.ts
  directives/v-permission.ts
  router/index.ts     # 路由 + meta.permission + beforeEach 守卫
  layouts/AdminLayout.vue
  components/ui/      # BaseButton/BaseInput/BaseSelect/BaseModal/BaseBadge/BasePagination/BaseSkeleton/BaseCaptcha
  components/AppToast.vue + composables/useToast.ts  # 轻量 Toast
  pages/Login.vue Dashboard.vue Forbidden.vue
  pages/system/Users.vue Roles.vue Permissions.vue Placeholder.vue
  App.vue             # 改为 <RouterView/>
  assets/main.css     # 权限蓝图设计令牌
tests/
  api/rbac.api.test.ts        # 全接口测试（node --test + 内置 fetch，驱动 createMockHandler）
  ui/rbac.spec.ts             # Playwright 关键路径
playwright.config.ts
docs/tests/rbac/rbac-test-report.md   # 测试报告（最终产物）
```

---

### Task 1: 测试依赖与测试基建

**Files:**
- Modify: `package.json`（新增 scripts + devDependencies）
- Create: `tests/api/_helpers.ts`

**Interfaces:**
- Produces: devDeps `@playwright/test`、`tsx`；scripts `"test:api": "tsx --test tests/api/rbac.api.test.ts"`、`"test:ui": "playwright test"`；`tests/api/_helpers.ts` 导出 `startMockServer(seed?): Promise<{ baseUrl: string; close: () => Promise<void> }>`（用 `node:http` 包 `createMockHandler(createSeed())` 监听端口 0）。

- [ ] **Step 1: 安装测试依赖**

Run: `npm i -D @playwright/test tsx`
Expected: 安装成功，`package.json` 出现两个 devDependencies

- [ ] **Step 2: 新增测试脚本与 helper**

在 `package.json` 加 `test:api`、`test:ui` 两个 script；写 `tests/api/_helpers.ts` 的 `startMockServer`（内部 `import { createMockHandler, createSeed } from '../../mock/handler'`，`createServer(...)`，`listen(0)`，返回 `baseUrl` 与 `close`）。

- [ ] **Step 3: 提交**

```bash
git add package.json package-lock.json tests/api/_helpers.ts
git commit -m "chore: 引入测试依赖（playwright/tsx）与 API 测试基建"
```

---

### Task 2: Mock 核心 — 内存库、种子、处理器框架、认证接口

**Files:**
- Create: `mock/types.ts`、`mock/seed.ts`、`mock/handler.ts`、`mock/routes/auth.ts`、`mock/index.ts`
- Modify: `mock/user.ts`（删除）、`mock/dashboard.ts`（删除）、`mock/index.ts`（重写）

**Interfaces:**
- Produces:
  - `mock/types.ts`：`PermissionModule = 'user'|'role'|'permission'|'system'`；`MockPermission { id; code; name; module }`；`MockRole { id; code; name; description; isSystem; permissionCodes: string[] }`；`MockUser { id; username; email; password; isActive; isSuperuser; roleIds: number[]; createdAt }`；`MockSession { token; userId }`；`MockDb { permissions: MockPermission[]; roles: MockRole[]; users: MockUser[]; sessions: MockSession[]; captcha: Map<string,string> }`；`ApiResponse<T>`；`RouteContext { db; user?: MockUser; body; query; params }`；`MockRoute { method; path; permission: 'open'|'login'|string; handler(ctx): ApiResponse<unknown> }`。
  - `mock/seed.ts`：`ALL_PERMISSION_CODES: string[]`（22 项）、`createSeed(): MockDb`、`getUserPermissionCodes(db, user): string[]`（superuser 返回全部，否则并集去重排序）。
  - `mock/handler.ts`：`createMockHandler(seed?: MockDb): (req: IncomingMessage, res: ServerResponse) => void`；路由匹配支持 `/api/users/:id`、`/api/users/:id/roles` 形路径；按 `permission` 三档拦截；读 body（JSON）、query、`Authorization` 头。
  - `mock/index.ts`：`export { createMockHandler, createSeed } from './handler'` 等。
  - `mock/routes/auth.ts`：`export const authRoutes: MockRoute[]`——`GET /api/auth/captcha`(open)、`POST /api/auth/login`(open)、`GET /api/users/me`(login)、`GET /api/users/me/permissions`(login)。

- [ ] **Step 1: 写失败测试**

在 `tests/api/rbac.api.test.ts`（Task 2 起逐步累积）先写认证相关断言：
- `test_auth_login_success`：`POST /api/auth/login` 传 `admin/123456`（captcha 先 `GET /api/auth/captcha` 取 text）→ `code===200`、`data.token` 非空、`data.user.username==='admin'`。
- `test_auth_login_wrong_captcha`：错误 captcha → `code===400`。
- `test_me_requires_login`：无 token 调 `/api/users/me` → `code===401`。
- `test_me_permissions_superuser_dedup_sorted`：以 admin token 调 `/api/users/me/permissions` → 返回全部 22 码且严格排序去重。

Run: `npx tsx --test tests/api/rbac.api.test.ts`
Expected: FAIL（`createMockHandler` 不存在）

- [ ] **Step 2: 实现 `mock/types.ts`、`mock/seed.ts`、`mock/handler.ts`、`mock/routes/auth.ts`、`mock/index.ts`**

按 Interfaces 落地；`createMockHandler` 未匹配到路由返回 `{ code: 404, message: '接口不存在', data: null }`；鉴权失败返回 401、权限不足返回 403。login 校验 captcha（从 `db.captcha` 取值、比对后删除）、密码、账号激活状态。

- [ ] **Step 3: 运行测试确认通过**

Run: `npx tsx --test tests/api/rbac.api.test.ts`
Expected: 认证 4 用例 PASS

- [ ] **Step 4: 提交**

```bash
git add mock/ tests/api/rbac.api.test.ts
git commit -m "feat: mock 核心处理器与认证接口"
```

---

### Task 3: Mock 用户接口（7 个）

**Files:**
- Create: `mock/routes/user.ts`

**Interfaces:**
- Consumes: `MockDb`、`RouteContext`、`MockRoute`、`getUserPermissionCodes`（均来自 Task 2）。
- Produces: `export const userRoutes: MockRoute[]`：
  - `GET /api/users`(login) → `MockUser[]`（不含 password 字段的公开视图）
  - `GET /api/users/search`(`user:list`) → `PageResult<MockUser>`（分页 + keyword 过滤 username/email）
  - `GET /api/users/:id`(`user:read`)
  - `POST /api/users`(`user:create`) → 校验 username/email/password 必填、username 唯一
  - `DELETE /api/users/:id`(`user:delete`)
  - `PUT /api/users/:id/roles`(`user:assign_roles`) → body `{ roleIds: number[] }`
  - `GET /api/users/:id/roles`(`user:read_roles`) → `MockRole[]`

- [ ] **Step 1: 写失败测试**

追加用例：
- `test_users_list_requires_login`：无 token → 401；admin token → 200 且 `data` 为数组。
- `test_users_list_no_permission_required`：viewer token 调 `GET /api/users` → 200（登录即可，无需 `user:list`）。
- `test_user_search_pagination`：`GET /api/users/search?page=1&pageSize=2` → `data.total===6`、`data.list.length===2`。
- `test_user_create_validation`：缺 username → 400。
- `test_user_assign_roles_permission`：viewer 调 `PUT /api/users/1/roles` → 403；ops 调 → 200（ops 无 `user:assign_roles`，但 superuser/admin 有——此处用 admin 200、viewer 403）。
- `test_user_read_roles_empty`：新建无角色用户，`GET /api/users/:id/roles` → 200 空数组（Review Focus 1）。

Run: `npx tsx --test tests/api/rbac.api.test.ts`
Expected: 新用例 FAIL（路由未注册）

- [ ] **Step 2: 实现 `mock/routes/user.ts`**

注册进 `createMockHandler` 的路由表（`mock/index.ts` 或 handler 内汇总）。公开视图剔除 `password`。

- [ ] **Step 3: 运行测试确认通过**

Run: `npx tsx --test tests/api/rbac.api.test.ts`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add mock/routes/user.ts mock/index.ts tests/api/rbac.api.test.ts
git commit -m "feat: mock 用户接口"
```

---

### Task 4: Mock 角色与权限接口（13 个）

**Files:**
- Create: `mock/routes/role.ts`、`mock/routes/permission.ts`

**Interfaces:**
- Produces:
  - `roleRoutes: MockRoute[]`：`GET /api/roles/`(login)、`GET /api/roles/search`(`role:list`)、`GET /api/roles/:id`(`role:read`)、`POST /api/roles`(`role:create`)、`PUT /api/roles/:id`(`role:update`)、`DELETE /api/roles/:id`(`role:delete`)、`PUT /api/roles/:id/permissions`(`role:assign_permissions`)。
  - `permissionRoutes: MockRoute[]`：`GET /api/permissions/`(login)、`GET /api/permissions/search`(`permission:list`)、`GET /api/permissions/:id`(`permission:read`)、`POST /api/permissions`(`permission:create`)、`PUT /api/permissions/:id`(`permission:update`，code 不可改)、`DELETE /api/permissions/:id`(`permission:delete`)。

- [ ] **Step 1: 写失败测试**

追加用例：
- `test_list_routes_require_login_not_permission`：无 token 调 `/api/roles/` → 401；viewer token → 200（Review Focus 4）。
- `test_role_delete_system_forbidden`：删除 `super_admin`（isSystem）→ 400。
- `test_role_assign_permissions`：ops 调 `PUT /api/roles/3/permissions` → 403（ops 无 `role:assign_permissions`）；admin → 200。
- `test_permission_update_immutable_code`：更新时改 code → 400。
- `test_permission_delete_used`：删除仍被角色引用的权限 → 400（或 200 并清理引用——本计划定为 400）。
- `test_permission_search`：`GET /api/permissions/search` → 200 且 `data.total===22`。

Run: `npx tsx --test tests/api/rbac.api.test.ts`
Expected: 新用例 FAIL

- [ ] **Step 2: 实现 `mock/routes/role.ts`、`mock/routes/permission.ts`**

注册进路由表。内置角色（isSystem）不可删除/改权限；权限 code 不可改；删除被引用权限返回 400。

- [ ] **Step 3: 运行测试确认通过**

Run: `npx tsx --test tests/api/rbac.api.test.ts`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add mock/routes/role.ts mock/routes/permission.ts mock/index.ts tests/api/rbac.api.test.ts
git commit -m "feat: mock 角色与权限接口"
```

---

### Task 5: Mock 工作台接口 + Vite 插件接入

**Files:**
- Create: `mock/routes/dashboard.ts`
- Modify: `vite.config.ts`（用 `createMockHandler` 替换旧 `mockApiPlugin(routes)`）

**Interfaces:**
- Produces: `dashboardRoutes: MockRoute[]` = `GET /api/dashboard/summary`(login) → `{ totalUsers, totalRoles, totalPermissions }`（由 db 实时统计）。
- Vite 插件：`configureServer` 中对 `/api/*` 请求调用 `createMockHandler()`，其余 `next()`。

- [ ] **Step 1: 写失败测试**

追加 `test_dashboard_summary`：admin token → 200 且 `data.totalRoles===3`、`data.totalPermissions===22`。

Run: `npx tsx --test tests/api/rbac.api.test.ts`
Expected: FAIL

- [ ] **Step 2: 实现 dashboard 路由 + 改 `vite.config.ts`**

`vite.config.ts` 移除旧 `MockItem`/`mockApiPlugin(routes)` 逻辑，改为 `server.middlewares.use((req,res,next) => req.url?.startsWith('/api/') ? createMockHandler()(req,res) : next())`。

- [ ] **Step 3: 运行测试 + 启动 dev server 冒烟**

Run: `npx tsx --test tests/api/rbac.api.test.ts` 与 `npm run dev`（另开终端）
Expected: 测试 PASS；dev server 启动无报错，`curl http://localhost:5174/api/dashboard/summary` 返回 401（未带 token）

- [ ] **Step 4: 提交**

```bash
git add mock/routes/dashboard.ts mock/index.ts vite.config.ts tests/api/rbac.api.test.ts
git commit -m "feat: mock 工作台接口并接入 Vite 插件"
```

---

### Task 6: 前端类型 + http 层扩展

**Files:**
- Modify: `src/types/index.ts`（重写）、`src/apis/http.ts`（加 put/del 与 401/403 拦截）

**Interfaces:**
- Produces:
  - 类型：`User { id; username; email; isActive; isSuperuser; roleIds: number[]; createdAt }`、`Role { id; code; name; description; isSystem; permissionCodes: string[]; createdAt }`、`Permission { id; code; name; module: 'user'|'role'|'permission'|'system'; createdAt }`、`AuthSession { token; user: User }`、`Captcha { captchaId; text }`、`PageResult<T>`、`DashboardSummary { totalUsers; totalRoles; totalPermissions }`、`ApiResponse<T>`。
  - `http`：`get<T>`、`post<T>`、`put<T>`、`del<T>`；响应拦截器 401 → 清 `localStorage` token 并跳 `/login`；403 → `reject(Error(message))`。

- [ ] **Step 1: 改 `src/types/index.ts` 与 `src/apis/http.ts`**

删除旧 `User` 定义；`http.ts` 新增 `put`/`del`（复用 axios 实例），拦截器按 PRD 3.4 处理 401/403。

- [ ] **Step 2: 验证**

Run: `npm run typecheck`
Expected: 由于旧页面引用旧类型，会报错——本任务先记录基线错误清单，Task 12 起逐步清零；仅确认 `types`/`http` 本身无新增错误。

- [ ] **Step 3: 提交**

```bash
git add src/types/index.ts src/apis/http.ts
git commit -m "feat: 前端 RBAC 类型与 http 层扩展"
```

---

### Task 7: 前端 apis 与 services 层

**Files:**
- Modify: `src/apis/index.ts`、`src/apis/user.ts`（重写）、`src/apis/dashboard.ts`（重写）
- Create: `src/apis/auth.ts`、`src/apis/role.ts`、`src/apis/permission.ts`
- Modify: `src/services/index.ts`、`src/services/user.service.ts`（重写）、`src/services/dashboard.service.ts`（重写）
- Create: `src/services/auth.service.ts`、`src/services/role.service.ts`、`src/services/permission.service.ts`

**Interfaces:**
- Consumes: `get/post/put/del`（Task 6）。
- Produces:
  - `authApi`：`captcha()`、`login(data: {username;password;captchaId;captcha}): Promise<AuthSession>`、`me(): Promise<User>`、`mePermissions(): Promise<string[]>`。
  - `userApi`：`listAll(): Promise<User[]>`、`search(params: {page;pageSize;keyword?}): Promise<PageResult<User>>`、`detail(id): Promise<User>`、`create(data): Promise<User>`、`remove(id): Promise<void>`、`assignRoles(id, roleIds: number[]): Promise<User>`、`readRoles(id): Promise<Role[]>`。
  - `roleApi`：`listAll()`、`search(params)`、`detail(id)`、`create(data)`、`update(id, data)`、`remove(id)`、`assignPermissions(id, permissionCodes: string[])`。
  - `permissionApi`：`listAll()`、`search(params)`、`detail(id)`、`create(data)`、`update(id, data)`、`remove(id)`。
  - `dashboardApi`：`summary(): Promise<DashboardSummary>`。
  - 对应 `*Service` 封装业务校验（如 user create 校验 username/email/password 非空）。

- [ ] **Step 1: 实现 apis 与 services 层**

按 Interfaces 落地；service 仅在 apis 之上加校验，不新增接口。

- [ ] **Step 2: 验证**

Run: `npm run typecheck`
Expected: apis/services 相关无类型错误（页面未改，旧页面错误仍在，属预期）

- [ ] **Step 3: 提交**

```bash
git add src/apis src/services
git commit -m "feat: 前端 RBAC apis 与 services 层"
```

---

### Task 8: Pinia store（auth / permission）

**Files:**
- Create: `src/store/auth.ts`、`src/store/permission.ts`
- Modify: `src/store/index.ts`（导出）

**Interfaces:**
- Consumes: `authApi`、`mePermissions`、`me`（Task 7）。
- Produces:
  - `useAuthStore`：state `token`、`user`；getter `isLoggedIn`；action `login(credentials): Promise<void>`（存 token 到 localStorage、拉 `me`、触发权限刷新）、`logout()`、`switchIdentity(username): Promise<void>`（用对应演示账号密码 `123456` 重新 login）。
  - `usePermissionStore`：state `codes: Set<string>`、`isSuperuser: boolean`、`loaded: boolean`；action `fetchPermissions()`（按当前 token 键控缓存，token 空则清空）；`hasPerm(code): boolean`（`isSuperuser || codes.has(code)`，未加载时返回 false）。

- [ ] **Step 1: 实现两个 store**

`permission` store 的缓存以 `token` 为 key（模块级 `cachedToken`/`cachedCodes`），切换 token 后重拉，避免跨账号复用（Review Focus 3）。

- [ ] **Step 2: 验证**

Run: `npm run typecheck`
Expected: store 无类型错误

- [ ] **Step 3: 提交**

```bash
git add src/store/auth.ts src/store/permission.ts src/store/index.ts
git commit -m "feat: auth 与 permission 状态仓库"
```

---

### Task 9: 权限组合式函数、指令、路由守卫、App 改造

**Files:**
- Create: `src/composables/usePermission.ts`、`src/directives/v-permission.ts`
- Modify: `src/router/index.ts`、`src/App.vue`、`src/main.ts`（注册指令）

**Interfaces:**
- Produces:
  - `usePermission(): { hasPerm: (code: string) => boolean }`（读 `usePermissionStore`）。
  - `v-permission`：值为权限码，无权限时移除元素。
  - 路由表：`/login`、`/403`、`/`（AdminLayout 父路由，子路由工作台 index、system/users(`user:list`)、system/roles(`role:list`)、system/permissions(`permission:list`)、system/api-keys(`system:api_keys`)、system/audit(`system:audit`)、system/alerts(`system:alerts`)、system/settings(`system:settings`)）；`meta.permission` 记录所需码。
  - 全局 `beforeEach`：未登录且目标非 `/login` → `/login`；已登录访问 `/login` → `/`；目标 `meta.permission` 存在且 `!hasPerm` → `/403`。
  - `App.vue` 改为 `<RouterView/>`；`main.ts` 注册 `v-permission`。

- [ ] **Step 1: 实现组合式函数、指令、路由、App**

`beforeEach` 内首次进入时若 `permission.loaded===false` 先 `await fetchPermissions()`。

- [ ] **Step 2: 验证**

Run: `npm run typecheck`
Expected: 路由/指令无类型错误（AdminLayout 与页面组件尚未创建，`component: () => import(...)` 指向的文件缺失会在 build 报错，故本任务只跑 typecheck 不 build）

- [ ] **Step 3: 提交**

```bash
git add src/composables/usePermission.ts src/directives/v-permission.ts src/router/index.ts src/App.vue src/main.ts
git commit -m "feat: 权限组合式函数、指令与路由守卫"
```

---

### Task 10: 设计令牌与 UI 基础组件

**Files:**
- Modify: `src/assets/main.css`（权限蓝图令牌）
- Create: `src/components/ui/BaseButton.vue`、`BaseInput.vue`、`BaseSelect.vue`、`BaseModal.vue`、`BaseBadge.vue`、`BasePagination.vue`、`BaseSkeleton.vue`、`BaseCaptcha.vue`
- Create: `src/components/AppToast.vue` + `src/composables/useToast.ts`

**Interfaces:**
- Produces:
  - `main.css`：`:root` 令牌 `--navy-900 #0F1B2D`、`--bg #F5F6F8`、`--panel #FFFFFF`、`--brand #3E63DD`、`--dawn #E2A13C`、`--grant #1E7A5A`、`--danger #C2453C`、文字/边框令牌；等宽字体栈用于 `.code`。
  - 组件 props：`BaseButton { variant?: 'primary'|'danger'|'ghost'; disabled?: boolean; loading?: boolean }`（slot 内容）；`BaseInput { modelValue; label?; error?; placeholder?; type? }`；`BaseSelect { modelValue; options: {label;value}[]; label? }`；`BaseModal { open; title }`（`@close`）；`BaseBadge { tone: 'grant'|'dawn'|'danger'|'muted'; text }`；`BasePagination { page; pageSize; total }`（`@change`）；`BaseSkeleton`；`BaseCaptcha { modelValue }`（`@refresh`）；`useToast()` → `{ toast(type, message) }` 与 `AppToast`。

- [ ] **Step 1: 写组件与样式**

全部 scoped CSS + 触觉反馈（`:active { transform: scale(0.98) }`）；实现 loading/empty/error 三态视觉。

- [ ] **Step 2: 验证**

Run: `npm run typecheck`
Expected: 无类型错误（组件未被引用，`noUnusedLocals` 不作用于 `.vue` 顶层，可通过）

- [ ] **Step 3: 提交**

```bash
git add src/assets/main.css src/components/ui src/components/AppToast.vue src/composables/useToast.ts
git commit -m "feat: 设计令牌与 UI 基础组件"
```

---

### Task 11: AdminLayout（侧边栏 + 顶栏 + 身份切换器 + 菜单过滤）

**Files:**
- Create: `src/layouts/AdminLayout.vue`

**Interfaces:**
- Consumes: `useAuthStore`、`usePermissionStore`/`usePermission`、`useToast`。
- Produces: `AdminLayout.vue`——左侧侧边栏（品牌区 + 平台组[工作台恒显示] + 系统管理组[7 子项按 `hasPerm` 过滤，全隐藏则父菜单隐藏] + 用户区[账号/退出]）、顶栏（面包屑 + 身份切换器 segmented：超级管理员/运营管理员/只读观察者，切换调 `switchIdentity`）、内容区 `<RouterView/>`。

- [ ] **Step 1: 实现 AdminLayout**

菜单项 `permission` 字段与 Global Constraints 映射一致；面包屑基于完整菜单结构生成。

- [ ] **Step 2: 验证**

Run: `npm run typecheck`
Expected: 无类型错误

- [ ] **Step 3: 提交**

```bash
git add src/layouts/AdminLayout.vue
git commit -m "feat: 后台整体布局与菜单权限过滤"
```

---

### Task 12: 登录页、工作台、403 页、占位页

**Files:**
- Create: `src/pages/Login.vue`、`src/pages/Dashboard.vue`、`src/pages/Forbidden.vue`、`src/pages/system/Placeholder.vue`

**Interfaces:**
- Consumes: `authApi.captcha/login`、`useAuthStore`、`usePermissionStore`、`dashboardApi.summary`、UI 组件。
- Produces:
  - `Login.vue`：用户名/密码 + 4 位验证码（BaseCaptcha，点击刷新），登录成功跳 `/`。
  - `Dashboard.vue`：统计卡片（totalUsers/totalRoles/totalPermissions）+ 当前身份权限清单 + 矩阵预览。
  - `Forbidden.vue`：403 提示 + 返回工作台按钮。
  - `Placeholder.vue`：按路由展示"功能建设中"占位。

- [ ] **Step 1: 实现四个页面**

`Dashboard` 用 `dashboardApi.summary()` 与 `mePermissions()` 渲染；矩阵预览由角色+权限客户端派生。

- [ ] **Step 2: 验证**

Run: `npm run typecheck && npm run build`
Expected: build 通过（此时所有路由组件已就位，系统三页 Task 13-15 未建会报错——本任务先建 `system/Users/Roles/Permissions.vue` 为空壳占位以过 build，后续任务填充）

- [ ] **Step 3: 提交**

```bash
git add src/pages/Login.vue src/pages/Dashboard.vue src/pages/Forbidden.vue src/pages/system/Placeholder.vue
git commit -m "feat: 登录页、工作台、403 与占位页"
```

---

### Task 13: 用户管理页

**Files:**
- Create: `src/store/user.ts`、`src/store/role.ts`（供分配弹窗取全量角色）
- Modify: `src/pages/system/Users.vue`（填充）

**Interfaces:**
- Consumes: `userService`、`roleApi.listAll`、`usePermission`、UI 组件。
- Produces: `useUserStore`（list/total/loading/error + fetchList/search/create/remove/assignRoles）；`Users.vue`——表格（ID/用户名/邮箱/角色/状态/创建时间/操作）+ 分页搜索 + 添加用户弹窗 + 分配角色弹窗 + 删除确认；按钮按 `v-permission`/`hasPerm` 包裹（`user:create`/`user:assign_roles`/`user:delete`）。

- [ ] **Step 1: 实现 user store 与 Users.vue**

角色列由 `roleIds` 映射名称；分配角色弹窗取 `roleApi.listAll()`。

- [ ] **Step 2: 验证**

Run: `npm run typecheck && npm run build`
Expected: 通过

- [ ] **Step 3: 提交**

```bash
git add src/store/user.ts src/store/role.ts src/pages/system/Users.vue
git commit -m "feat: 用户管理页"
```

---

### Task 14: 角色管理页

**Files:**
- Modify: `src/store/role.ts`（扩展 CRUD）
- Modify: `src/pages/system/Roles.vue`（填充）

**Interfaces:**
- Consumes: `roleService`、`permissionApi.listAll`、`usePermission`。
- Produces: `useRoleStore`（list/total/loading/error + fetchList/create/update/remove/assignPermissions）；`Roles.vue`——表格（ID/角色码/名称/描述/内置标记/权限数/操作）+ 创建/编辑弹窗（角色码/名称/描述/权限多选）+ 分配权限弹窗 + 删除确认；按钮 `role:create`/`role:update`/`role:assign_permissions`/`role:delete`；内置角色（isSystem）禁删/禁改权限。

- [ ] **Step 1: 实现 Roles.vue 与 role store 扩展**

权限多选列表按 4 模块分组（22 项）。

- [ ] **Step 2: 验证**

Run: `npm run typecheck && npm run build`
Expected: 通过

- [ ] **Step 3: 提交**

```bash
git add src/store/role.ts src/pages/system/Roles.vue
git commit -m "feat: 角色管理页"
```

---

### Task 15: 权限管理页（含权限矩阵）

**Files:**
- Create: `src/store/permission.ts`（列表状态，注意与 Task 8 的权限码 store 区分：本文件是权限「目录」的 CRUD store）
- Modify: `src/pages/system/Permissions.vue`（填充）

**Interfaces:**
- Consumes: `permissionService`、`roleApi.listAll`（取各角色 permissionCodes 派生矩阵）、`usePermission`。
- Produces: `usePermissionCatalogStore`（为避免与 Task 8 `usePermissionStore` 撞名，命名为 `usePermissionCatalogStore`：list/total/loading/error + fetchList/create/update/remove）；`Permissions.vue`——列表/矩阵双视图切换；列表（ID/权限码/名称/模块/操作，按钮 `permission:create`/`permission:update`/`permission:delete`）；矩阵（22 行 × 3 角色，勾选态由角色 permissionCodes 派生，sticky 表头与模块行）。

- [ ] **Step 1: 实现 Permissions.vue 与 catalog store**

矩阵为只读视图（授权关系在角色页维护），不新增接口。

- [ ] **Step 2: 验证**

Run: `npm run typecheck && npm run build`
Expected: 通过

- [ ] **Step 3: 提交**

```bash
git add src/store/permission.ts src/pages/system/Permissions.vue
git commit -m "feat: 权限管理页与权限矩阵"
```

---

### Task 16: API 全接口测试套件收尾 + 覆盖核对

**Files:**
- Modify: `tests/api/rbac.api.test.ts`

**Interfaces:**
- Consumes: `startMockServer`（Task 1）、`createSeed`。
- Produces: 覆盖第 6 节全部 26 个接口 × {成功 / 400 / 401 / 403 / 404} 分支的完整用例；断言每类响应 `code` 与关键 `data` 字段结构。

- [ ] **Step 1: 补齐全部接口用例**

对照 PRD 第 6 节逐一核对：认证 4 + 用户 7 + 角色 7 + 权限 6 + 工作台 1 = 25 个接口（注：`/users/me` 与 `/users/me/permissions` 已在 Task 2）。为每个接口至少覆盖成功 + 无权限（以 viewer/ops 验证 403）+ 未登录（401）；校验类补 400、不存在补 404。

- [ ] **Step 2: 运行并确认全绿**

Run: `npx tsx --test tests/api/rbac.api.test.ts`
Expected: 全部用例 PASS，且用例数 ≥ 接口数 × 3 分支

- [ ] **Step 3: 提交**

```bash
git add tests/api/rbac.api.test.ts
git commit -m "test: RBAC 全接口覆盖测试"
```

---

### Task 17: Playwright UI 关键路径测试

**Files:**
- Create: `playwright.config.ts`、`tests/ui/rbac.spec.ts`

**Interfaces:**
- Consumes: dev server（playwright `webServer` 启动 `npm run dev`）。
- Produces: `rbac.spec.ts` 关键路径：三种身份登录（admin/ops/viewer）→ 侧边栏菜单差异、按钮显隐（用户页添加/删除、角色页创建/分配、权限页创建）、直接访问无权路由（viewer 访问 `/system/roles`）落 `/403`、身份切换后菜单重算。

- [ ] **Step 1: 写 playwright.config.ts 与 spec**

`webServer.command = 'npm run dev'`、`url = 'http://localhost:5174'`、`reuseExistingServer`。

- [ ] **Step 2: 安装浏览器并运行**

Run: `npx playwright install chromium`，再 `npx playwright test`
Expected: 关键路径用例 PASS

- [ ] **Step 3: 提交**

```bash
git add playwright.config.ts tests/ui/rbac.spec.ts
git commit -m "test: RBAC UI 关键路径测试"
```

---

### Task 18: 测试报告 + 收尾提交推送

**Files:**
- Create: `docs/tests/rbac/rbac-test-report.md`

**Interfaces:**
- Produces: Markdown 报告——结论、API 覆盖统计（接口数 × 分支数 × 通过数）、逐接口用例明细、UI 关键路径记录、缺陷/遗留。

- [ ] **Step 1: 运行两套测试并记录真实结果**

Run: `npx tsx --test tests/api/rbac.api.test.ts` 与 `npx playwright test`
Expected: 全绿；把实际输出写入报告

- [ ] **Step 2: 写 `docs/tests/rbac/rbac-test-report.md`**

按上述结构记录；对未覆盖或失败项如实标注。

- [ ] **Step 3: 提交并推送**

```bash
git add -A
git commit -m "feat: rbac模块开发完毕并生成了测试报告，所有产物提交本地库"
git push
```

---

## Self-Review

**Spec 覆盖：** PRD 第 4 节页面清单 → Task 11/12/13/14/15；第 5 节三级权限控制 → Task 9/11/13/14/15；第 6 节接口契约 → Task 2/3/4/5；第 7 节技术方案 → Task 6-15；第 8 节测试与验收 → Task 16/17/18；第 9 节交付物 → Task 18。无遗漏。

**类型一致性：** `createMockHandler`/`createSeed`/`getUserPermissionCodes` 在 Task 2 定义，Task 3/4/5/16 按同名消费；`get/put/del` 在 Task 6 定义，Task 7 消费；`hasPerm` 在 Task 8/9 定义，Task 11/13/14/15 消费。权限码字符串在 Global Constraints 与各任务映射逐字一致。注意 Task 8 的权限码 store 命名 `usePermissionStore` 与 Task 15 的权限目录 store 命名 `usePermissionCatalogStore` 已显式区分。

**Review Focus 落地：** 6 条已各映射到 Task 2/3/4/9/12/16 的测试或验证步骤。

**比例：** 计划以签名、接口清单、测试断言为主，不含完整函数体转录；后端 mock 用 `tsx --test` 跑测试，前端用 `npm run typecheck`/`npm run build`/Playwright 验证。
