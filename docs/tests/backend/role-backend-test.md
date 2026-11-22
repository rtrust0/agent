# 【role】后端模块测试报告

- 报告时间：2026-11-22
- 被测模块：角色模块（role）（`backend/app/modules/role/`，分层 api/service/repository/model/schema）
- 测试文件：`backend/tests/test_role.py`
- 执行命令：`cd backend && .venv/Scripts/python.exe -m pytest tests/test_role.py -q`
- 测试环境：Python 3.14 / FastAPI / SQLAlchemy 2.0（async）/ Pydantic v2；pytest + pytest-asyncio + httpx，内存 SQLite
- 用例结果：**12 passed / 0 failed**

## 一、接口覆盖

| # | 方法 | 路径 | 所需权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/roles/` | 仅登录 | 全量列表 | ✅ |
| 2 | GET | `/api/v1/roles/search` | role:list | 分页 + 关键字 | ✅ |
| 3 | POST | `/api/v1/roles` | role:create | 创建 + 编码重复 400 | ✅ |
| 4 | GET | `/api/v1/roles/{id}` | role:read | 详情 + 404 | ✅ |
| 5 | PUT | `/api/v1/roles/{id}` | role:update | 更新名称/描述 | ✅ |
| 6 | DELETE | `/api/v1/roles/{id}` | role:delete | 删除 + 内置角色 400 | ✅ |
| 7 | PUT | `/api/v1/roles/{id}/permissions` | role:assign_permissions | 分配权限 + 非法权限 ID 400 | ✅ |

> 未登录返回业务码 401、无权限返回业务码 403；各模块按上表权限码分别覆盖对应分支，具体见用例清单。

## 二、用例清单

- `test_roles_list_login_only`
- `test_roles_list_requires_login`
- `test_role_search_forbidden`
- `test_role_search_with_permission`
- `test_role_create_success`
- `test_role_create_duplicate_code`
- `test_role_create_forbidden`
- `test_role_detail_and_not_found`
- `test_role_update`
- `test_role_delete_and_builtin_guard`
- `test_role_assign_permissions`
- `test_role_assign_permissions_invalid_id`

## 三、关键断言

- 角色列表与权限分配接口的鉴权边界正确（403/401）
- `super_admin` 内置角色不可删除
- 分配权限后响应内联返回角色当前权限集合
- 写操作带审计（见 audit 报告）

## 五、复现步骤

```bash
cd backend
python -m venv .venv                       # 首次执行
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest tests/test_role.py -q
```

报告由测试执行结果生成，`passed` 数量与实际用例数一致。
