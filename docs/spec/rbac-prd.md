# 辰光 Vue 前端框架 · RBAC 权限管理模块 PRD

> 版本：v1.0 · 日期：2026-11-05 · 状态：待评审
> 目标项目：`chenguang-vue`（Vue 3 + TypeScript + Vite + Pinia + Vue Router + axios + Vite Mock 中间件）
> 上游参考：`chenguang-agent-platform-v4/docs/spec/PROJECT_SPEC_V2.md`（RBAC 授权章节）、`docs/design/plans/rbac-plan.md`、`docs/design/ui/RBAC-UI-设计说明书.md`、`docs/ui/rbac/`（静态 UI 原型）

---

## 1. 概述与背景

辰光平台现有 RBAC 模块已具备用户 / 角色 / 权限的完整数据模型与 CRUD，但缺少**授权控制**能力：后端只做身份认证、不校验权限码；前端菜单、操作按钮、路由对所有登录用户一视同仁。

本 PRD 定义在 `chenguang-vue` 前端框架内落地的 **RBAC 权限管理模块**：补齐"谁能访问什么、能做什么"的授权体验——登录、后台整体布局、工作台、用户 / 角色 / 权限三个管理页、权限矩阵、403 无权页，以及贯穿全局的**菜单 / 按钮 / 路由三级权限控制**。

本模块为前端框架工程，**数据来源为纯 Mock**（Vite mock 中间件 + 内存态种子数据），接口契约与真实后端字段对齐，为后续接真实后端预留契约。

---

## 2. 目标 / 非目标 / 反目标

### 2.1 目标

1. 提供完整的 RBAC 后台体验：登录（含图形验证码）、后台整体布局、工作台、用户 / 角色 / 权限三页、403 无权页。
2. 实现三级权限控制：侧边栏菜单按权限显隐、操作按钮按权限显隐、路由守卫按权限拦截。
3. 权限管理页提供**权限矩阵**视图（权限 × 角色的授权二维网格）。
4. 提供顶栏**身份切换器**，可在三种演示身份间一键切换，直观呈现权限差异。
5. Mock 层覆盖 PRD 全部接口，支持内存态 CRUD 与权限码拦截（401 / 403 / 校验失败）。
6. 测试达到"全 API 覆盖 + UI 关键路径"双重验收，并产出 Markdown 测试报告。

### 2.2 非目标（本次不做）

- 对接真实后端（FastAPI / JWT / MySQL）。
- 资源级数据权限（本人 / 部门 / 全量数据隔离）。
- 权限操作审计日志、权限申请与审批流程。
- 用户编辑（`user:update` 权限码在清单中保留，但本次不提供用户编辑接口与按钮，与上游 Spec 2.5.3 一致）。
- 前端组件单元测试（Vitest / Jest 不引入）。

### 2.3 反目标（做成了即为失败）

- 破坏框架既有分层约定（`apis → services → store → pages`），或把页面逻辑与 mock 数据耦合进视图组件。
- 引入重量级 UI 组件库，偏离"权限蓝图"视觉与零依赖定位。
- 权限控制只在某个页面生效，而非法则一致地贯穿菜单 / 按钮 / 路由。

---

## 3. 角色与权限模型

### 3.1 权限码规范

格式 `模块:操作`，全小写。本次共 **22 个权限码**：

| 模块 | 权限码 | 含义 |
|---|---|---|
| user | `user:list` | 用户列表查看 |
| user | `user:read` | 用户详情查看 |
| user | `user:create` | 创建用户 |
| user | `user:update` | 更新用户（本次无接口使用，保留在清单） |
| user | `user:delete` | 删除用户 |
| user | `user:assign_roles` | 给用户分配角色 |
| user | `user:read_roles` | 查看用户角色 |
| role | `role:list` | 角色列表查看 |
| role | `role:read` | 角色详情查看 |
| role | `role:create` | 创建角色 |
| role | `role:update` | 更新角色 |
| role | `role:delete` | 删除角色 |
| role | `role:assign_permissions` | 给角色分配权限 |
| permission | `permission:list` | 权限列表查看 |
| permission | `permission:read` | 权限详情查看 |
| permission | `permission:create` | 创建权限 |
| permission | `permission:update` | 更新权限 |
| permission | `permission:delete` | 删除权限 |
| system | `system:api_keys` | API 密钥管理 |
| system | `system:audit` | 审计日志查看 |
| system | `system:alerts` | 告警规则管理 |
| system | `system:settings` | 系统配置管理 |

### 3.2 角色（种子数据）

| id | code | name | isSystem | permissions |
|---|---|---|---|---|
| 1 | `super_admin` | 超级管理员 | true | 全部 22 项 |
| 2 | `ops_admin` | 运营管理员 | false | `user:list` `user:read` `user:create` `user:update` `user:read_roles` `role:list` `role:read` `role:create` `role:update` `permission:list` `permission:read` |
| 3 | `viewer` | 只读观察者 | false | `user:list` `user:read` `user:read_roles` `role:list` `role:read` `permission:list` `permission:read` |

### 3.3 演示账号与身份

登录页与顶栏身份切换器共用三个演示身份，密码统一 `123456`：

| 账号 | 角色 | superuser | 权限概要 |
|---|---|---|---|
| `admin` | 超级管理员 | true | 全部权限（`is_superuser` 直接放行） |
| `ops` | 运营管理员 | false | 用户 / 角色的读、创建、更新；权限只读 |
| `viewer` | 只读观察者 | false | 用户 / 角色 / 权限只读 |

### 3.4 授权判定规则

- `is_superuser == true`：直接放行，拥有全部权限。
- 否则：取用户所有角色权限码的并集，判断目标权限码是否在集合内。
- 前端 `hasPerm(code)` 采用同一规则：`isSuperuser` 直接返回 `true`，否则查权限码集合；`GET /api/users/me/permissions` 对超管返回全部已定义权限码。两者保持一致，避免"按钮被隐藏但 mock 又放行"的错位。
- 权限不足统一返回业务错误码 `403`，前端提示"没有权限执行该操作"；未登录 / token 无效返回 `401`，前端跳登录。

---

## 4. 功能需求（页面清单）

| 路由 | 页面 | 说明 |
|---|---|---|
| `/login` | 登录 | 用户名 / 密码 + 4 位图形验证码（可点击刷新），登录成功跳工作台 |
| `/` | 工作台 | RBAC 概览：统计卡片、当前身份权限清单、权限矩阵预览 |
| `/system/users` | 用户管理 | 用户列表（分页 / 搜索）、添加用户、分配角色、删除用户 |
| `/system/roles` | 角色管理 | 角色列表（分页 / 搜索）、创建角色、编辑、分配权限、删除 |
| `/system/permissions` | 权限管理 | 权限列表 / **权限矩阵**双视图、创建 / 编辑 / 删除权限 |
| `/system/api-keys` 等 | 占位页 | API 密钥 / 审计日志 / 告警规则 / 系统配置四个占位页（仅用于演示菜单权限过滤） |
| `/403` | 无权访问 | 路由守卫拦截的无权限提示页 |

### 4.1 后台整体布局（AdminLayout）

- 左侧固定深色侧边栏（248px）：品牌区 + 「平台」组（工作台，无权限要求恒显示）+「系统管理」组（7 个子项）+ 用户区（当前账号 + 退出登录）。
- 顶栏（60px）：面包屑 + 右侧身份切换器。
- 内容区最大宽 1280px，左对齐，细边框 + 极轻阴影，不做统一大圆角。

### 4.2 视觉设计系统：权限蓝图（Permission Blueprint）

| Token | 值 | 用途 |
|---|---|---|
| `--navy-900` | `#0F1B2D` | 侧边栏、矩阵表头 |
| `--bg` | `#F5F6F8` | 页面背景 |
| `--panel` | `#FFFFFF` | 面板 |
| `--brand` | `#3E63DD` | 主交互色（主按钮 / 激活态） |
| `--dawn` | `#E2A13C` | 品牌强调（内置角色 / 警示） |
| `--grant` | `#1E7A5A` | 授权绿（已授权 / 成功 / 活跃） |
| `--danger` | `#C2453C` | 警示红（删除 / 停用 / 拒绝） |

- 字体：标题用 `Space Grotesk`（回退系统无衬线），权限码 / ID 用等宽字体（`IBM Plex Mono`，回退 `Consolas`），中文正文系统字体栈。
- 图标：内联 SVG（24×24、2px 描边、round 线帽），不依赖外部图标库。

### 4.3 用户管理页

- 表格列：ID、用户名、邮箱、角色、状态、创建时间、操作。
- 操作列按权限渲染：分配角色（`user:assign_roles`）、删除（`user:delete`）。
- 顶部「添加用户」按钮（`user:create`）：用户名、邮箱、密码、初始角色（多选）。
- 分配角色弹窗：角色复选框列表（按模块分组，角色数据来自开放的 `GET /api/roles/`）。

### 4.4 角色管理页

- 表格列：ID、角色码、名称、描述、内置标记、权限数、操作。
- 操作列按权限渲染：编辑（`role:update`）、分配权限（`role:assign_permissions`）、删除（`role:delete`）。
- 内置角色（`isSystem`）不可删除、不可编辑权限。
- 创建 / 编辑弹窗：角色码、名称、描述、权限复选框（22 项按模块分组）。
- 分配权限弹窗：同权限复选框结构。

### 4.5 权限管理页（含权限矩阵）

- 列表视图：ID、权限码、名称、模块、操作（编辑 `permission:update`、删除 `permission:delete`）；顶部「创建权限」（`permission:create`）。
- 矩阵视图（核心特色）：行 = 22 项权限（按 user / role / permission / system 分组），列 = 3 个角色，交叉点绿色实心勾 = 已授权、空心 = 未授权；表头与模块行 sticky。
- 矩阵数据由「角色 + 已授权权限」关系派生，不新增独立接口。

### 4.6 工作台

- 统计卡片：用户数 / 角色数 / 权限数（来自 `GET /api/dashboard/summary`）。
- 当前身份权限清单：来自 `GET /api/users/me/permissions`。
- 权限矩阵预览：从角色与权限派生的小型矩阵。

### 4.7 登录与验证码

- 4 位随机大写字符（排除 `0/O/1/I`），点击刷新，不区分大小写。
- Mock 验证码接口返回验证码文本（供测试与演示使用），不校验图片 OCR。

### 4.8 身份切换器

- 顶栏分段控件：超级管理员 / 运营管理员 / 只读观察者。
- 切换即"换账号重新登录"：重新换取 token、重拉权限码、刷新菜单与按钮，整页重新计算可见性。

---

## 5. 三级权限控制

### 5.1 菜单过滤（侧边栏）

| 菜单项 | 路由 | 权限码 |
|---|---|---|
| 工作台 | `/` | 无（恒显示） |
| 用户管理 | `/system/users` | `user:list` |
| 角色管理 | `/system/roles` | `role:list` |
| 权限管理 | `/system/permissions` | `permission:list` |
| API 密钥 | `/system/api-keys` | `system:api_keys` |
| 审计日志 | `/system/audit` | `system:audit` |
| 告警规则 | `/system/alerts` | `system:alerts` |
| 系统配置 | `/system/settings` | `system:settings` |

- 无权限的子菜单不渲染；「系统管理」下全部子项无权限时，父菜单整体隐藏。
- 面包屑基于完整菜单结构生成，不受过滤影响。

### 5.2 按钮过滤（页面操作）

| 页面 | 按钮 | 权限码 |
|---|---|---|
| 用户管理 | 添加用户 | `user:create` |
| 用户管理 | 分配角色 | `user:assign_roles` |
| 用户管理 | 删除用户 | `user:delete` |
| 角色管理 | 创建角色 | `role:create` |
| 角色管理 | 编辑角色 | `role:update` |
| 角色管理 | 分配权限 | `role:assign_permissions` |
| 角色管理 | 删除角色 | `role:delete` |
| 权限管理 | 创建权限 | `permission:create` |
| 权限管理 | 编辑权限 | `permission:update` |
| 权限管理 | 删除权限 | `permission:delete` |

- 无权限按钮不渲染；表格对应操作列整列隐藏。
- 实现方式：`v-permission` 指令 + `hasPerm(code)` 组合式函数（二者语义等价，指令用于模板、函数用于脚本判断）。

### 5.3 路由守卫

- 全局 `router.beforeEach`：未登录访问受保护路由 → 跳 `/login`（携带来源）；已登录但无 `meta.permission` 对应权限 → 跳 `/403`。
- 路由 `meta.permission` 记录所需权限码；`/system/*` 各页配置对应码（同 5.1 映射）。

---

## 6. 接口契约

> 统一前缀 `/api`；响应统一 `{ code, message, data }`；`code === 200` 成功，`403` 无权限，`401` 未登录 / token 无效，`400` 参数校验失败，`404` 资源不存在。
> 请求鉴权分三档：**开放**（无需登录）、**登录**（需有效 token，无权限码）、**需权限码**（标注具体权限码）。受保护接口通过 `Authorization: Bearer <token>` 鉴权。

### 6.1 认证

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/api/auth/captcha` | 开放 | 返回 `{ captchaId, text }`，供登录使用 |
| POST | `/api/auth/login` | 开放 | `{ username, password, captchaId, captcha }` → `{ token, user }` |
| GET | `/api/users/me` | 登录 | 当前用户信息 |
| GET | `/api/users/me/permissions` | 登录 | 当前用户权限码 `string[]`（去重、已排序） |

### 6.2 用户

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/api/users` | 登录 | 全量用户（供分配角色弹窗） |
| GET | `/api/users/search` | `user:list` | 分页搜索 `{ page, pageSize, keyword }` |
| GET | `/api/users/{id}` | `user:read` | 用户详情 |
| POST | `/api/users` | `user:create` | 创建用户 |
| DELETE | `/api/users/{id}` | `user:delete` | 删除用户 |
| PUT | `/api/users/{id}/roles` | `user:assign_roles` | 分配角色 `{ roleIds[] }` |
| GET | `/api/users/{id}/roles` | `user:read_roles` | 查看用户角色 |

### 6.3 角色

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/api/roles/` | 登录 | 全量角色（供分配角色弹窗） |
| GET | `/api/roles/search` | `role:list` | 分页搜索 |
| GET | `/api/roles/{id}` | `role:read` | 角色详情 |
| POST | `/api/roles` | `role:create` | 创建角色 |
| PUT | `/api/roles/{id}` | `role:update` | 更新角色 |
| DELETE | `/api/roles/{id}` | `role:delete` | 删除角色 |
| PUT | `/api/roles/{id}/permissions` | `role:assign_permissions` | 分配权限 `{ permissionCodes[] }` |

### 6.4 权限

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/api/permissions/` | 登录 | 全量权限（供分配权限弹窗） |
| GET | `/api/permissions/search` | `permission:list` | 分页搜索 |
| GET | `/api/permissions/{id}` | `permission:read` | 权限详情 |
| POST | `/api/permissions` | `permission:create` | 创建权限 |
| PUT | `/api/permissions/{id}` | `permission:update` | 更新权限（`code` 不可改） |
| DELETE | `/api/permissions/{id}` | `permission:delete` | 删除权限 |

### 6.5 工作台

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/api/dashboard/summary` | 登录 | `{ totalUsers, totalRoles, totalPermissions }` |

### 6.6 数据模型

- `User`：`{ id, username, email, isActive, isSuperuser, roleIds[], createdAt }`
- `Role`：`{ id, code, name, description, isSystem, permissionCodes[], createdAt }`
- `Permission`：`{ id, code, name, module, createdAt }`
- `PageResult<T>`：`{ list, total, page, pageSize }`

---

## 7. 技术方案

**采用方案一：框架原生分层。** 理由：唯一同时满足"基于框架、贴近原型、零依赖、可接后端"四项要求。

### 7.1 目录结构

```
mock/
  index.ts            # createMockHandler(seed)：构建可独立测试的内存 mock 处理器
  db.ts               # 内存数据库（users/roles/permissions/sessions）+ 种子数据
  auth.ts             # 验证码 / 登录 / 当前用户 / 当前用户权限
  user.ts  role.ts  permission.ts  dashboard.ts
src/
  apis/               # http 封装 + auth/user/role/permission/dashboard 模块接口
  services/           # 业务逻辑层（校验、数据加工）
  store/              # auth、permission、user、role、permission 五个 Pinia store
  router/             # 路由 + meta.permission + beforeEach 守卫
  composables/usePermission.ts   # hasPerm(code)
  directives/v-permission.ts     # v-permission="'user:create'"
  layouts/AdminLayout.vue
  components/ui/       # BaseButton/Input/Select/Table/Modal/Toast/Badge/Pagination/Skeleton/Captcha
  pages/
    Login.vue  Dashboard.vue  Forbidden.vue
    system/Users.vue  Roles.vue  Permissions.vue  Placeholder.vue
  assets/main.css      # 权限蓝图设计令牌 + 基础样式
docs/tests/rbac/       # 测试报告目录
```

### 7.2 关键机制

- **鉴权**：登录获取 token 存入 `localStorage`；http 请求拦截器注入 `Authorization`；响应拦截器统一解包 `{ code, message, data }`，`401` 清 token 跳登录，`403` 抛业务错误提示。
- **权限状态**：`permission` store 按 token 键控缓存权限码集合；登录成功与身份切换时重拉 `GET /users/me/permissions`；token 为空时清空（避免跨账号复用高权限缓存）。
- **Mock 鉴权与拦截**：`createMockHandler(seed)` 解析 `Authorization` 映射到会话用户，按第 3.4 节规则对受保护接口做权限码判定，返回 `401` / `403` / `400` / `404` / `200`。
- **UI 组件**：原生 Vue + scoped CSS 手写一套轻量基础组件，满足 loading / empty / error 三态与触觉反馈（`scale(0.98)`）。
- **权限矩阵**：数据由 `GET /api/roles/`（含 `permissionCodes`）与 `GET /api/permissions/` 在客户端派生，不新增接口。

### 7.3 依赖

- 运行与开发依赖不新增，沿用现有 `vue` / `vue-router` / `pinia` / `axios` / `vite` / `typescript`。
- 测试专用 devDependencies（不进入运行时产物）：`@playwright/test`（UI 关键路径自动化，含浏览器二进制）、`tsx`（用 Node 内置测试运行器加载 TS 测试文件）。

---

## 8. 测试与验收

### 8.1 测试策略（方案 B：API 全覆盖 + UI 关键路径）

**API 层（硬指标）**：用 Node 内置测试运行器（`node --test`）+ 原生 `fetch`，直接驱动 `createMockHandler(seed)` 暴露的内存处理器，覆盖第 6 节全部接口 × 三类分支：

- 正常分支：成功返回与字段结构。
- 校验失败：缺失 / 非法参数 → `400`。
- 权限分支：以 `admin` / `ops` / `viewer` 三种身份分别验证 `403` 与放行；未登录 / 无效 token → `401`。

**UI 层（关键路径，Playwright）**：覆盖上游 Spec 第 4~7 条验收标准——三种身份登录、侧边栏菜单过滤、按钮显隐、直接访问无权路由落到 `/403`。

### 8.2 测试报告

- 输出 Markdown，存放于 `docs/tests/rbac/`：`rbac-test-report.md`（总报告：结论 + 覆盖统计 + 逐接口用例明细 + UI 关键路径记录 + 缺陷 / 遗留）。

### 8.3 验收标准

1. `admin` 可访问全部接口与页面；`ops` / `viewer` 访问越权接口返回业务码 `403`。
2. `GET /api/users/me/permissions` 返回当前身份去重后的权限码列表。
3. 侧边栏「系统管理」子菜单按权限显隐，全部无权限时父菜单隐藏。
4. 三个管理页的增 / 删 / 改 / 分配按钮按权限显隐。
5. 直接访问无权路由被拦截并落到 `/403`。
6. 三种身份切换后菜单 / 按钮 / 权限即时重算。
7. 全接口测试与 UI 关键路径测试全部通过，报告落盘于 `docs/tests/rbac/`。

---

## 9. 交付物清单

1. RBAC 模块前端代码（页面 / 布局 / 组件 / store / apis / services / 路由守卫 / 权限指令与组合式函数）。
2. Mock 层（内存数据库 + 种子数据 + 全接口处理器 + 权限拦截）。
3. 测试脚本（API 全覆盖 + UI 关键路径）。
4. 测试报告 `docs/tests/rbac/rbac-test-report.md`。
5. Git 提交（本地 + 远程推送）。

---

## 10. 边界与遗留

- `user:update` 权限码保留在清单中，但本次无用户编辑接口与按钮（与上游 Spec 一致）。
- 四个系统占位页（API 密钥 / 审计 / 告警 / 配置）仅做菜单入口与占位内容，不做实际功能。
- 未引入 Vitest / Jest，不覆盖组件级单测。
- Mock 数据为内存态，刷新或重启后重置；测试依赖同一进程内的 seed，不依赖外部持久化。
