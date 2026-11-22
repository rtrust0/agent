from tests.helpers import (
    AUTH,
    create_knowledge_base,
    create_permission,
    create_role,
    create_user,
    login_token,
)

LONG_CONTENT = "辰光 Agent 平台支持知识库文档解析与检索。" * 8


async def _admin(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    return await login_token(client, "admin")


async def _kb_user(db_session, username: str, codes: list[str], *, data_scope: str = "own"):
    permissions = [await create_permission(db_session, code) for code in codes]
    role = await create_role(db_session, f"{username}_role", permissions)
    return await create_user(db_session, username, roles=[role], data_scope=data_scope)


async def test_kb_create_requires_permission(client, db_session):
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    response = await client.post(
        "/api/v1/knowledge-bases", json={"name": "KB"}, headers=AUTH(token)
    )
    assert response.json()["code"] == 403


async def test_kb_create_list_and_scope(client, db_session):
    await _kb_user(db_session, "owner", ["knowledge:create", "knowledge:list"])
    token = await login_token(client, "owner")
    created = await client.post(
        "/api/v1/knowledge-bases",
        json={"name": "产品知识库", "description": "手册", "chunk_size": 50, "chunk_overlap": 0},
        headers=AUTH(token),
    )
    body = created.json()["data"]
    assert body["status"] == "empty"
    assert body["created_by"] == "owner"
    assert body["chunk_size"] == 50

    await create_knowledge_base(db_session, "别人的库", created_by="someone")
    listed = await client.get("/api/v1/knowledge-bases", headers=AUTH(token))
    assert listed.json()["data"]["total"] == 1


async def test_kb_detail_out_of_scope(client, db_session):
    await _kb_user(db_session, "reader", ["knowledge:read"])
    foreign = await create_knowledge_base(db_session, "外部库", created_by="x")
    token = await login_token(client, "reader")
    response = await client.get(f"/api/v1/knowledge-bases/{foreign.id}", headers=AUTH(token))
    assert response.json()["code"] == 403


async def test_kb_update(client, db_session):
    token = await _admin(client, db_session)
    kb = await create_knowledge_base(db_session, "待改")
    updated = await client.put(
        f"/api/v1/knowledge-bases/{kb.id}",
        json={"name": "已改", "chunk_size": 200, "top_k": 8, "similarity_threshold": 0.2},
        headers=AUTH(token),
    )
    body = updated.json()["data"]
    assert body["name"] == "已改"
    assert body["chunk_size"] == 200
    assert body["top_k"] == 8
    assert body["similarity_threshold"] == 0.2


async def test_document_upload_creates_segments(client, db_session):
    token = await _admin(client, db_session)
    kb = await create_knowledge_base(db_session, "文档库")
    kb.chunk_size = 50
    kb.chunk_overlap = 0
    await db_session.commit()

    uploaded = await client.post(
        f"/api/v1/knowledge-bases/{kb.id}/documents",
        json={"file_name": "手册.txt", "file_type": "txt", "content": LONG_CONTENT},
        headers=AUTH(token),
    )
    body = uploaded.json()["data"]
    assert body["status"] == "completed"
    assert body["segment_count"] > 1
    assert body["uploaded_by"] == "admin"

    detail = await client.get(f"/api/v1/knowledge-bases/{kb.id}", headers=AUTH(token))
    assert detail.json()["data"]["status"] == "ready"
    assert detail.json()["data"]["document_count"] == 1
    assert detail.json()["data"]["segment_count"] == body["segment_count"]

    documents = await client.get(f"/api/v1/knowledge-bases/{kb.id}/documents", headers=AUTH(token))
    assert documents.json()["data"]["total"] == 1

    segments = await client.get(f"/api/v1/knowledge-bases/{kb.id}/segments", headers=AUTH(token))
    assert segments.json()["data"]["total"] == body["segment_count"]
    assert segments.json()["data"]["items"][0]["position"] == 1


async def test_document_upload_unsupported_type(client, db_session):
    token = await _admin(client, db_session)
    kb = await create_knowledge_base(db_session, "类型库")
    response = await client.post(
        f"/api/v1/knowledge-bases/{kb.id}/documents",
        json={"file_name": "a.exe", "file_type": "exe", "content": "x"},
        headers=AUTH(token),
    )
    assert response.json()["code"] == 400


async def test_document_retry_and_delete(client, db_session):
    token = await _admin(client, db_session)
    kb = await create_knowledge_base(db_session, "重试库")
    uploaded = await client.post(
        f"/api/v1/knowledge-bases/{kb.id}/documents",
        json={"file_name": "a.txt", "file_type": "txt", "content": "辰光平台"},
        headers=AUTH(token),
    )
    doc_id = uploaded.json()["data"]["id"]

    retried = await client.post(
        f"/api/v1/knowledge-bases/{kb.id}/documents/{doc_id}/retry", headers=AUTH(token)
    )
    assert retried.json()["data"]["status"] == "completed"

    deleted = await client.delete(
        f"/api/v1/knowledge-bases/{kb.id}/documents/{doc_id}", headers=AUTH(token)
    )
    assert deleted.json()["code"] == 200
    detail = await client.get(f"/api/v1/knowledge-bases/{kb.id}", headers=AUTH(token))
    assert detail.json()["data"]["document_count"] == 0
    assert detail.json()["data"]["segment_count"] == 0
    assert detail.json()["data"]["status"] == "empty"


async def test_segment_update_and_delete(client, db_session):
    token = await _admin(client, db_session)
    kb = await create_knowledge_base(db_session, "分段库")
    await client.post(
        f"/api/v1/knowledge-bases/{kb.id}/documents",
        json={"file_name": "b.txt", "file_type": "txt", "content": "第一段内容"},
        headers=AUTH(token),
    )
    segments = (
        await client.get(f"/api/v1/knowledge-bases/{kb.id}/segments", headers=AUTH(token))
    ).json()["data"]["items"]
    seg_id = segments[0]["id"]

    updated = await client.put(
        f"/api/v1/knowledge-bases/{kb.id}/segments/{seg_id}",
        json={"content": "修改后的分段内容，长度更长"},
        headers=AUTH(token),
    )
    assert updated.json()["data"]["content"].startswith("修改后")
    assert updated.json()["data"]["word_count"] == len("修改后的分段内容，长度更长")

    deleted = await client.delete(
        f"/api/v1/knowledge-bases/{kb.id}/segments/{seg_id}", headers=AUTH(token)
    )
    assert deleted.json()["code"] == 200
    detail = await client.get(f"/api/v1/knowledge-bases/{kb.id}", headers=AUTH(token))
    assert detail.json()["data"]["segment_count"] == 0


async def test_retrieval_test_and_reindex(client, db_session):
    token = await _admin(client, db_session)
    kb = await create_knowledge_base(db_session, "检索库")
    kb.similarity_threshold = 0.1
    await db_session.commit()
    await client.post(
        f"/api/v1/knowledge-bases/{kb.id}/documents",
        json={"file_name": "c.txt", "file_type": "txt", "content": "辰光平台支持检索测试"},
        headers=AUTH(token),
    )

    hit = await client.post(
        f"/api/v1/knowledge-bases/{kb.id}/retrieval-test",
        json={"query": "辰光平台"},
        headers=AUTH(token),
    )
    body = hit.json()["data"]
    assert body["hits"]
    assert body["hits"][0]["score"] > 0

    miss = await client.post(
        f"/api/v1/knowledge-bases/{kb.id}/retrieval-test",
        json={"query": "无关内容"},
        headers=AUTH(token),
    )
    assert miss.json()["data"]["hits"] == []

    reindexed = await client.post(
        f"/api/v1/knowledge-bases/{kb.id}/reindex", headers=AUTH(token)
    )
    assert reindexed.json()["data"]["status"] == "ready"
    assert reindexed.json()["data"]["document_count"] == 1


async def test_kb_delete_cascades(client, db_session):
    token = await _admin(client, db_session)
    kb = await create_knowledge_base(db_session, "待删库")
    await client.post(
        f"/api/v1/knowledge-bases/{kb.id}/documents",
        json={"file_name": "d.txt", "file_type": "txt", "content": "内容"},
        headers=AUTH(token),
    )
    deleted = await client.delete(f"/api/v1/knowledge-bases/{kb.id}", headers=AUTH(token))
    missing = await client.get(f"/api/v1/knowledge-bases/{kb.id}", headers=AUTH(token))
    assert deleted.json()["code"] == 200
    assert missing.json()["code"] == 404


async def test_document_on_missing_kb(client, db_session):
    token = await _admin(client, db_session)
    response = await client.post(
        "/api/v1/knowledge-bases/9999/documents",
        json={"file_name": "x.txt", "file_type": "txt", "content": "x"},
        headers=AUTH(token),
    )
    assert response.json()["code"] == 404
