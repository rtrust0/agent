# RBAC 授权功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为辰光 Agent 平台的用户/角色/权限管理接口加权限码拦截，新增"当前用户权限查询"接口，并让前端侧边栏菜单、操作按钮、路由守卫按当前用户权限差异化显示。

**Architecture:** 后端在 `src/core/deps.py` 新增一个可携带权限码的依赖工厂 `get_current_user_with_permission(permission_code)`，复用现有 `get_current_user()` 完成 JWT 身份认证后，遍历 `user.roles → role.permissions`（两者均已 `lazy="selectin"`）提取权限码集合做授权判定；在 user/role/permission 三个模块的 API 层给 17 个敏感接口注入该依赖。前端新增 `usePermissions` hook 拉取并缓存 `GET /users/me/permissions` 返回的权限码集合，供布局、页面、路由守卫消费 `hasPerm(code)`。

**Tech Stack:** FastAPI（依赖注入 + APIRouter）、SQLAlchemy 2.0 async ORM、Pydantic v2；React 19 + TypeScript（strict）+ Vite；pytest + pytest-asyncio（后端）；`npm run lint` + `npm run build`（前端验证）。

**Spec:** `docs/spec/PROJECT_SPEC_V2.md`（RBAC 授权功能，第 2.4~3.5 节；基础约定见 `docs/PROJECT_SPEC.md` V1）

## Global Constraints

- 权限码格式 `模块:操作`，全部小写；本次共 22 个权限码（逐字）：`user:list`, `user:read`, `user:create`, `user:update`, `user:delete`, `user:assign_roles`, `user:read_roles`, `role:list`, `role:read`, `role:create`, `role:update`, `role:delete`, `role:assign_permissions`, `permission:list`, `permission:read`, `permission:create`, `permission:update`, `permission:delete`, `system:api_keys`, `system:audit`, `system:alerts`, `system:settings`。
- 超级管理员 `User.is_superuser == True` 拥有全部权限：权限校验时直接放行，无需逐条匹配。
- 权限不足：`BizException(code=403, message="没有权限执行该操作")`，全局异常处理器返回 HTTP 200 + `{"code": 403, "message": "没有权限执行该操作", "data": null}`。
- 未登录 / token 过期：`get_current_user()` 抛 `BizException(code=401, ...)`；前端 `ApiClient.handleResponse` 在 HTTP 401 时清 token 并跳 `/login`（已实现，本次不改）。
- 后端路由统一 `/api/v1` 前缀，在 `src/main.py` 用 `app.include_router(router, prefix="/api/v1")` 注册；本次不新增路由模块、不改 `main.py` 注册逻辑。
- 响应包装：新接口 `GET /api/v1/users/me/permissions` 返回 `ResponseSchema[list[str]]`，`data` 为去重后的权限码字符串列表。
- 数据库：复用现有 `users`/`roles`/`permissions`/`user_roles`/`role_permissions` 表，ORM 模型不变，无新增 Alembic 迁移。
- 前端 `VITE_USE_MOCK` 开关（`app/src/services/config.ts`）：授权控制在 mock 与真实后端两种模式下都要工作；mock 模式返回预设的 22 个权限码。
- 后端表字段 snake_case；前端 api 层已做 camelCase→snake_case 转换（如 `is_active`、`role_ids`、`permission_ids`、`page_size`）。本次新增接口返回 `string[]`，无字段名映射问题。
- 前端类型是后端 Schema 的权威来源：`GET /users/me/permissions` 返回 `string[]`，前端 `getCurrentUserPermissions(): Promise<string[]>` 直接对应，不新增类型别名。

## Review Focus

1. **`user/api.py` 中端点函数名 `get_current_user` 遮蔽了 `from src.core.deps import get_current_user` 导入的依赖函数。** 新增 `/users/me/permissions` 端点若写 `Depends(get_current_user)` 会在装饰器求值时捕获到本地端点函数（自引用/递归）。→ 归属 Task 2：必须先把端点函数重命名为 `read_me`，并由 `test_me_permissions_depends_on_deps_get_current_user` 断言该路由的依赖解析到 `src.core.deps.get_current_user`（函数对象本体），而非本地端点。

2. **无任何角色、或角色无任何权限的用户访问受保护接口。** 期望 `get_user_permission_codes(user)` 返回空集、依赖抛 403，而不是因访问 `user.roles`/`role.permissions` 报错。→ 归属 Task 1：`test_get_user_permission_codes_empty_user` 断言 `make_user(codes=[])` 得到 `set()`；`test_permission_dep_denies_missing_code` 断言抛 `BizException(code=403)`。

3. **超级管理员即使未分配任何角色也要放行所有权限码。** 期望 `is_superuser=True` 时直接返回用户，不进入权限码集合比对。→ 归属 Task 1：`test_permission_dep_superuser_bypasses` 用 `superuser=True, codes=[]` 断言放行。

4. **权限码集合去重与返回顺序确定性。** 同一权限码可能来自多个角色，`/users/me/permissions` 必须去重；为保证前端展示与测试断言稳定，返回前 `sorted()`。→ 归属 Task 1 `test_get_user_permission_codes_dedup`（断言集合去重）、Task 2 `test_me_permissions_normal_user_dedup`（断言 `sorted` 后的精确列表）。

5. **前端权限码缓存在登录用户切换后未失效。** 模块级缓存必须按 `access_token` 键控：token 变化或清除时重新拉取/清空，否则退出登录再以低权限账号登录会复用上一个高权限账号的缓存。→ 归属 Task 5：`usePermissions` 的缓存以 `tokenStorage.get()` 为 key，token 为空时清空并返回空集；前端无测试运行器，以 `npm run build` 通过 + 手动切换账号验证。

6. **不在拦截清单内的全量列举接口仍无权限保护。** 按 Spec 2.5.3，`GET /users`（`list_users`）、`GET /roles/`（`get_roles`）、`GET /permissions/`（`list_permissions`）三个全量列举接口不注入权限依赖（前端分配角色/权限弹窗依赖它们）。这些接口保持开放是 Spec 的显式约定，实现时不得擅自加拦截。→ 归属 Task 3：`test_unlisted_list_routes_remain_open` 断言这三条路由不含 `get_current_user_with_permission` 依赖。

---

## File Structure

**后端（修改现有文件，不新建模块）**
- `src/core/deps.py` — 新增 `get_user_permission_codes(user)` 权限码集合工具 + `get_current_user_with_permission(permission_code)` 依赖工厂（本次授权核心）。
- `src/modules/user/api.py` — 新增 `GET /users/me/permissions` 端点；给 6 个用户接口注入权限依赖；重命名被遮蔽的 `get_current_user` 端点函数。
- `src/modules/role/api.py` — 给 6 个角色接口注入权限依赖。
- `src/modules/permission/api.py` — 给 5 个权限接口注入权限依赖。
- `test/test_rbac_authorization.py` — 新建：deps 单元测试 + 端点测试 + 路由接线测试（无需数据库，全部用内存 ORM 对象 / 依赖闭包检查）。

**前端（修改现有文件）**
- `app/src/services/api/system.ts` — 新增 `getCurrentUserPermissions(): Promise<string[]>`（调 `GET /users/me/permissions`）。
- `app/src/services/mock/system.ts` — 新增 `getCurrentUserPermissions(): Promise<string[]>`（返回预设 22 权限码）。
- `app/src/hooks/usePermissions.ts` — 新建：`usePermissions()` hook，按 token 键控缓存权限码集合，暴露 `hasPerm(code: string): boolean`。
- `app/src/layouts/DashboardLayout.tsx` — `systemMenuItems` 关联权限码并按 `hasPerm` 过滤；子项全无权限时隐藏"系统管理"父菜单。
- `app/src/pages/system/Users.tsx` / `Roles.tsx` / `Permissions.tsx` — 操作按钮按权限码条件渲染。
- `app/src/components/AuthGuard.tsx` — 新增可选 `requiredPermission?: string`，无权限时拦截。
- `app/src/App.tsx` — 给 7 条 `/system/*` 路由包裹带权限码的 `AuthGuard`。

---

### Task 1: 后端权限依赖函数（`src/core/deps.py`）

**Files:**
- Modify: `src/core/deps.py`
- Test: `test/test_rbac_authorization.py`（新建）

**Interfaces:**
- Produces:
  - `def get_user_permission_codes(user: User) -> set[str]` — 遍历 `user.roles` 中每个 `role.permissions`，返回去重后的 `permission.code` 集合。
  - `def get_current_user_with_permission(permission_code: str)` — 工厂函数，返回 async 依赖 `_check(current_user: User = Depends(get_current_user)) -> User`；`is_superuser` 直接返回，否则 `permission_code not in get_user_permission_codes(current_user)` 时 `raise BizException(code=403, message="没有权限执行该操作")`。

- [ ] **Step 1: 写失败测试** — 新建 `test/test_rbac_authorization.py`，内容如下（内存构造 ORM 对象，不连数据库）：

```python
import pytest
from src.core.deps import get_user_permission_codes, get_current_user_with_permission
from src.core.exceptions import BizException
from src.modules.user.model import User
from src.modules.role.model import Role
from src.modules.permission.model import Permission


def make_user(*, superuser=False, codes=()):
    user = User(username="u", email="u@x.com", hashed_password="x",
                is_active=True, is_superuser=superuser)
    role = Role(code="r1", name="r1")
    role.permissions = [Permission(code=c, name=c) for c in codes]
    user.roles = [role]
    return user


def test_get_user_permission_codes_dedup():
    user = make_user(codes=["user:list", "user:create"])
    role2 = Role(code="r2", name="r2")
    role2.permissions = [
        Permission(code="user:list", name="user:list"),
        Permission(code="role:read", name="role:read"),
    ]
    user.roles.append(role2)
    assert get_user_permission_codes(user) == {"user:list", "user:create", "role:read"}


def test_get_user_permission_codes_empty_user():
    assert get_user_permission_codes(make_user(codes=[])) == set()


@pytest.mark.asyncio
async def test_permission_dep_superuser_bypasses():
    dep = get_current_user_with_permission("role:delete")
    user = make_user(superuser=True, codes=[])
    assert await dep(user) is user


@pytest.mark.asyncio
async def test_permission_dep_grants_matching_code():
    dep = get_current_user_with_permission("user:read")
    user = make_user(codes=["user:read", "user:list"])
    assert await dep(user) is user


@pytest.mark.asyncio
async def test_permission_dep_denies_missing_code():
    dep = get_current_user_with_permission("role:delete")
    user = make_user(codes=["user:read"])
    with pytest.raises(BizException) as exc:
        await dep(user)
    assert exc.value.code == 403
    assert exc.value.message == "没有权限执行该操作"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest test/test_rbac_authorization.py -v`
Expected: FAIL — `ImportError: cannot import name 'get_user_permission_codes' from 'src.core.deps'`

- [ ] **Step 3: 在 `src/core/deps.py` 实现两个函数**

在文件底部新增 `get_user_permission_codes` 与 `get_current_user_with_permission`，签名与上述 Interfaces 一致。内层 `_check` 只允许闭包捕获 `permission_code`（`BizException`、`get_user_permission_codes`、`get_current_user` 都走模块全局或默认参数，不得在 `_check` 内再引其他自由变量，以保证 Task 3 闭包检查只含一个 cell）。

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest test/test_rbac_authorization.py -v`
Expected: 5 passed

- [ ] **Step 5: 提交**

```bash
git add src/core/deps.py test/test_rbac_authorization.py
git commit -m "feat: 新增权限码集合工具与带权限码的当前用户依赖"
```

---

### Task 2: 后端 `/users/me/permissions` 端点 + 用户接口权限依赖（`src/modules/user/api.py`）

**Files:**
- Modify: `src/modules/user/api.py`
- Test: `test/test_rbac_authorization.py`（追加）

**Interfaces:**
- Consumes: `get_current_user`, `get_current_user_with_permission`, `get_user_permission_codes`（均来自 `src.core.deps`）；`PermissionRepository`（来自 `src.modules.permission.repository`）。
- Produces:
  - 路由 `GET /api/v1/users/me/permissions`，`response_model=ResponseSchema[list[str]]`，端点函数 `get_my_permissions(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> ResponseSchema[list[str]]`；超管走 `PermissionRepository(db).get_all()` 收集全部权限码，非超管走 `get_user_permission_codes(current_user)`，两种路径都 `sorted(...)` 后放入 `data`。
  - 6 个用户接口各加一个 `current_user: User = Depends(get_current_user_with_permission("..."))` 参数：`create_user`→`user:create`，`list_search_results`→`user:list`，`get_user`→`user:read`，`delete_user`→`user:delete`，`user_assign_roles`→`user:assign_roles`，`get_user_roles_list`→`user:read_roles`。`/users/me`、`/users/me/permissions`、`/users`（`list_users`）不加。

- [ ] **Step 1: 写失败测试** — 在 `test/test_rbac_authorization.py` 追加：

```python
class _FakeResult:
    def __init__(self, items): self._items = items
    def scalars(self): return self
    def all(self): return self._items


class _FakeDb:
    def __init__(self, items): self._items = items
    async def execute(self, stmt): return _FakeResult(self._items)


@pytest.mark.asyncio
async def test_me_permissions_normal_user_dedup():
    from src.modules.user.api import get_my_permissions
    user = make_user(codes=["user:read", "role:list", "user:read"])
    resp = await get_my_permissions(current_user=user, db=None)
    assert resp.data == ["role:list", "user:read"]


@pytest.mark.asyncio
async def test_me_permissions_superuser_returns_all():
    from src.modules.user.api import get_my_permissions
    user = make_user(superuser=True)
    all_perms = [
        Permission(code="user:list", name="user:list"),
        Permission(code="role:delete", name="role:delete"),
    ]
    resp = await get_my_permissions(current_user=user, db=_FakeDb(all_perms))
    assert resp.data == ["role:delete", "user:list"]


def _flatten(dep):
    yield dep
    for sub in dep.dependencies:
        yield from _flatten(sub)


def test_me_permissions_depends_on_deps_get_current_user():
    from src.main import app
    from src.core import deps
    route = next(r for r in app.routes if getattr(r, "path", "") == "/api/v1/users/me/permissions")
    calls = {d.call for d in _flatten(route.dependant)}
    assert deps.get_current_user in calls
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest test/test_rbac_authorization.py -v`
Expected: FAIL — `ImportError: cannot import name 'get_my_permissions' from 'src.modules.user.api'`（或路由不存在）

- [ ] **Step 3: 改造 `src/modules/user/api.py`**

1. 顶部导入改为 `from src.core.deps import get_current_user, get_current_user_with_permission, get_user_permission_codes`（保留原有 `PageParams` 导入），并新增 `from src.modules.permission.repository import PermissionRepository`。
2. 将现有 `/me` 端点函数 `async def get_current_user(...)` 重命名为 `async def read_me(...)`（路由路径 `/me` 不变），消除对 deps 导入 `get_current_user` 的遮蔽。
3. 紧接 `/me` 之后新增 `@router.get("/me/permissions", response_model=ResponseSchema[list[str]], summary="获取当前用户权限码")` 端点 `get_my_permissions`，实现见 Interfaces。
4. 给上述 6 个端点函数各追加权限依赖参数（`user:list`/`user:read`/`user:create`/`user:delete`/`user:assign_roles`/`user:read_roles`）。

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest test/test_rbac_authorization.py -v`
Expected: 8 passed

- [ ] **Step 5: 提交**

```bash
git add src/modules/user/api.py test/test_rbac_authorization.py
git commit -m "feat: 新增当前用户权限查询接口并给用户接口加权限拦截"
```

---

### Task 3: 后端角色/权限接口权限依赖（`src/modules/role/api.py`、`src/modules/permission/api.py`）

**Files:**
- Modify: `src/modules/role/api.py`
- Modify: `src/modules/permission/api.py`
- Test: `test/test_rbac_authorization.py`（追加）

**Interfaces:**
- Consumes: `get_current_user_with_permission`（来自 `src.core.deps`）。
- Produces:
  - `role/api.py` 6 个端点加依赖：`create_role`→`role:create`，`list_search_results`→`role:list`，`get_role`→`role:read`，`update_role`→`role:update`，`delete_role`→`role:delete`，`update_role_permissions`→`role:assign_permissions`；`get_roles`（`GET /roles/`）不加。
  - `permission/api.py` 5 个端点加依赖：`create_permission`→`permission:create`，`list_search_results`→`permission:list`，`get_permission`→`permission:read`，`update_permission`→`permission:update`，`delete_permission`→`permission:delete`；`list_permissions`（`GET /permissions/`）不加。

- [ ] **Step 1: 写失败测试** — 在 `test/test_rbac_authorization.py` 追加（复用上一任务的 `_flatten`）：

```python
PROTECTED = [
    ("POST", "/api/v1/users", "user:create"),
    ("GET", "/api/v1/users/search", "user:list"),
    ("GET", "/api/v1/users/{user_id}", "user:read"),
    ("DELETE", "/api/v1/users/{user_id}", "user:delete"),
    ("PUT", "/api/v1/users/{user_id}/roles", "user:assign_roles"),
    ("GET", "/api/v1/users/{user_id}/roles", "user:read_roles"),
    ("POST", "/api/v1/roles", "role:create"),
    ("GET", "/api/v1/roles/search", "role:list"),
    ("GET", "/api/v1/roles/{role_id}", "role:read"),
    ("PUT", "/api/v1/roles/{role_id}", "role:update"),
    ("DELETE", "/api/v1/roles/{role_id}", "role:delete"),
    ("PUT", "/api/v1/roles/{role_id}/permissions", "role:assign_permissions"),
    ("POST", "/api/v1/permissions", "permission:create"),
    ("GET", "/api/v1/permissions/search", "permission:list"),
    ("GET", "/api/v1/permissions/{permission_id}", "permission:read"),
    ("PUT", "/api/v1/permissions/{permission_id}", "permission:update"),
    ("DELETE", "/api/v1/permissions/{permission_id}", "permission:delete"),
]

UNLISTED = [
    ("GET", "/api/v1/users"),
    ("GET", "/api/v1/roles/"),
    ("GET", "/api/v1/permissions/"),
]


def _route_perm_codes(route):
    codes = set()
    for dep in _flatten(route.dependant):
        call = dep.call
        if call is not None and getattr(call, "__qualname__", "").startswith(
            "get_current_user_with_permission"
        ):
            codes.add(call.__closure__[0].cell_contents)
    return codes


def test_protected_routes_wired():
    from src.main import app
    actual = {}
    for route in app.routes:
        for method in getattr(route, "methods", set()):
            for code in _route_perm_codes(route):
                actual[(method, route.path)] = code
    for method, path, code in PROTECTED:
        assert actual.get((method, path)) == code, f"{method} {path} -> {code}"


def test_unlisted_list_routes_remain_open():
    from src.main import app
    for route in app.routes:
        for method in getattr(route, "methods", set()):
            if (method, route.path) in UNLISTED:
                assert _route_perm_codes(route) == set()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest test/test_rbac_authorization.py::test_protected_routes_wired -v`
Expected: FAIL — 角色/权限路由缺权限码，`assert actual.get((method, path)) == code` 断言失败（用户 6 条已由 Task 2 满足）

- [ ] **Step 3: 给 `src/modules/role/api.py` 与 `src/modules/permission/api.py` 注入权限依赖**

分别在两个文件顶部导入 `get_current_user_with_permission`，并按 Interfaces 给对应端点函数追加 `current_user: User = Depends(get_current_user_with_permission("..."))` 参数（`User` 从 `src.modules.user.model` 导入；role/api.py 目前未导入 `User`，需新增）。

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest test/test_rbac_authorization.py -v`
Expected: 10 passed（Task 1 的 5 + Task 2 的 3 + 本任务 2）

- [ ] **Step 5: 提交**

```bash
git add src/modules/role/api.py src/modules/permission/api.py test/test_rbac_authorization.py
git commit -m "feat: 给角色与权限接口加权限码拦截"
```

---

### Task 4: 前端权限查询服务（`system.ts` + mock）

**Files:**
- Modify: `app/src/services/api/system.ts`
- Modify: `app/src/services/mock/system.ts`

**Interfaces:**
- Consumes: `apiClient`（已存在于 system.ts）；`mockPermissions` 无关，返回硬编码码表。
- Produces:
  - `apiSystemService.getCurrentUserPermissions(): Promise<string[]>` → `return apiClient.get('/users/me/permissions')`。
  - `mockSystemService.getCurrentUserPermissions(): Promise<string[]>` → 返回 `Promise.resolve([...22 个权限码])`（全部 22 个，见 Global Constraints，mock 模式模拟超管全量权限）。

- [ ] **Step 1: 写失败验证** — 前端无测试运行器，先不改代码，记录基线：

Run: `cd app && npm run build`
Expected: PASS（记录为基线，Step 3 改完后再次构建对比）

- [ ] **Step 2: 确认当前接口缺失**

在 `app/src/services/api/system.ts` 中确认 `apiSystemService` 尚无 `getCurrentUserPermissions`（mock 同理）。本步骤为检查动作，无输出。

- [ ] **Step 3: 实现两个 `getCurrentUserPermissions()`**

在 `app/src/services/api/system.ts` 的 `apiSystemService` 内新增 `getCurrentUserPermissions(): Promise<string[]>`（`apiClient.get('/users/me/permissions')`）；在 `app/src/services/mock/system.ts` 的 `mockSystemService` 内新增同名方法，返回 `Promise.resolve([...22 权限码])`（码表逐字复制自 Global Constraints）。

- [ ] **Step 4: 验证**

Run: `cd app && npm run lint && npm run build`
Expected: 无 lint 错误，build 成功（`getCurrentUserPermissions` 尚未被调用也不影响，若 TS 报未使用先忽略，Task 5 起被使用）

- [ ] **Step 5: 提交**

```bash
git add app/src/services/api/system.ts app/src/services/mock/system.ts
git commit -m "feat: 新增当前用户权限查询服务与 mock"
```

---

### Task 5: 前端 `usePermissions` hook（`app/src/hooks/usePermissions.ts`）

**Files:**
- Create: `app/src/hooks/usePermissions.ts`

**Interfaces:**
- Consumes: `tokenStorage`（`@/services/api/client`）、`USE_MOCK`（`@/services/config`）、`apiSystemService`（`@/services/api/system`）、`mockSystemService`（`@/services/mock/system`）。
- Produces: `export function usePermissions(): { hasPerm: (code: string) => boolean }` — 模块级缓存 `cachedToken: string | null` 与 `cachedPerms: Set<string> | null`，按 `tokenStorage.get()` 键控；未登录时清空并返回空集；`hasPerm(code)` 基于当前 `Set` 判定。内部状态用 `useState<Set<string> | null>`（`null` 表示未加载），`useEffect` 拉取一次并写入缓存。

- [ ] **Step 1: 写实现**（无测试运行器，此任务以"编译 + 逻辑自洽"为可检查结果）

新建 `app/src/hooks/usePermissions.ts`，实现签名与上述 Interfaces 一致。要点：token 为空 → 清 `cachedToken`/`cachedPerms` 并 `setPerms(null)`；token 与 `cachedToken` 相同且有缓存 → 直接复用；否则按 `USE_MOCK` 分支调用对应 `getCurrentUserPermissions()`，成功后 `new Set(codes)` 写入缓存并 setState，失败时 `setPerms(null)`（视同无权限）。`hasPerm = useCallback((code: string) => !!perms?.has(code), [perms])`。

- [ ] **Step 2: 验证**

Run: `cd app && npm run lint && npm run build`
Expected: 无 lint 错误（注意 `strict: true` / `noUnusedLocals`，不得引入未使用变量），build 成功

- [ ] **Step 3: 提交**

```bash
git add app/src/hooks/usePermissions.ts
git commit -m "feat: 新增权限码查询与缓存 hook"
```

---

### Task 6: 前端侧边栏菜单权限过滤（`app/src/layouts/DashboardLayout.tsx`）

**Files:**
- Modify: `app/src/layouts/DashboardLayout.tsx`

**Interfaces:**
- Consumes: `usePermissions`（`@/hooks/usePermissions`）。
- Produces: `systemMenuItems` 每项新增 `permission` 字段（映射见下），渲染前过滤：`const visibleSystemItems = systemMenuItems.filter(i => hasPerm(i.permission))`；仅当 `visibleSystemItems.length > 0` 才渲染"系统管理"父菜单及其子项；`menuItems`（平台功能）不加权限、保持原样；面包屑 `getBreadcrumbs` 仍基于完整 `systemMenuItems`。

菜单权限码映射（逐字）：用户管理 `user:list`，角色管理 `role:list`，权限管理 `permission:list`，API密钥 `system:api_keys`，审计日志 `system:audit`，告警规则 `system:alerts`，系统配置 `system:settings`。

- [ ] **Step 1: 写失败验证**（无测试运行器，先记录当前构建基线）

Run: `cd app && npm run build`
Expected: PASS（基线）

- [ ] **Step 2: 实现菜单过滤**

在 `DashboardLayout.tsx` 顶部引入 `usePermissions` 并调用获取 `hasPerm`；给 `systemMenuItems` 每项加 `permission`；将侧边栏"系统管理"父菜单与其子项渲染改为基于 `visibleSystemItems`（父菜单当 `visibleSystemItems.length === 0` 时不渲染，子项 `map` 改为遍历 `visibleSystemItems`）。

- [ ] **Step 3: 验证**

Run: `cd app && npm run lint && npm run build`
Expected: 无 lint 错误，build 成功

- [ ] **Step 4: 提交**

```bash
git add app/src/layouts/DashboardLayout.tsx
git commit -m "feat: 侧边栏系统菜单按权限码过滤显示"
```

---

### Task 7: 前端系统页面按钮权限过滤（`Users.tsx` / `Roles.tsx` / `Permissions.tsx`）

**Files:**
- Modify: `app/src/pages/system/Users.tsx`
- Modify: `app/src/pages/system/Roles.tsx`
- Modify: `app/src/pages/system/Permissions.tsx`

**Interfaces:**
- Consumes: `usePermissions`（`@/hooks/usePermissions`）。
- Produces: 各页面顶部调用 `const { hasPerm } = usePermissions()`，按下方映射用 `hasPerm(...)` 包裹对应按钮/操作列，无权限不渲染（表格操作列整列隐藏）。

按钮权限码映射（逐字）：
- `Users.tsx`：添加用户 `user:create`；删除用户 `user:delete`；分配角色 `user:assign_roles`（当前已有 `!USE_MOCK` 条件，需 `&& hasPerm(...)` 叠加）。
- `Roles.tsx`：创建角色 `role:create`；编辑角色 `role:update`；删除角色 `role:delete`；分配权限 `role:assign_permissions`（`!USE_MOCK` 条件叠加）。
- `Permissions.tsx`：创建权限 `permission:create`；编辑权限 `permission:update`；删除权限 `permission:delete`。

- [ ] **Step 1: 写失败验证**（基线构建）

Run: `cd app && npm run build`
Expected: PASS（基线）

- [ ] **Step 2: 实现三个页面的按钮条件渲染**

在三个页面分别引入 `usePermissions` 并包裹对应按钮（见映射）。注意：分配角色/分配权限按钮原本就有 `!USE_MOCK` 判断，保持两者 `&&` 叠加；确保 `hasPerm` 在组件内被使用（满足 `noUnusedLocals`）。

- [ ] **Step 3: 验证**

Run: `cd app && npm run lint && npm run build`
Expected: 无 lint 错误，build 成功

- [ ] **Step 4: 提交**

```bash
git add app/src/pages/system/Users.tsx app/src/pages/system/Roles.tsx app/src/pages/system/Permissions.tsx
git commit -m "feat: 系统管理页面操作按钮按权限码显示"
```

---

### Task 8: 前端路由守卫扩展（`AuthGuard.tsx` + `App.tsx`）

**Files:**
- Modify: `app/src/components/AuthGuard.tsx`
- Modify: `app/src/App.tsx`

**Interfaces:**
- Consumes: `usePermissions`（`@/hooks/usePermissions`）、`authService`（`@/services/auth`，已存在）。
- Produces:
  - `AuthGuardProps` 新增 `requiredPermission?: string`。
  - `AuthGuard` 逻辑：未登录 → `<Navigate to="/login" state={{ from: location }} replace />`；`requiredPermission` 指定且权限未加载完（`ready === false`）→ 返回 `null`；`requiredPermission` 指定且 `!hasPerm(requiredPermission)` → `<Navigate to="/login" replace />`；否则渲染 `children`。
  - `App.tsx`：7 条 `/system/*` 路由改为 `<AuthGuard requiredPermission="...">` 包裹（`system/users`→`user:list`，`system/roles`→`role:list`，`system/permissions`→`permission:list`，`system/api-keys`→`system:api_keys`，`system/audit`→`system:audit`，`system/alerts`→`system:alerts`，`system/settings`→`system:settings`）。

- [ ] **Step 1: 写失败验证**（基线构建）

Run: `cd app && npm run build`
Expected: PASS（基线）

- [ ] **Step 2: 扩展 `AuthGuard.tsx`**

给 `AuthGuardProps` 增加 `requiredPermission?: string`，组件内调用 `usePermissions()` 获取 `hasPerm` 与 `ready`，按 Interfaces 实现拦截逻辑。

- [ ] **Step 3: 修改 `App.tsx` 路由**

将 7 条 `/system/*` 路由的 `element` 用带 `requiredPermission` 的 `AuthGuard` 包裹（其余路由保持 `element={<AuthGuard><DashboardLayout /></AuthGuard>}` 的父级包裹不变，系统子路由加第二层守卫）。

- [ ] **Step 4: 验证**

Run: `cd app && npm run lint && npm run build`
Expected: 无 lint 错误，build 成功

- [ ] **Step 5: 提交**

```bash
git add app/src/components/AuthGuard.tsx app/src/App.tsx
git commit -m "feat: 路由守卫支持按权限码拦截系统页面"
```

---

## Self-Review

**Spec 覆盖：** 2.5.1 依赖函数 → Task 1；2.5.2 `/users/me/permissions` → Task 2；2.5.3 接口拦截清单（17 条带权限码）→ Task 2（user 6）+ Task 3（role 6 + permission 5）；3.1 权限获取 → Task 4 + Task 5；3.2 菜单过滤 → Task 6；3.3 按钮过滤 → Task 7；3.4 路由守卫 → Task 8。无遗漏。

**类型一致性：** `get_user_permission_codes` / `get_current_user_with_permission` 在 Task 1 定义，Task 2/3 按同名同签名消费；前端 `getCurrentUserPermissions(): Promise<string[]>` 在 Task 4 定义，Task 5 消费；`hasPerm(code: string): boolean` 在 Task 5 定义，Task 6/7/8 消费。权限码字符串在 Global Constraints、Task 3 的 `PROTECTED`、Task 6/7/8 映射中逐字一致。

**Review Focus 落地：** 6 条已各映射到 Task 1/2/3/5 的测试或验证步骤。

**比例：** 计划以签名、测试断言、权限码清单为主，不含完整函数体转录；后端任务用 pytest（无需数据库），前端任务用 `npm run lint` + `npm run build` 验证。
