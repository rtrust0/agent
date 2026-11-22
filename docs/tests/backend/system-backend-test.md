# 【system】后端模块测试报告

- 报告时间：2026-11-22
- 被测模块：系统管理模块（system）（`backend/app/modules/system/`，分层 api/service/repository/model/schema）
- 测试文件：`backend/tests/test_system.py`
- 执行命令：`cd backend && .venv/Scripts/python.exe -m pytest tests/test_system.py -q`
- 测试环境：Python 3.14 / FastAPI / SQLAlchemy 2.0（async）/ Pydantic v2；pytest + pytest-asyncio + httpx，内存 SQLite
- 用例结果：**7 passed / 0 failed**

## 一、接口覆盖

| # | 方法 | 路径 | 所需权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/system/api-keys` | system:api_keys | 密钥列表 | ✅ |
| 2 | POST | `/api/v1/system/api-keys` | system:api_keys | 创建（自动生成 sk- 密钥） | ✅ |
| 3 | PUT | `/api/v1/system/api-keys/{id}` | system:api_keys | 更新状态/限流 | ✅ |
| 4 | DELETE | `/api/v1/system/api-keys/{id}` | system:api_keys | 删除 + 404 | ✅ |
| 5 | GET | `/api/v1/system/alerts/rules` | system:alerts | 告警规则列表 | ✅ |
| 6 | POST | `/api/v1/system/alerts/rules` | system:alerts | 创建规则 | ✅ |
| 7 | PUT | `/api/v1/system/alerts/rules/{id}` | system:alerts | 更新规则 | ✅ |
| 8 | DELETE | `/api/v1/system/alerts/rules/{id}` | system:alerts | 删除规则 | ✅ |
| 9 | GET | `/api/v1/system/alerts/active` | system:alerts | 活跃告警 | ✅ |
| 10 | POST | `/api/v1/system/alerts/{id}/acknowledge` | system:alerts | 确认告警 + 404 | ✅ |
| 11 | POST | `/api/v1/system/alerts/{id}/resolve` | system:alerts | 解决告警 + 重复解决 400 | ✅ |
| 12 | GET | `/api/v1/system/settings` | system:settings | 系统配置（无记录时自动初始化） | ✅ |
| 13 | PUT | `/api/v1/system/settings` | system:settings | 更新系统配置 | ✅ |

> 未登录返回业务码 401、无权限返回业务码 403；各模块按上表权限码分别覆盖对应分支，具体见用例清单。

## 二、用例清单

- `test_system_endpoints_require_permission`
- `test_api_key_crud`
- `test_alert_rule_crud`
- `test_alerts_acknowledge_and_resolve`
- `test_alert_not_found`
- `test_settings_get_creates_default_and_update`
- `test_system_write_operations_are_audited`

## 三、关键断言

- 密钥创建自动生成 `sk-` 前缀 32 位随机串
- 告警确认/解决状态机正确，已解决告警不可再次解决
- 系统配置 GET 首次访问自动创建默认行，后续复用同一行
- 系统写操作生成 `module=system` 审计记录

## 五、复现步骤

```bash
cd backend
python -m venv .venv                       # 首次执行
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest tests/test_system.py -q
```

报告由测试执行结果生成，`passed` 数量与实际用例数一致。
