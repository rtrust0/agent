# 【prompt】后端模块测试报告

- 报告时间：2026-11-22
- 被测模块：Prompt 管理模块（prompt）（`backend/app/modules/prompt/`，分层 api/service/repository/model/schema）
- 测试文件：`backend/tests/test_prompt.py`
- 执行命令：`cd backend && .venv/Scripts/python.exe -m pytest tests/test_prompt.py -q`
- 测试环境：Python 3.14 / FastAPI / SQLAlchemy 2.0（async）/ Pydantic v2；pytest + pytest-asyncio + httpx，内存 SQLite
- 用例结果：**11 passed / 0 failed**

## 一、接口覆盖

| # | 方法 | 路径 | 所需权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/prompts` | prompt:list | 分页 + 数据范围 | ✅ |
| 2 | POST | `/api/v1/prompts` | prompt:create | 创建（默认 draft / v0.1） | ✅ |
| 3 | GET | `/api/v1/prompts/{id}` | prompt:read | 详情 + 越权 403 | ✅ |
| 4 | PUT | `/api/v1/prompts/{id}` | prompt:update | 更新内容/变量 | ✅ |
| 5 | DELETE | `/api/v1/prompts/{id}` | prompt:delete | 删除 | ✅ |
| 6 | POST | `/api/v1/prompts/{id}/publish` | prompt:publish | 发布版本 | ✅ |
| 7 | GET | `/api/v1/prompts/{id}/versions` | prompt:read | 版本列表 | ✅ |
| 8 | POST | `/api/v1/prompts/{id}/versions/{version}/rollback` | prompt:publish | 回滚 | ✅ |
| 9 | POST | `/api/v1/prompts/{id}/test` | prompt:test | 变量渲染 + 缺失变量提示 | ✅ |

> 未登录返回业务码 401、无权限返回业务码 403；各模块按上表权限码分别覆盖对应分支，具体见用例清单。

## 二、用例清单

- `test_prompt_create_requires_permission`
- `test_prompt_create_and_detail`
- `test_prompt_list_data_scope`
- `test_prompt_detail_out_of_scope`
- `test_prompt_update`
- `test_prompt_publish_versions_and_rollback`
- `test_prompt_test_render`
- `test_prompt_delete`
- `test_prompt_update_cannot_publish_directly`
- `test_prompt_delete_out_of_scope_forbidden`
- `test_prompt_republish_after_rollback_no_duplicate_version`

## 三、关键断言

- 发布后状态置 `published` 且版本递增
- 回滚同时恢复历史内容与版本号
- 回滚后再次发布不会与历史版本重号
- `PUT /prompts/{id}` 不能直接把状态改为 published（必须走发布接口）
- `{{变量}}` 渲染缺失变量时保留占位符并返回 `missing_variables`

## 五、复现步骤

```bash
cd backend
python -m venv .venv                       # 首次执行
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest tests/test_prompt.py -q
```

报告由测试执行结果生成，`passed` 数量与实际用例数一致。
