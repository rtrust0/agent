# 【knowledge】后端模块测试报告

- 报告时间：2026-11-22
- 被测模块：知识库模块（knowledge）（`backend/app/modules/knowledge/`，分层 api/service/repository/model/schema）
- 测试文件：`backend/tests/test_knowledge.py`
- 执行命令：`cd backend && .venv/Scripts/python.exe -m pytest tests/test_knowledge.py -q`
- 测试环境：Python 3.14 / FastAPI / SQLAlchemy 2.0（async）/ Pydantic v2；pytest + pytest-asyncio + httpx，内存 SQLite
- 用例结果：**11 passed / 0 failed**

## 一、接口覆盖

| # | 方法 | 路径 | 所需权限码 | 覆盖场景 | 结果 |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/knowledge-bases` | knowledge:list | 分页 + 数据范围 | ✅ |
| 2 | POST | `/api/v1/knowledge-bases` | knowledge:create | 创建（分块/检索配置） | ✅ |
| 3 | GET | `/api/v1/knowledge-bases/{id}` | knowledge:read | 详情 + 越权 403 + 404 | ✅ |
| 4 | PUT | `/api/v1/knowledge-bases/{id}` | knowledge:update | 更新配置 | ✅ |
| 5 | DELETE | `/api/v1/knowledge-bases/{id}` | knowledge:delete | 删除（级联文档/分段） | ✅ |
| 6 | GET | `/api/v1/knowledge-bases/{id}/documents` | knowledge:read | 文档列表 | ✅ |
| 7 | POST | `/api/v1/knowledge-bases/{id}/documents` | knowledge:document_upload | 上传 + 分块 + 不支持类型 400 | ✅ |
| 8 | POST | `/api/v1/knowledge-bases/{id}/documents/{doc_id}/retry` | knowledge:document_upload | 重试 | ✅ |
| 9 | DELETE | `/api/v1/knowledge-bases/{id}/documents/{doc_id}` | knowledge:document_delete | 删除文档 | ✅ |
| 10 | GET | `/api/v1/knowledge-bases/{id}/segments` | knowledge:read | 分段列表 | ✅ |
| 11 | PUT | `/api/v1/knowledge-bases/{id}/segments/{seg_id}` | knowledge:document_delete | 更新分段 | ✅ |
| 12 | DELETE | `/api/v1/knowledge-bases/{id}/segments/{seg_id}` | knowledge:document_delete | 删除分段 | ✅ |
| 13 | POST | `/api/v1/knowledge-bases/{id}/retrieval-test` | knowledge:retrieval_test | 检索测试 | ✅ |
| 14 | POST | `/api/v1/knowledge-bases/{id}/reindex` | knowledge:reindex | 重新索引 | ✅ |

> 未登录返回业务码 401、无权限返回业务码 403；各模块按上表权限码分别覆盖对应分支，具体见用例清单。

## 二、用例清单

- `test_kb_create_requires_permission`
- `test_kb_create_list_and_scope`
- `test_kb_detail_out_of_scope`
- `test_kb_update`
- `test_document_upload_creates_segments`
- `test_document_upload_unsupported_type`
- `test_document_retry_and_delete`
- `test_segment_update_and_delete`
- `test_retrieval_test_and_reindex`
- `test_kb_delete_cascades`
- `test_document_on_missing_kb`

## 三、关键断言

- 上传后按 `chunk_size/chunk_overlap` 生成分段，文档与知识库计数同步
- 删除文档/分段后计数与状态（ready/empty）自动回写
- 检索测试按关键词打分并受 `similarity_threshold` 限制，命中的分段累加 `hit_count`
- 删除知识库级联清理文档与分段

## 五、复现步骤

```bash
cd backend
python -m venv .venv                       # 首次执行
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest tests/test_knowledge.py -q
```

报告由测试执行结果生成，`passed` 数量与实际用例数一致。
