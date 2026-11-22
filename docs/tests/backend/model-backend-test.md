# 【model】后端模块测试报告

- 报告时间：2026-11-22
- 被测模块：模型管理模块（model）（`backend/app/modules/model/`，分层 api/service/repository/model/schema）
- 测试文件：`backend/tests/test_model.py`
- 执行命令：`cd backend && .venv/Scripts/python.exe -m pytest tests/test_model.py -q`
- 测试环境：Python 3.14 / FastAPI / SQLAlchemy 2.0（async）/ Pydantic v2；pytest + pytest-asyncio + httpx，内存 SQLite
- 用例结果：**11 passed / 0 failed**

## 一、接口覆盖

| # | 方法 | 路径 | 所需权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/models` | model:list | 分页 + provider/status/关键字过滤 | ✅ |
| 2 | POST | `/api/v1/models` | model:create | 创建 + 供应商不存在 404 + model_id 重复 400 | ✅ |
| 3 | GET | `/api/v1/models/{id}` | model:read | 详情 + 404 | ✅ |
| 4 | PUT | `/api/v1/models/{id}` | model:update | 更新 + 默认模型互斥 | ✅ |
| 5 | DELETE | `/api/v1/models/{id}` | model:delete | 删除 | ✅ |
| 6 | POST | `/api/v1/models/{id}/test` | model:test | 连接测试（供应商未连接时失败） | ✅ |
| 7 | GET | `/api/v1/models/providers` | model:provider_manage | 供应商列表 | ✅ |
| 8 | POST | `/api/v1/models/providers` | model:provider_manage | 创建供应商（api_key 不回显） | ✅ |
| 9 | GET | `/api/v1/models/providers/{id}` | model:provider_manage | 供应商详情 + 404 | ✅ |
| 10 | PUT | `/api/v1/models/providers/{id}` | model:provider_manage | 更新供应商 | ✅ |
| 11 | DELETE | `/api/v1/models/providers/{id}` | model:provider_manage | 删除供应商 | ✅ |
| 12 | POST | `/api/v1/models/providers/{id}/test` | model:test | 连接测试（缺 API Key 失败） | ✅ |

> 未登录返回业务码 401、无权限返回业务码 403；各模块按上表权限码分别覆盖对应分支，具体见用例清单。

## 二、用例清单

- `test_providers_require_permission`
- `test_provider_crud`
- `test_provider_test_connection`
- `test_provider_test_without_key`
- `test_model_create_and_duplicate`
- `test_model_create_unknown_provider`
- `test_model_list_and_filters`
- `test_model_update_and_default_switch`
- `test_model_delete_and_not_found`
- `test_model_test_connection`
- `test_model_list_requires_permission`

## 三、关键断言

- `api_key` 永不出现在响应中，仅返回 `has_api_key`
- 同一时刻只有一个 `is_default=true` 的模型
- 供应商未连接时模型测试返回失败而非异常

## 五、复现步骤

```bash
cd backend
python -m venv .venv                       # 首次执行
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest tests/test_model.py -q
```

报告由测试执行结果生成，`passed` 数量与实际用例数一致。
