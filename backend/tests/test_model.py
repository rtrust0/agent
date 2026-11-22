from tests.helpers import AUTH, create_model, create_provider, create_user, login_token


async def _plain(client, db_session):
    await create_user(db_session, "plain")
    return await login_token(client, "plain")


async def test_providers_require_permission(client, db_session):
    token = await _plain(client, db_session)
    response = await client.get("/api/v1/models/providers", headers=AUTH(token))
    assert response.json()["code"] == 403


async def test_provider_crud(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")

    created = await client.post(
        "/api/v1/models/providers",
        json={
            "name": "DeepSeek",
            "type": "openai",
            "endpoint": "https://api.deepseek.com/v1",
            "api_key": "sk-secret",
            "description": "国产模型",
        },
        headers=AUTH(token),
    )
    body = created.json()
    assert body["code"] == 200
    assert body["data"]["has_api_key"] is True
    assert "api_key" not in body["data"]
    provider_id = body["data"]["id"]

    listed = await client.get("/api/v1/models/providers", headers=AUTH(token))
    assert listed.json()["data"][0]["name"] == "DeepSeek"

    detail = await client.get(f"/api/v1/models/providers/{provider_id}", headers=AUTH(token))
    assert detail.json()["data"]["type"] == "openai"

    updated = await client.put(
        f"/api/v1/models/providers/{provider_id}",
        json={"name": "DeepSeek V3", "description": "改名"},
        headers=AUTH(token),
    )
    assert updated.json()["data"]["name"] == "DeepSeek V3"

    deleted = await client.delete(f"/api/v1/models/providers/{provider_id}", headers=AUTH(token))
    assert deleted.json()["code"] == 200
    missing = await client.get(f"/api/v1/models/providers/{provider_id}", headers=AUTH(token))
    assert missing.json()["code"] == 404


async def test_provider_test_connection(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    provider = await create_provider(db_session, "OpenAI", api_key="sk-demo")
    ok = await client.post(f"/api/v1/models/providers/{provider.id}/test", headers=AUTH(token))
    assert ok.json()["data"]["success"] is True
    assert ok.json()["data"]["latency_ms"] == 1


async def test_provider_test_without_key(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    provider = await create_provider(db_session, "NoKey", api_key="")
    result = await client.post(
        f"/api/v1/models/providers/{provider.id}/test", headers=AUTH(token)
    )
    assert result.json()["data"]["success"] is False
    assert result.json()["data"]["message"] == "未配置 API Key"


async def test_model_create_and_duplicate(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    provider = await create_provider(db_session)
    payload = {
        "name": "GPT-4o",
        "model_id": "gpt-4o",
        "provider_id": provider.id,
        "capabilities": ["chat", "vision"],
        "context_length": 128000,
        "input_price": 0.005,
        "output_price": 0.015,
        "is_default": True,
    }
    created = await client.post("/api/v1/models", json=payload, headers=AUTH(token))
    duplicate = await client.post("/api/v1/models", json=payload, headers=AUTH(token))
    body = created.json()
    assert body["code"] == 200
    assert body["data"]["provider_name"] == "OpenAI"
    assert body["data"]["capabilities"] == ["chat", "vision"]
    assert body["data"]["is_default"] is True
    assert duplicate.json()["code"] == 400


async def test_model_create_unknown_provider(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    response = await client.post(
        "/api/v1/models",
        json={"name": "X", "model_id": "x-1", "provider_id": 999},
        headers=AUTH(token),
    )
    assert response.json()["code"] == 404


async def test_model_list_and_filters(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    provider = await create_provider(db_session)
    await create_model(db_session, provider, "gpt-4o")
    await create_model(db_session, provider, "gpt-4o-mini")

    listed = await client.get("/api/v1/models?keyword=mini", headers=AUTH(token))
    assert listed.json()["data"]["total"] == 1
    filtered = await client.get(
        f"/api/v1/models?provider_id={provider.id}&status=available", headers=AUTH(token)
    )
    assert filtered.json()["data"]["total"] == 2


async def test_model_update_and_default_switch(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    provider = await create_provider(db_session)
    first = await create_model(db_session, provider, "gpt-4o")
    second = await create_model(db_session, provider, "gpt-4o-mini")
    await client.put(
        f"/api/v1/models/{first.id}", json={"is_default": True}, headers=AUTH(token)
    )
    switched = await client.put(
        f"/api/v1/models/{second.id}", json={"is_default": True}, headers=AUTH(token)
    )
    assert switched.json()["data"]["is_default"] is True
    first_after = await client.get(f"/api/v1/models/{first.id}", headers=AUTH(token))
    assert first_after.json()["data"]["is_default"] is False


async def test_model_delete_and_not_found(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    provider = await create_provider(db_session)
    model = await create_model(db_session, provider)
    deleted = await client.delete(f"/api/v1/models/{model.id}", headers=AUTH(token))
    missing = await client.get(f"/api/v1/models/{model.id}", headers=AUTH(token))
    assert deleted.json()["code"] == 200
    assert missing.json()["code"] == 404


async def test_model_test_connection(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    provider = await create_provider(db_session)
    model = await create_model(db_session, provider)
    ok = await client.post(f"/api/v1/models/{model.id}/test", headers=AUTH(token))
    assert ok.json()["data"]["success"] is True

    provider.status = "disconnected"
    await db_session.commit()
    failed = await client.post(f"/api/v1/models/{model.id}/test", headers=AUTH(token))
    assert failed.json()["data"]["success"] is False


async def test_model_list_requires_permission(client, db_session):
    token = await _plain(client, db_session)
    response = await client.get("/api/v1/models", headers=AUTH(token))
    assert response.json()["code"] == 403
