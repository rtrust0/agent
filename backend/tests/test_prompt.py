from tests.helpers import (
    AUTH,
    create_permission,
    create_prompt,
    create_role,
    create_user,
    login_token,
)


async def _prompt_user(db_session, username: str, *, data_scope: str = "own", codes=None):
    permissions = []
    for code in codes or []:
        permissions.append(await create_permission(db_session, code))
    role = await create_role(db_session, f"{username}_role", permissions)
    return await create_user(db_session, username, roles=[role], data_scope=data_scope)


async def test_prompt_create_requires_permission(client, db_session):
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    response = await client.post(
        "/api/v1/prompts",
        json={"name": "P", "content": "hi"},
        headers=AUTH(token),
    )
    assert response.json()["code"] == 403


async def test_prompt_create_and_detail(client, db_session):
    await _prompt_user(db_session, "maker", codes=["prompt:create"])
    token = await login_token(client, "maker")
    created = await client.post(
        "/api/v1/prompts",
        json={
            "name": "客服提示词",
            "content": "你是 {{name}} 的客服",
            "tags": ["客服"],
            "variables": ["name"],
        },
        headers=AUTH(token),
    )
    body = created.json()
    assert body["code"] == 200
    assert body["data"]["version"] == "v0.1"
    assert body["data"]["status"] == "draft"
    assert body["data"]["created_by"] == "maker"

    detail_token = await login_token(client, "maker")
    detail = await client.get(f"/api/v1/prompts/{body['data']['id']}", headers=AUTH(detail_token))
    # 无 prompt:read 权限 → 403
    assert detail.json()["code"] == 403


async def test_prompt_list_data_scope(client, db_session):
    await _prompt_user(db_session, "owner", codes=["prompt:list"])
    await _prompt_user(db_session, "other", codes=["prompt:list"])
    await create_prompt(db_session, "我的", created_by="owner")
    await create_prompt(db_session, "别人的", created_by="other")
    token = await login_token(client, "owner")
    body = (await client.get("/api/v1/prompts", headers=AUTH(token))).json()
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["name"] == "我的"


async def test_prompt_detail_out_of_scope(client, db_session):
    await _prompt_user(db_session, "reader", codes=["prompt:read"])
    foreign = await create_prompt(db_session, "外部", created_by="someone")
    token = await login_token(client, "reader")
    response = await client.get(f"/api/v1/prompts/{foreign.id}", headers=AUTH(token))
    assert response.json()["code"] == 403


async def test_prompt_update(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    prompt = await create_prompt(db_session, "旧名")
    updated = await client.put(
        f"/api/v1/prompts/{prompt.id}",
        json={"name": "新名", "content": "新的内容 {{topic}}"},
        headers=AUTH(token),
    )
    body = updated.json()["data"]
    assert body["name"] == "新名"
    assert body["content"] == "新的内容 {{topic}}"
    assert body["version"] == "v0.1"


async def test_prompt_publish_versions_and_rollback(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    prompt = await create_prompt(db_session, "版本测试", content="v1 内容")

    first = await client.post(
        f"/api/v1/prompts/{prompt.id}/publish",
        json={"changelog": "首发"},
        headers=AUTH(token),
    )
    assert first.json()["data"]["version"] == "v0.2"
    assert first.json()["data"]["status"] == "published"

    prompt.content = "v2 内容"
    await db_session.commit()
    second = await client.post(f"/api/v1/prompts/{prompt.id}/publish", headers=AUTH(token))
    assert second.json()["data"]["version"] == "v0.3"

    versions = await client.get(f"/api/v1/prompts/{prompt.id}/versions", headers=AUTH(token))
    items = versions.json()["data"]
    assert [v["version"] for v in items] == ["v0.3", "v0.2"]
    assert items[0]["content"] == "v2 内容"

    rolled = await client.post(
        f"/api/v1/prompts/{prompt.id}/versions/v0.2/rollback", headers=AUTH(token)
    )
    assert rolled.json()["data"]["version"] == "v0.2"
    assert rolled.json()["data"]["content"] == "v1 内容"

    missing = await client.post(
        f"/api/v1/prompts/{prompt.id}/versions/v9.9/rollback", headers=AUTH(token)
    )
    assert missing.json()["code"] == 404


async def test_prompt_test_render(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    prompt = await create_prompt(db_session, "渲染", content="你好 {{name}}，你是 {{role}}")
    response = await client.post(
        f"/api/v1/prompts/{prompt.id}/test",
        json={"variables": {"name": "小明"}},
        headers=AUTH(token),
    )
    body = response.json()["data"]
    assert body["rendered"] == "你好 小明，你是 {{role}}"
    assert body["missing_variables"] == ["role"]

    full = await client.post(
        f"/api/v1/prompts/{prompt.id}/test",
        json={"variables": {"name": "小明", "role": "管理员"}},
        headers=AUTH(token),
    )
    assert full.json()["data"]["missing_variables"] == []


async def test_prompt_delete(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    prompt = await create_prompt(db_session, "待删")
    deleted = await client.delete(f"/api/v1/prompts/{prompt.id}", headers=AUTH(token))
    missing = await client.get(f"/api/v1/prompts/{prompt.id}", headers=AUTH(token))
    assert deleted.json()["code"] == 200
    assert missing.json()["code"] == 404


async def test_prompt_update_cannot_publish_directly(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    prompt = await create_prompt(db_session, "未发布")
    response = await client.put(
        f"/api/v1/prompts/{prompt.id}", json={"status": "published"}, headers=AUTH(token)
    )
    assert response.json()["code"] == 400
    detail = await client.get(f"/api/v1/prompts/{prompt.id}", headers=AUTH(token))
    assert detail.json()["data"]["status"] == "draft"


async def test_prompt_delete_out_of_scope_forbidden(client, db_session):
    await _prompt_user(db_session, "writer", codes=["prompt:delete"])
    foreign = await create_prompt(db_session, "他人 Prompt", created_by="someone")
    token = await login_token(client, "writer")
    response = await client.delete(f"/api/v1/prompts/{foreign.id}", headers=AUTH(token))
    assert response.json()["code"] == 403


async def test_prompt_republish_after_rollback_no_duplicate_version(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    prompt = await create_prompt(db_session, "版本连续")
    await client.post(f"/api/v1/prompts/{prompt.id}/publish", headers=AUTH(token))
    await client.post(f"/api/v1/prompts/{prompt.id}/publish", headers=AUTH(token))
    await client.post(
        f"/api/v1/prompts/{prompt.id}/versions/v0.2/rollback", headers=AUTH(token)
    )
    republished = await client.post(
        f"/api/v1/prompts/{prompt.id}/publish", headers=AUTH(token)
    )
    assert republished.json()["data"]["version"] == "v0.4"
    versions = (
        await client.get(f"/api/v1/prompts/{prompt.id}/versions", headers=AUTH(token))
    ).json()["data"]
    assert [v["version"] for v in versions] == ["v0.4", "v0.3", "v0.2"]
