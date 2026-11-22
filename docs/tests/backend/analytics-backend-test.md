# 【analytics】后端模块测试报告

- 报告时间：2026-11-22
- 被测模块：数据统计模块（analytics）（`backend/app/modules/analytics/`，分层 api/service/repository/model/schema）
- 测试文件：`backend/tests/test_analytics.py`
- 执行命令：`cd backend && .venv/Scripts/python.exe -m pytest tests/test_analytics.py -q`
- 测试环境：Python 3.14 / FastAPI / SQLAlchemy 2.0（async）/ Pydantic v2；pytest + pytest-asyncio + httpx，内存 SQLite
- 用例结果：**6 passed / 0 failed**

## 一、接口覆盖

| # | 方法 | 路径 | 所需权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/analytics/overview` | analytics:read | 总量/成功率/平均延迟 | ✅ |
| 2 | GET | `/api/v1/analytics/daily` | analytics:read | 按日统计（补齐空白日期） | ✅ |
| 3 | GET | `/api/v1/analytics/by-agent` | analytics:read | 按 Agent 聚合 | ✅ |
| 4 | GET | `/api/v1/analytics/by-model` | analytics:read | 按模型聚合 | ✅ |
| 5 | GET | `/api/v1/analytics/costs` | analytics:read | 费用总额/单次均值/按日明细 | ✅ |
| 6 | GET | `/api/v1/analytics/evaluation` | analytics:read | 满意度/评分/待优化数 | ✅ |

> 未登录返回业务码 401、无权限返回业务码 403；各模块按上表权限码分别覆盖对应分支，具体见用例清单。

## 二、用例清单

- `test_analytics_requires_permission`
- `test_analytics_overview`
- `test_analytics_daily`
- `test_analytics_by_agent_and_model`
- `test_analytics_costs`
- `test_analytics_evaluation`

## 三、关键断言

- 成功率 = completed / total，保留两位小数
- 按模型聚合时未关联模型归入「未指定模型」
- 费用均值按对话数计算，0 对话时不除零

## 五、复现步骤

```bash
cd backend
python -m venv .venv                       # 首次执行
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest tests/test_analytics.py -q
```

报告由测试执行结果生成，`passed` 数量与实际用例数一致。
