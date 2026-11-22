# 【dashboard】后端模块测试报告

- 报告时间：2026-11-22
- 被测模块：工作台模块（dashboard）（`backend/app/modules/dashboard/`，分层 api/service/repository/model/schema）
- 测试文件：`backend/tests/test_dashboard.py`
- 执行命令：`cd backend && .venv/Scripts/python.exe -m pytest tests/test_dashboard.py -q`
- 测试环境：Python 3.14 / FastAPI / SQLAlchemy 2.0（async）/ Pydantic v2；pytest + pytest-asyncio + httpx，内存 SQLite
- 用例结果：**6 passed / 0 failed**

## 一、接口覆盖

| # | 方法 | 路径 | 所需权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/dashboard/stats` | dashboard:read | 总览计数（用户/角色/权限/Agent/模型/知识库/工具/对话） | ✅ |
| 2 | GET | `/api/v1/dashboard/trends` | dashboard:read | 近 N 日趋势（补齐空白日期） | ✅ |
| 3 | GET | `/api/v1/dashboard/top-agents` | dashboard:read | Agent 调用排行 | ✅ |
| 4 | GET | `/api/v1/dashboard/recent-alerts` | dashboard:read | 最近告警 | ✅ |
| 5 | GET | `/api/v1/dashboard/resource-usage` | dashboard:read | 资源用量 | ✅ |

> 未登录返回业务码 401、无权限返回业务码 403；各模块按上表权限码分别覆盖对应分支，具体见用例清单。

## 二、用例清单

- `test_dashboard_requires_permission`
- `test_dashboard_stats`
- `test_dashboard_trends_fill_missing_days`
- `test_dashboard_top_agents`
- `test_dashboard_recent_alerts`
- `test_dashboard_resource_usage`

## 三、关键断言

- 未授权用户访问返回业务码 403
- 趋势固定返回请求天数（缺失日期补 0）
- 排行按对话数倒序

## 五、复现步骤

```bash
cd backend
python -m venv .venv                       # 首次执行
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest tests/test_dashboard.py -q
```

报告由测试执行结果生成，`passed` 数量与实际用例数一致。
