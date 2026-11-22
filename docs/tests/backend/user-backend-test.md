# 【user】后端模块测试报告

- 报告时间：2026-11-22
- 被测模块：用户模块（user）（`backend/app/modules/user/`，分层 api/service/repository/model/schema）
- 测试文件：`backend/tests/test_user.py`
- 执行命令：`cd backend && .venv/Scripts/python.exe -m pytest tests/test_user.py -q`
- 测试环境：Python 3.14 / FastAPI / SQLAlchemy 2.0（async）/ Pydantic v2；pytest + pytest-asyncio + httpx，内存 SQLite
- 用例结果：**17 passed / 0 failed**

## 一、接口覆盖

| # | 方法 | 路径 | 所需权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/users` | 仅登录 | 全量列表（前端分配角色弹窗依赖） | ✅ |
| 2 | GET | `/api/v1/users/search` | user:list | 分页 + 关键字 + 数据范围过滤 | ✅ |
| 3 | POST | `/api/v1/users` | user:create | 创建校验：空用户名/重复用户名/重复邮箱 | ✅ |
| 4 | GET | `/api/v1/users/{id}` | user:read | 详情 + 404 | ✅ |
| 5 | PUT | `/api/v1/users/{id}` | user:update | 更新邮箱/状态/数据范围/密码 | ✅ |
| 6 | DELETE | `/api/v1/users/{id}` | user:delete | 删除 + 404 | ✅ |
| 7 | PUT | `/api/v1/users/{id}/roles` | user:assign_roles | 分配角色 + 角色不存在 400 | ✅ |
| 8 | GET | `/api/v1/users/{id}/roles` | user:read_roles | 用户角色列表 | ✅ |
| 9 | GET | `/api/v1/users/me` | 仅登录 | 当前用户信息 | ✅ |
| 10 | GET | `/api/v1/users/me/permissions` | 仅登录 | 去重排序；超管从库中实时推导全部权限码 | ✅ |

> 未登录返回业务码 401、无权限返回业务码 403；各模块按上表权限码分别覆盖对应分支，具体见用例清单。

## 二、用例清单

- `test_users_list_requires_login`
- `test_users_list_login_only`
- `test_user_search_requires_permission`
- `test_user_search_with_permission`
- `test_user_search_keyword`
- `test_user_detail`
- `test_user_create_validation`
- `test_user_create_success`
- `test_user_create_forbidden`
- `test_user_delete`
- `test_user_delete_not_found`
- `test_assign_roles`
- `test_get_user_roles`
- `test_me`
- `test_me_permissions_dedup_sorted`
- `test_me_permissions_superuser_all`
- `test_user_search_is_platform_level`

## 三、关键断言

- `/users/me/permissions` 返回去重且升序的权限码列表
- 超管返回数据库中全部已定义权限码（非代码常量）
- 用户目录属平台级数据：`data_scope=own` 的用户在搜索时也能看到全部用户（仅受 `user:list` 控制），避免只读角色「有权限却看到空列表」
- 创建用户未提供权限码时也需登录（401 分支覆盖）

## 五、复现步骤

```bash
cd backend
python -m venv .venv                       # 首次执行
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest tests/test_user.py -q
```

报告由测试执行结果生成，`passed` 数量与实际用例数一致。
