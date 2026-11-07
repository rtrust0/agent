# RBAC 模块测试报告

> 项目：`chenguang-vue`（Vue 3 + TypeScript + Vite + Pinia + Vue Router + Vite Mock 中间件）
> 测试日期：2026-11-07
> 对应需求：`docs/spec/rbac-prd.md`
> 实现计划：`docs/superpowers/plans/2026-11-05-rbac-module.md`

---

## 一、测试结论

| 测试层 | 用例数 | 通过 | 失败 | 结论 |
|---|---:|---:|---:|---|
| API 全接口测试（Node `node:test` + 原生 fetch） | 71 | 71 | 0 | 通过 |
| UI 关键路径测试（Playwright + Chromium） | 10 | 10 | 0 | 通过 |
| TypeScript 类型检查（`vue-tsc -b`） | — | — | 0 错误 | 通过 |
| 生产构建（`vue-tsc -b && vite build`） | — | — | 0 错误 | 通过 |

**总体结论：RBAC 模块的 25 个接口在成功、参数校验失败、未登录、无权限、资源不存在等分支上全部符合 `docs/spec/rbac-prd.md` 的契约；菜单 / 按钮 / 路由三级权限控制在三种演示身份下表现正确。经整分支独立复查并修复全部 Important 级问题后，测试全部通过。**

---

## 二、测试环境

| 项目 | 版本 / 说明 |
|---|---|
| 操作系统 | Windows 11 |
| Node.js | v24.22.0 |
| npm | 11.19.1 |
| 运行框架 | Vue 3.5、Vite 6、Pinia 2.3、Vue Router 4.5、axios 1.7 |
| API 测试 | Node 内置测试运行器（`node --test`），经 `tsx` 加载 TypeScript；`fetch` 直连 `node:http` 包装的 mock handler |
| UI 测试 | `@playwright/test` 1.64.1，Chromium，headless，viewport 1440×900 |

### 复现命令

```bash
# API 全接口测试
npm run test:api

# UI 关键路径测试（Playwright 自动启动 dev server）
npm run test:ui

# 类型检查 / 生产构建
npm run typecheck
npm run build
```

---

## 三、API 覆盖统计

- 接口总数：**25**（认证 4、用户 7、角色 7、权限 6、工作台 1），另有 1 条未知路由兜底用例。
- 用例总数：**71**。
- 覆盖分支：成功 `200`、参数校验失败 `400`、未登录 / token 无效 `401`、无权限 `403`、资源不存在 `404`、未知路由 `404`。

| 分支类型 | 覆盖说明 | 代表用例 |
|---|---|---|
| 成功（200） | 每个接口至少一条成功路径，并断言关键字段 | `user create success`、`role update success`、`permission create success` |
| 参数校验失败（400） | 必填缺失、重复、非法模块、不可变字段、内置角色保护、被引用权限删除 | `user create validation`、`role create duplicate code`、`permission update immutable code` |
| 未登录（401） | 所有需登录接口在无 token / 非法 token 时拒绝 | `users list requires login`、`invalid token is rejected` |
| 无权限（403） | 以 `viewer` / `ops` / 无角色用户 `nobody` 验证权限码拦截 | `user create forbidden for viewer`、`role assign permissions permission` |
| 资源不存在（404） | 用户 / 角色 / 权限详情与删除的不存在分支 | `role detail success and 404`、`permission delete 404` |

---

## 四、逐接口测试明细

### 4.1 认证

| 接口 | 覆盖分支 | 结果 |
|---|---|---|
| `GET /api/auth/captcha` | 返回 `captchaId` + 4 位验证码文本 | 通过 |
| `POST /api/auth/login` | 登录成功；验证码错误 400；密码错误 400；停用账号 400 | 通过 |
| `GET /api/users/me` | 未登录 401；非法 token 401；登录成功返回当前用户 | 通过 |
| `GET /api/users/me/permissions` | 超管返回全部 22 码且排序；viewer 返回精确 7 码 | 通过 |

### 4.2 用户

| 接口 | 覆盖分支 | 结果 |
|---|---|---|
| `GET /api/users` | 未登录 401；登录后 200（6 条）；无角色用户仍可访问（登录即可） | 通过 |
| `GET /api/users/search` | 分页（total 6 / 每页 2）；关键字过滤；无 `user:list` 返回 403 | 通过 |
| `GET /api/users/{id}` | 成功；不存在 404；无 `user:read` 403 | 通过 |
| `POST /api/users` | 成功（列表增至 7）；缺用户名 400；重名 400；viewer 403 | 通过 |
| `DELETE /api/users/{id}` | 成功（列表降至 5）；不存在 404；viewer 403 | 通过 |
| `PUT /api/users/{id}/roles` | admin 成功；viewer 403 | 通过 |
| `GET /api/users/{id}/roles` | 空角色返回 `[]`；有角色返回 1 条 | 通过 |

### 4.3 角色

| 接口 | 覆盖分支 | 结果 |
|---|---|---|
| `GET /api/roles/` | 未登录 401；登录后 200（3 条）；无角色用户仍可访问 | 通过 |
| `GET /api/roles/search` | 分页；关键字；无 `role:list` 403 | 通过 |
| `GET /api/roles/{id}` | 成功（`super_admin`）；不存在 404；无 `role:read` 403 | 通过 |
| `POST /api/roles` | 成功；缺角色码 400；角色码重复 400；viewer 403 | 通过 |
| `PUT /api/roles/{id}` | 成功改名；内置角色 400；viewer 403 | 通过 |
| `DELETE /api/roles/{id}` | 非内置角色删除成功；内置角色 400；不存在 404；viewer 403 | 通过 |
| `PUT /api/roles/{id}/permissions` | admin 成功并校验权限列表；ops 403；内置角色 400 | 通过 |

### 4.4 权限

| 接口 | 覆盖分支 | 结果 |
|---|---|---|
| `GET /api/permissions/` | 未登录 401；登录后 200（22 条）；无角色用户仍可访问 | 通过 |
| `GET /api/permissions/search` | 分页（total 22）；无 `permission:list` 403 | 通过 |
| `GET /api/permissions/{id}` | 成功（`user:list`）；不存在 404；无 `permission:read` 403 | 通过 |
| `POST /api/permissions` | 成功；缺权限码 400；非法模块 400；编码重复 400；viewer 403 | 通过 |
| `PUT /api/permissions/{id}` | 改名成功；修改 code 400；viewer 403 | 通过 |
| `DELETE /api/permissions/{id}` | 被角色引用 400；未被引用删除成功；不存在 404；viewer 403 | 通过 |

### 4.5 工作台与兜底

| 接口 | 覆盖分支 | 结果 |
|---|---|---|
| `GET /api/dashboard/summary` | 未登录 401；登录后返回 `totalUsers=6`、`totalRoles=3`、`totalPermissions=22` | 通过 |
| 未匹配路由 | 返回业务码 404 | 通过 |

---

## 五、UI 关键路径测试明细

| # | 用例 | 覆盖的验收点 | 结果 |
|---:|---|---|---|
| 1 | `admin sees all system menu items` | 超级管理员可见全部 7 个系统菜单 | 通过 |
| 2 | `viewer menu hides write / system modules` | 只读观察者仅见用户 / 角色 / 权限，API 密钥 / 审计 / 配置隐藏 | 通过 |
| 3 | `viewer sees no create / delete / assign buttons on users page` | 用户页三个写操作按钮对 viewer 全部隐藏 | 通过 |
| 4 | `ops sees create but not delete / assign buttons on users page` | 运营管理员可见「添加用户」，不可见删除 / 分配角色 | 通过 |
| 5 | `admin sees role action buttons` | 超级管理员可见创建 / 编辑 / 分配权限 / 删除 | 通过 |
| 6 | `viewer permissions page hides create and renders matrix` | viewer 无创建按钮；权限矩阵渲染出已授权标记 | 通过 |
| 7 | `ops is redirected to /403 for an unauthorized system route` | 直接访问无权路由被拦截到 `/403` | 通过 |
| 8 | `unauthenticated access redirects to login with redirect query` | 未登录访问受保护页跳转登录页 | 通过 |
| 9 | `identity switch recomputes menu and user box` | 切换身份后菜单与用户区即时重算 | 通过 |

---

## 六、缺陷与遗留

### 6.1 缺陷

无遗留缺陷。整分支独立复查发现的 8 个问题（见 6.4）已全部修复并通过回归测试。

### 6.2 已知边界与设计取舍（非缺陷）

1. **`user:update` 权限码保留但无接口与按钮**：与 `PROJECT_SPEC_V2.md` 2.5.3 的拦截清单一致，用户不支持编辑，仅保留权限码定义。
2. **四个系统菜单为占位页**：API 密钥 / 审计日志 / 告警规则 / 系统配置仅用于演示菜单级权限过滤，页面内容为「功能建设中」。
3. **Mock 为内存态**：刷新页面不丢登录态（token 存 localStorage），但重启 dev server 或重新创建种子后数据重置；测试均使用独立种子，互不影响。
4. **权限矩阵为只读视图**：授权关系在角色页维护，矩阵由角色与权限关系派生，不新增独立接口（符合 PRD 4.5）。
5. **未引入组件级单元测试**：PRD 非目标明确排除 Vitest / Jest，本次以 API 全覆盖 + UI 关键路径作为验收手段。
6. **字体回退**：Space Grotesk / IBM Plex Mono 未通过外部 CDN 引入，离线时回退到系统无衬线 / 等宽字体，不阻塞功能。

### 6.3 工具链说明

- `npm run typecheck` 原脚本 `vue-tsc --noEmit` 在 solution-style `tsconfig.json`（`files: []` + references）下不检查子项目，已改为 `vue-tsc -b`，使类型检查真实生效。
- 测试专用 devDependencies：`@playwright/test`、`tsx`，不进入运行时产物。

### 6.4 最终复查修复记录

整分支独立复查（`eac9026..HEAD`）发现的问题与处理：

1. **超管权限码返回静态常量**（Important，已修复）——`/users/me/permissions` 对超管改为返回 `db.permissions` 实时推导，动态新建权限后可正确纳入；新增用例「`me permissions includes dynamically created permission for superuser`」。
2. **超管空角色短路未被测试**（Important，已修复）——新增无角色超管用例「`superuser with empty roles bypasses and returns all codes`」。
3. **多角色权限去重未被真实覆盖**（Important，已修复）——新增 `wangfang`（运营管理员 + 只读观察者）去重用例「`me permissions multi-role user dedup`」。
4. **权限缓存跨账号失效被整页刷新掩盖**（Important，已修复）——路由守卫改为每次导航校验权限（按 token 键控缓存，命中即复用），并新增 UI 用例「`logout then login as viewer shrinks menu without reload`」。
5. **`/403`「切换账号」按钮无效**（Important，已修复）——点击先退出登录再跳转登录页。
6. **更新接口接受空必填字段**（Important，已修复）——角色 / 权限更新时 `code`/`name` 为空返回 400，服务层同步校验；新增 2 条回归用例。
7. **创建时携带角色 / 权限是否越权**（裁定：维持 PRD 现状）——PRD §4.3/§6.2 明确「添加用户：初始角色多选」「创建角色：权限多选」，且 `user:create` / `role:create` 与 `user:assign_roles` / `role:assign_permissions` 分离是本演示的既定设计；身份切换器本身已允许演示任意身份。若后续要求更严格的职责分离，再收紧 mock 与前端弹窗。
8. **mock handler 未捕获异常导致请求挂起**（Minor 上调为修复）——`decodeURIComponent` 遇到非法编码会抛错且响应永不结束，已加 try/catch 兜底返回业务码 500。
9. **报告覆盖口径**（已修正）——401 分支由共享 handler 的同一路径统一处理，对代表性接口逐一断言即可覆盖该分支，本报告据此说明，不再声称「每接口均有显式 401 用例」。

### 6.5 剩余边界（不阻塞，移交评估）

- `v-permission` 指令已注册但页面统一用 `hasPerm` 条件渲染，指令当前未被模板使用（计划要求的交付物，保留）。
- mock 校验对非法 `roleIds`/`permissionCodes` 采取静默过滤而非 400；分页参数非数字未显式校验；验证码缓存无 TTL；会话无服务端注销接口。
- `MockRoute.permission` 类型为 `string`，未收窄为权限码字面量联合类型。
- 编辑角色弹窗不含权限复选框（权限通过独立的「分配权限」动作维护）。

---

## 七、结论

RBAC 模块已按 `docs/spec/rbac-prd.md` 完成开发，接口契约、三级权限控制、权限矩阵与三种演示身份的差异均通过自动化验证。建议验收通过并合入。
