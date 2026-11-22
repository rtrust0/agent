from tests.helpers import (
    AUTH,
    create_permission,
    create_role,
    create_tool,
    create_user,
    login_token,
)


async def _admin(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    return await login_token(client, "admin")


async def test_tool_create_requires_permission(client, db_session):
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    response = await client.post(
        "/api/v1/tools", json={"name": "T", "type": "http_api"}, headers=AUTH(token)
    )
    assert response.json()["code"] == 403


async def test_tool_create_and_duplicate(client, db_session):
    token = await _admin(client, db_session)
    payload = {
        "name": "天气查询",
        "type": "http_api",
        "config": {"url": "https://api.weather.com"},
        "function_definition": {"name": "get_weather", "parameters": {}},
    }
    created = await client.post("/api/v1/tools", json=payload, headers=AUTH(token))
    duplicate = await client.post("/api/v1/tools", json=payload, headers=AUTH(token))
    body = created.json()["data"]
    assert body["status"] == "disabled"
    assert body["created_by"] == "admin"
    assert duplicate.json()["code"] == 400


async def test_tool_create_invalid_type(client, db_session):
    token = await _admin(client, db_session)
    response = await client.post(
        "/api/v1/tools", json={"name": "坏工具", "type": "shell"}, headers=AUTH(token)
    )
    assert response.json()["code"] == 400


async def test_tool_list_scope(client, db_session):
    permission = await create_permission(db_session, "tool:list")
    role = await create_role(db_session, "lister", [permission])
    await create_user(db_session, "owner", roles=[role], data_scope="own")
    await create_tool(db_session, "我的工具", created_by="owner")
    await create_tool(db_session, "别人的工具", created_by="other")
    token = await login_token(client, "owner")
    body = (await client.get("/api/v1/tools", headers=AUTH(token))).json()
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["name"] == "我的工具"


async def test_tool_detail_out_of_scope(client, db_session):
    permission = await create_permission(db_session, "tool:read")
    role = await create_role(db_session, "reader", [permission])
    await create_user(db_session, "reader", roles=[role], data_scope="own")
    foreign = await create_tool(db_session, "外部工具", created_by="x")
    token = await login_token(client, "reader")
    response = await client.get(f"/api/v1/tools/{foreign.id}", headers=AUTH(token))
    assert response.json()["code"] == 403


async def test_tool_update(client, db_session):
    token = await _admin(client, db_session)
    tool = await create_tool(db_session, "待改工具")
    updated = await client.put(
        f"/api/v1/tools/{tool.id}",
        json={"name": "已改工具", "description": "新描述", "config": {"url": "https://x.dev"}},
        headers=AUTH(token),
    )
    body = updated.json()["data"]
    assert body["name"] == "已改工具"
    assert body["config"]["url"] == "https://x.dev"


async def test_tool_toggle(client, db_session):
    token = await _admin(client, db_session)
    tool = await create_tool(db_session, "开关工具", status="disabled")
    enabled = await client.post(f"/api/v1/tools/{tool.id}/toggle", headers=AUTH(token))
    assert enabled.json()["data"]["status"] == "enabled"
    disabled = await client.post(f"/api/v1/tools/{tool.id}/toggle", headers=AUTH(token))
    assert disabled.json()["data"]["status"] == "disabled"


async def test_tool_test_success_and_failure(client, db_session):
    token = await _admin(client, db_session)
    configured = await create_tool(db_session, "已配置工具")
    bare = await create_tool(db_session, "未配置工具")
    bare.config = None
    await db_session.commit()

    ok = await client.post(
        f"/api/v1/tools/{configured.id}/test",
        json={"arguments": {"city": "北京"}},
        headers=AUTH(token),
    )
    failed = await client.post(f"/api/v1/tools/{bare.id}/test", headers=AUTH(token))
    assert ok.json()["data"]["success"] is True
    assert "city" in ok.json()["data"]["message"]
    assert failed.json()["data"]["success"] is False


async def test_tool_logs(client, db_session):
    token = await _admin(client, db_session)
    tool = await create_tool(db_session, "日志工具")
    tool.call_count_7d = 42
    tool.success_rate = 96.5
    tool.avg_latency = 320
    await db_session.commit()
    response = await client.get(f"/api/v1/tools/{tool.id}/logs", headers=AUTH(token))
    body = response.json()["data"]
    assert body["total"] == 0
    assert body["items"] == []
    assert body["summary"]["call_count_7d"] == 42
    assert body["summary"]["avg_latency"] == 320


async def test_tool_delete_and_not_found(client, db_session):
    token = await _admin(client, db_session)
    tool = await create_tool(db_session, "待删工具")
    deleted = await client.delete(f"/api/v1/tools/{tool.id}", headers=AUTH(token))
    missing = await client.get(f"/api/v1/tools/{tool.id}", headers=AUTH(token))
    assert deleted.json()["code"] == 200
    assert missing.json()["code"] == 404


async def test_tool_update_and_delete_out_of_scope(client, db_session):
    permissions = [
        await create_permission(db_session, code)
        for code in ("tool:update", "tool:delete")
    ]
    role = await create_role(db_session, "writer", permissions)
    await create_user(db_session, "writer", roles=[role], data_scope="own")
    foreign = await create_tool(db_session, "他人工具", created_by="someone")
    token = await login_token(client, "writer")
    updated = await client.put(
        f"/api/v1/tools/{foreign.id}", json={"name": "越权"}, headers=AUTH(token)
    )
    deleted = await client.delete(f"/api/v1/tools/{foreign.id}", headers=AUTH(token))
    assert updated.json()["code"] == 403
    assert deleted.json()["code"] == 403
