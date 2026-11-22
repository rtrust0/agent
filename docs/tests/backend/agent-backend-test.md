# 【agent】后端模块测试报告

- 报告时间：2026-11-22
- 被测模块：Agent 管理模块（agent）（`backend/app/modules/agent/`，分层 api/service/repository/model/schema）
- 测试文件：`backend/tests/test_agent.py`
- 执行命令：`cd backend && .venv/Scripts/python.exe -m pytest tests/test_agent.py -q`
- 测试环境：Python 3.14 / FastAPI / SQLAlchemy 2.0（async）/ Pydantic v2；pytest + pytest-asyncio + httpx，内存 SQLite
- 用例结果：**10 passed / 0 failed**

## 一、接口覆盖

| # | 方法 | 路径 | 所需权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/agents` | agent:list | 分页 + status/type 过滤 + 数据范围 | ✅ |
| 2 | POST | `/api/v1/agents` | agent:create | 创建（类型校验、模型存在性校验） | ✅ |
| 3 | GET | `/api/v1/agents/{id}` | agent:read | 详情 + 数据范围 403 | ✅ |
| 4 | PUT | `/api/v1/agents/{id}` | agent:update | 更新 | ✅ |
| 5 | DELETE | `/api/v1/agents/{id}` | agent:delete | 删除 | ✅ |
| 6 | POST | `/api/v1/agents/{id}/publish` | agent:publish | 发布：版本自增 + 旧版本下线 | ✅ |
| 7 | GET | `/api/v1/agents/{id}/versions` | agent:read | 版本列表（倒序 + is_current） | ✅ |
| 8 | POST | `/api/v1/agents/{id}/versions/{version}/rollback` | agent:publish | 回滚 + 不存在版本 404 | ✅ |
| 9 | POST | `/api/v1/agents/{id}/test` | agent:test | 调试测试 | ✅ |
| 10 | GET | `/api/v1/agents/{id}/monitor` | agent:monitor | 监控指标 | ✅ |

> 未登录返回业务码 401、无权限返回业务码 403；各模块按上表权限码分别覆盖对应分支，具体见用例清单。

## 二、用例清单

- `test_agent_create_requires_permission`
- `test_agent_create_success`
- `test_agent_create_invalid_type`
- `test_agent_create_with_model`
- `test_agent_list_data_scope`
- `test_agent_detail_out_of_scope_forbidden`
- `test_agent_all_scope_sees_everything`
- `test_agent_update_and_delete`
- `test_agent_publish_versions_and_rollback`
- `test_agent_test_and_monitor`

## 三、关键断言

- `own` 数据范围只能看到 `created_by=本人用户名` 的 Agent，`all` 可见全量
- 访问他人 Agent 详情返回 403
- 发布版本号按 `v0.1 → v0.2 → v0.3` 递增且只有一个 `is_current`
- 回滚后 Agent 版本与配置同步回退

## 五、复现步骤

```bash
cd backend
python -m venv .venv                       # 首次执行
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest tests/test_agent.py -q
```

报告由测试执行结果生成，`passed` 数量与实际用例数一致。
