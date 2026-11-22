# 【conversation】后端模块测试报告

- 报告时间：2026-11-22
- 被测模块：对话日志模块（conversation）（`backend/app/modules/conversation/`，分层 api/service/repository/model/schema）
- 测试文件：`backend/tests/test_conversation.py`
- 执行命令：`cd backend && .venv/Scripts/python.exe -m pytest tests/test_conversation.py -q`
- 测试环境：Python 3.14 / FastAPI / SQLAlchemy 2.0（async）/ Pydantic v2；pytest + pytest-asyncio + httpx，内存 SQLite
- 用例结果：**9 passed / 0 failed**

## 一、接口覆盖

| # | 方法 | 路径 | 所需权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/conversations` | conversation:list | 分页 + status/agent 过滤 + 数据范围 | ✅ |
| 2 | GET | `/api/v1/conversations/{id}` | conversation:read | 详情 + 越权 403 + 404 | ✅ |
| 3 | GET | `/api/v1/conversations/{id}/turns` | conversation:read | 轮次（按 position 升序） | ✅ |
| 4 | GET | `/api/v1/turns/{turn_id}/trace` | conversation:read | 链路追踪 + 404 | ✅ |
| 5 | POST | `/api/v1/conversations/{id}/annotate` | conversation:annotate | 标注（评分 1-5 校验） | ✅ |
| 6 | GET | `/api/v1/conversations/{id}/export` | conversation:export | CSV 导出 | ✅ |

> 未登录返回业务码 401、无权限返回业务码 403；各模块按上表权限码分别覆盖对应分支，具体见用例清单。

## 二、用例清单

- `test_conversations_require_permission`
- `test_conversation_list_and_filters`
- `test_conversation_data_scope`
- `test_conversation_detail_forbidden_out_of_scope`
- `test_conversation_turns_and_trace`
- `test_conversation_annotate`
- `test_conversation_annotate_invalid_rating`
- `test_conversation_export_csv`
- `test_conversation_not_found`

## 三、关键断言

- `own` 数据范围按 `user_id` 过滤对话
- 越权访问他人对话详情返回 403
- 评分超出 1-5 由 Pydantic 返回 422
- 导出 CSV 每条轮次一行，含表头

## 五、复现步骤

```bash
cd backend
python -m venv .venv                       # 首次执行
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest tests/test_conversation.py -q
```

报告由测试执行结果生成，`passed` 数量与实际用例数一致。
