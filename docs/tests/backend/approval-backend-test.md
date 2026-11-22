# 【approval】后端模块测试报告

- 报告时间：2026-11-22
- 被测模块：权限申请与审批模块（approval）（`backend/app/modules/approval/`，分层 api/service/repository/model/schema）
- 测试文件：`backend/tests/test_approval.py`
- 执行命令：`cd backend && .venv/Scripts/python.exe -m pytest tests/test_approval.py -q`
- 测试环境：Python 3.14 / FastAPI / SQLAlchemy 2.0（async）/ Pydantic v2；pytest + pytest-asyncio + httpx，内存 SQLite
- 用例结果：**9 passed / 0 failed**

## 一、接口覆盖

| # | 方法 | 路径 | 所需权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | POST | `/api/v1/approvals/apply` | approval:apply | 发起申请 + 重复申请 400 + 权限码不存在 404 | ✅ |
| 2 | GET | `/api/v1/approvals/my` | approval:apply | 我的申请分页 | ✅ |
| 3 | GET | `/api/v1/approvals/list` | approval:audit | 审批列表 + status 过滤 | ✅ |
| 4 | PUT | `/api/v1/approvals/{id}/audit` | approval:audit | 通过/拒绝 + 重复审批 400 + 404 | ✅ |

> 未登录返回业务码 401、无权限返回业务码 403；各模块按上表权限码分别覆盖对应分支，具体见用例清单。

## 二、用例清单

- `test_apply_requires_login_and_permission`
- `test_apply_success_and_duplicate`
- `test_apply_unknown_permission_and_empty_reason`
- `test_my_applications`
- `test_approval_list_requires_audit_permission`
- `test_approve_grants_permission_immediately`
- `test_reject_does_not_grant`
- `test_audit_processed_application_twice`
- `test_expired_grant_not_effective`

## 三、关键断言

- 审批通过后权限立即可用于鉴权（`/users/me/permissions` 同步可见）
- 拒绝不授予权限
- `expired_at` 已过期的历史授权不再计入有效权限（到期自动回收）
- 处理过的申请不可重复审批

## 五、复现步骤

```bash
cd backend
python -m venv .venv                       # 首次执行
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest tests/test_approval.py -q
```

报告由测试执行结果生成，`passed` 数量与实际用例数一致。
