# 【audit】后端模块测试报告

- 报告时间：2026-11-22
- 被测模块：审计日志模块（audit）（`backend/app/modules/audit/`，分层 api/service/repository/model/schema）
- 测试文件：`backend/tests/test_audit.py`
- 执行命令：`cd backend && .venv/Scripts/python.exe -m pytest tests/test_audit.py -q`
- 测试环境：Python 3.14 / FastAPI / SQLAlchemy 2.0（async）/ Pydantic v2；pytest + pytest-asyncio + httpx，内存 SQLite
- 用例结果：**7 passed / 0 failed**

## 一、接口覆盖

| # | 方法 | 路径 | 所需权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/system/audit-logs` | system:audit | 分页 + module/action/username/时间过滤 | ✅ |
| 2 | GET | `/api/v1/system/audit-logs/export` | system:audit | CSV 导出（Content-Disposition） | ✅ |

> 未登录返回业务码 401、无权限返回业务码 403；各模块按上表权限码分别覆盖对应分支，具体见用例清单。

## 二、用例清单

- `test_login_writes_audit_log`
- `test_write_operation_writes_audit_log`
- `test_read_operation_not_audited`
- `test_audit_logs_require_permission`
- `test_audit_logs_filter_by_username`
- `test_audit_logs_export_csv`
- `test_audit_log_survives_user_deletion`

## 三、关键断言

- 登录与写操作落库，读操作不落库
- 按 module/action/username 过滤生效
- 用户删除后审计记录保留（`user_id` 可空）
- CSV 表头与内容正确

## 五、复现步骤

```bash
cd backend
python -m venv .venv                       # 首次执行
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest tests/test_audit.py -q
```

报告由测试执行结果生成，`passed` 数量与实际用例数一致。
