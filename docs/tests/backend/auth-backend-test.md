# 【auth】后端模块测试报告

- 报告时间：2026-11-22
- 被测模块：认证模块（auth）（`backend/app/modules/auth/`，分层 api/service/repository/model/schema）
- 测试文件：`backend/tests/test_auth.py`
- 执行命令：`cd backend && .venv/Scripts/python.exe -m pytest tests/test_auth.py -q`
- 测试环境：Python 3.14 / FastAPI / SQLAlchemy 2.0（async）/ Pydantic v2；pytest + pytest-asyncio + httpx，内存 SQLite
- 用例结果：**4 passed / 0 failed**

## 一、接口覆盖

| # | 方法 | 路径 | 所需权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | POST | `/api/v1/auth/login` | 无需登录 | 登录成功 / 密码错误 / 用户不存在 / 账号禁用 + 登录审计落库 | ✅ |

> 未登录返回业务码 401、无权限返回业务码 403；各模块按上表权限码分别覆盖对应分支，具体见用例清单。

## 二、用例清单

- `test_login_success`
- `test_login_wrong_password`
- `test_login_unknown_user`
- `test_login_disabled_user`

## 三、关键断言

- 密码错误与用户不存在统一返回业务码 401，不泄露账号是否存在
- 禁用账号即使密码正确也返回 401
- 登录成功后 `audit_logs` 新增一条 module=auth、action=login 的记录

## 五、复现步骤

```bash
cd backend
python -m venv .venv                       # 首次执行
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest tests/test_auth.py -q
```

报告由测试执行结果生成，`passed` 数量与实际用例数一致。
