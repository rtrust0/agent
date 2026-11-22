# 【permission】后端模块测试报告

- 报告时间：2026-11-22
- 被测模块：权限模块（permission）（`backend/app/modules/permission/`，分层 api/service/repository/model/schema）
- 测试文件：`backend/tests/test_permission.py`
- 执行命令：`cd backend && .venv/Scripts/python.exe -m pytest tests/test_permission.py -q`
- 测试环境：Python 3.14 / FastAPI / SQLAlchemy 2.0（async）/ Pydantic v2；pytest + pytest-asyncio + httpx，内存 SQLite
- 用例结果：**9 passed / 0 failed**

## 一、接口覆盖

| # | 方法 | 路径 | 所需权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/permissions/` | 仅登录 | 全量列表（含 module 派生字段） | ✅ |
| 2 | GET | `/api/v1/permissions/search` | permission:list | 分页 + 关键字 | ✅ |
| 3 | POST | `/api/v1/permissions` | permission:create | 创建 + 格式校验 + 重复 400 | ✅ |
| 4 | GET | `/api/v1/permissions/{id}` | permission:read | 详情 + 404 | ✅ |
| 5 | PUT | `/api/v1/permissions/{id}` | permission:update | 更新名称/描述，code 不可改 | ✅ |
| 6 | DELETE | `/api/v1/permissions/{id}` | permission:delete | 删除 | ✅ |

> 未登录返回业务码 401、无权限返回业务码 403；各模块按上表权限码分别覆盖对应分支，具体见用例清单。

## 二、用例清单

- `test_permissions_list_login_only`
- `test_permissions_list_requires_login`
- `test_permission_search_forbidden`
- `test_permission_create_and_search`
- `test_permission_create_invalid_code`
- `test_permission_create_duplicate`
- `test_permission_detail_not_found`
- `test_permission_update_keeps_code`
- `test_permission_delete`

## 三、关键断言

- 权限码必须符合 `模块:操作` 全小写格式
- `module` 字段由权限码前缀派生，供前端分组展示
- 更新权限不会改变权限码

## 五、复现步骤

```bash
cd backend
python -m venv .venv                       # 首次执行
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest tests/test_permission.py -q
```

报告由测试执行结果生成，`passed` 数量与实际用例数一致。
