from tests.helpers import (
    AUTH,
    create_agent,
    create_model,
    create_permission,
    create_provider,
    create_role,
    create_user,
    login_token,
)


async def _agent_user(db_session, username: str, *, data_scope: str = "own", codes=None):
    permissions = []
    for code in codes or []:
        permissions.append(await create_permission(db_session, code))
    role = await create_role(db_session, f"{username}_role", permissions)
    return await create_user(
        db_session, username, roles=[role], data_scope=data_scope, superuser=False
    )


async def test_agent_create_requires_permission(client, db_session):
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    response = await client.post(
        "/api/v1/agents", json={"name": "A", "type": "conversation"}, headers=AUTH(token)
    )
    assert response.json()["code"] == 403


async def test_agent_create_success(client, db_session):
    await _agent_user(db_session, "maker", codes=["agent:create"])
    token = await login_token(client, "maker")
    response = await client.post(
        "/api/v1/agents",
        json={"name": "客服助手", "type": "conversation", "config": {"temperature": 0.5}},
        headers=AUTH(token),
    )
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["status"] == "draft"
    assert body["data"]["version"] == "v0.1"
    assert body["data"]["created_by"] == "maker"


async def test_agent_create_invalid_type(client, db_session):
    await _agent_user(db_session, "maker2", codes=["agent:create"])
    token = await login_token(client, "maker2")
    response = await client.post(
        "/api/v1/agents", json={"name": "A", "type": "unknown"}, headers=AUTH(token)
    )
    assert response.json()["code"] == 400


async def test_agent_create_with_model(client, db_session):
    await _agent_user(db_session, "maker3", codes=["agent:create"])
    token = await login_token(client, "maker3")
    provider = await create_provider(db_session)
    model = await create_model(db_session, provider)
    ok = await client.post(
        "/api/v1/agents",
        json={"name": "带模型", "type": "analysis", "model_id": model.id},
        headers=AUTH(token),
    )
    missing = await client.post(
        "/api/v1/agents", json={"name": "坏模型", "type": "analysis", "model_id": 9999},
        headers=AUTH(token),
    )
    assert ok.json()["code"] == 200
    assert missing.json()["code"] == 404


async def test_agent_list_data_scope(client, db_session):
    await _agent_user(db_session, "owner", codes=["agent:list", "agent:read"])
    await _agent_user(db_session, "other", codes=["agent:list", "agent:read"])
    await create_agent(db_session, "我的 Agent", created_by="owner")
    await create_agent(db_session, "别人的 Agent", created_by="other")
    token = await login_token(client, "owner")
    listed = await client.get("/api/v1/agents", headers=AUTH(token))
    body = listed.json()
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["name"] == "我的 Agent"


async def test_agent_detail_out_of_scope_forbidden(client, db_session):
    await _agent_user(db_session, "viewer1", codes=["agent:read"])
    foreign = await create_agent(db_session, "外部 Agent", created_by="someone")
    token = await login_token(client, "viewer1")
    response = await client.get(f"/api/v1/agents/{foreign.id}", headers=AUTH(token))
    assert response.json()["code"] == 403


async def test_agent_all_scope_sees_everything(client, db_session):
    await _agent_user(db_session, "superops", data_scope="all", codes=["agent:list"])
    await create_agent(db_session, "A1", created_by="x")
    await create_agent(db_session, "A2", created_by="y")
    token = await login_token(client, "superops")
    response = await client.get("/api/v1/agents", headers=AUTH(token))
    assert response.json()["data"]["total"] == 2


async def test_agent_update_and_delete(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    agent = await create_agent(db_session, "待改")
    updated = await client.put(
        f"/api/v1/agents/{agent.id}",
        json={"name": "已改", "status": "inactive"},
        headers=AUTH(token),
    )
    assert updated.json()["data"]["name"] == "已改"
    deleted = await client.delete(f"/api/v1/agents/{agent.id}", headers=AUTH(token))
    missing = await client.get(f"/api/v1/agents/{agent.id}", headers=AUTH(token))
    assert deleted.json()["code"] == 200
    assert missing.json()["code"] == 404


async def test_agent_publish_versions_and_rollback(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    agent = await create_agent(db_session, "发布测试")

    first = await client.post(
        f"/api/v1/agents/{agent.id}/publish",
        json={"changelog": "首次发布"},
        headers=AUTH(token),
    )
    assert first.json()["data"]["version"] == "v0.2"
    assert first.json()["data"]["status"] == "active"

    second = await client.post(f"/api/v1/agents/{agent.id}/publish", headers=AUTH(token))
    assert second.json()["data"]["version"] == "v0.3"

    versions = await client.get(f"/api/v1/agents/{agent.id}/versions", headers=AUTH(token))
    items = versions.json()["data"]
    assert [v["version"] for v in items] == ["v0.3", "v0.2"]
    assert items[0]["is_current"] is True
    assert items[0]["published_by"] == "admin"

    rolled = await client.post(
        f"/api/v1/agents/{agent.id}/versions/v0.2/rollback", headers=AUTH(token)
    )
    assert rolled.json()["data"]["version"] == "v0.2"

    missing = await client.post(
        f"/api/v1/agents/{agent.id}/versions/v9.9/rollback", headers=AUTH(token)
    )
    assert missing.json()["code"] == 404


async def test_agent_test_and_monitor(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    agent = await create_agent(db_session, "调试助手", status="active")
    tested = await client.post(
        f"/api/v1/agents/{agent.id}/test", json={"input": "你好"}, headers=AUTH(token)
    )
    body = tested.json()["data"]
    assert body["success"] is True
    assert "你好" in body["output"]

    monitor = await client.get(f"/api/v1/agents/{agent.id}/monitor", headers=AUTH(token))
    assert monitor.json()["data"]["version"] == "v0.1"
    assert monitor.json()["data"]["recent_errors"] == []
