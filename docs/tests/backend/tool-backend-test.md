# 【tool】后端模块测试报告

- 报告时间：2026-11-22
- 被测模块：工具管理模块（tool）（`backend/app/modules/tool/`，分层 api/service/repository/model/schema）
- 测试文件：`backend/tests/test_tool.py`
- 执行命令：`cd backend && .venv/Scripts/python.exe -m pytest tests/test_tool.py -q`
- 测试环境：Python 3.14 / FastAPI / SQLAlchemy 2.0（async）/ Pydantic v2；pytest + pytest-asyncio + httpx，内存 SQLite
- 用例结果：**10 passed / 0 failed**

## 一、接口覆盖

| # | 方法 | 路径 | 所需权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/tools` | tool:list | 分页 + 数据范围 | ✅ |
| 2 | POST | `/api/v1/tools` | tool:create | 注册 + 重名 400 + 类型非法 400 | ✅ |
| 3 | GET | `/api/v1/tools/{id}` | tool:read | 详情 + 越权 403 | ✅ |
| 4 | PUT | `/api/v1/tools/{id}` | tool:update | 更新 | ✅ |
| 5 | DELETE | `/api/v1/tools/{id}` | tool:delete | 删除 + 404 | ✅ |
| 6 | POST | `/api/v1/tools/{id}/test` | tool:test | 测试（未配置时失败） | ✅ |
| 7 | POST | `/api/v1/tools/{id}/toggle` | tool:toggle | 启用/禁用切换 | ✅ |
| 8 | GET | `/api/v1/tools/{id}/logs` | tool:read | 统计摘要 + 日志分页 | ✅ |

> 未登录返回业务码 401、无权限返回业务码 403；各模块按上表权限码分别覆盖对应分支，具体见用例清单。

## 二、用例清单

- `test_tool_create_requires_permission`
- `test_tool_create_and_duplicate`
- `test_tool_create_invalid_type`
- `test_tool_list_scope`
- `test_tool_detail_out_of_scope`
- `test_tool_update`
- `test_tool_toggle`
- `test_tool_test_success_and_failure`
- `test_tool_logs`
- `test_tool_delete_and_not_found`

## 三、关键断言

- 工具名唯一，类型限制为 builtin/http_api/custom_function
- toggle 幂等交替 enabled/disabled
- 未配置 `config/function_definition` 时测试返回失败

## 四、实现说明与已知限制

- `GET /tools/{id}/logs`：数据库中未设计工具调用日志表，接口返回 `summary`（调用量/成功率/平均延迟）+ 空日志分页，待后续补充日志表后接入真实明细。

## 五、复现步骤

```bash
cd backend
python -m venv .venv                       # 首次执行
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest tests/test_tool.py -q
```

报告由测试执行结果生成，`passed` 数量与实际用例数一致。
