from app.modules.system.model import Alert
from tests.helpers import AUTH, create_user, login_token


async def _admin(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    return await login_token(client, "admin")


def _alert(**kwargs) -> Alert:
    defaults = dict(
        type="performance",
        title="响应超时",
        message="平均响应时间超过 5s",
        source="agent",
        severity="high",
        status="active",
    )
    defaults.update(kwargs)
    return Alert(**defaults)


async def test_system_endpoints_require_permission(client, db_session):
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    for path in (
        "/api/v1/system/api-keys",
        "/api/v1/system/alerts/rules",
        "/api/v1/system/settings",
    ):
        response = await client.get(path, headers=AUTH(token))
        assert response.json()["code"] == 403


async def test_api_key_crud(client, db_session):
    token = await _admin(client, db_session)
    created = await client.post(
        "/api/v1/system/api-keys",
        json={"name": "默认密钥", "permissions": "readonly", "rate_limit": 120},
        headers=AUTH(token),
    )
    body = created.json()["data"]
    assert body["key"].startswith("sk-")
    assert body["status"] == "active"
    assert body["created_by"] == "admin"
    key_id = body["id"]

    listed = await client.get("/api/v1/system/api-keys", headers=AUTH(token))
    assert listed.json()["data"][0]["name"] == "默认密钥"

    updated = await client.put(
        f"/api/v1/system/api-keys/{key_id}",
        json={"status": "disabled", "rate_limit": 30},
        headers=AUTH(token),
    )
    assert updated.json()["data"]["status"] == "disabled"
    assert updated.json()["data"]["rate_limit"] == 30

    deleted = await client.delete(f"/api/v1/system/api-keys/{key_id}", headers=AUTH(token))
    assert deleted.json()["code"] == 200
    missing = await client.put(
        f"/api/v1/system/api-keys/{key_id}", json={"name": "x"}, headers=AUTH(token)
    )
    assert missing.json()["code"] == 404


async def test_alert_rule_crud(client, db_session):
    token = await _admin(client, db_session)
    created = await client.post(
        "/api/v1/system/alerts/rules",
        json={
            "name": "高错误率告警",
            "description": "错误率超过阈值",
            "condition": {"metric": "error_rate", "operator": ">", "threshold": 5},
            "notification": {"channels": ["email"], "recipients": ["ops@example.com"]},
        },
        headers=AUTH(token),
    )
    body = created.json()["data"]
    assert body["status"] == "enabled"
    assert body["condition"]["threshold"] == 5
    rule_id = body["id"]

    listed = await client.get("/api/v1/system/alerts/rules", headers=AUTH(token))
    assert listed.json()["data"][0]["name"] == "高错误率告警"

    updated = await client.put(
        f"/api/v1/system/alerts/rules/{rule_id}",
        json={"status": "disabled", "name": "已停用规则"},
        headers=AUTH(token),
    )
    assert updated.json()["data"]["status"] == "disabled"

    deleted = await client.delete(
        f"/api/v1/system/alerts/rules/{rule_id}", headers=AUTH(token)
    )
    assert deleted.json()["code"] == 200
    assert (await client.get("/api/v1/system/alerts/rules", headers=AUTH(token))).json()[
        "data"
    ] == []


async def test_alerts_acknowledge_and_resolve(client, db_session):
    token = await _admin(client, db_session)
    alert = _alert()
    db_session.add(alert)
    await db_session.commit()
    await db_session.refresh(alert)

    active = await client.get("/api/v1/system/alerts/active", headers=AUTH(token))
    assert active.json()["data"][0]["status"] == "active"

    acknowledged = await client.post(
        f"/api/v1/system/alerts/{alert.id}/acknowledge", headers=AUTH(token)
    )
    assert acknowledged.json()["data"]["status"] == "acknowledged"
    assert acknowledged.json()["data"]["acknowledged_by"] == "admin"

    resolved = await client.post(
        f"/api/v1/system/alerts/{alert.id}/resolve", headers=AUTH(token)
    )
    assert resolved.json()["data"]["status"] == "resolved"

    again = await client.post(
        f"/api/v1/system/alerts/{alert.id}/resolve", headers=AUTH(token)
    )
    assert again.json()["code"] == 400

    empty = await client.get("/api/v1/system/alerts/active", headers=AUTH(token))
    assert empty.json()["data"] == []


async def test_alert_not_found(client, db_session):
    token = await _admin(client, db_session)
    response = await client.post("/api/v1/system/alerts/9999/acknowledge", headers=AUTH(token))
    assert response.json()["code"] == 404


async def test_settings_get_creates_default_and_update(client, db_session):
    token = await _admin(client, db_session)
    first = await client.get("/api/v1/system/settings", headers=AUTH(token))
    body = first.json()["data"]
    assert body["system_name"] == "辰光Agent平台"
    assert body["smtp_port"] == 587

    updated = await client.put(
        "/api/v1/system/settings",
        json={"system_name": "辰光 Agent 平台", "default_temperature": 0.3},
        headers=AUTH(token),
    )
    data = updated.json()["data"]
    assert data["system_name"] == "辰光 Agent 平台"
    assert data["default_temperature"] == 0.3

    second = await client.get("/api/v1/system/settings", headers=AUTH(token))
    assert second.json()["data"]["id"] == body["id"]


async def test_system_write_operations_are_audited(client, db_session):
    token = await _admin(client, db_session)
    await client.post(
        "/api/v1/system/api-keys", json={"name": "审计密钥"}, headers=AUTH(token)
    )
    logs = (
        await client.get("/api/v1/system/audit-logs?module=system", headers=AUTH(token))
    ).json()["data"]
    assert logs["total"] == 1
    assert logs["items"][0]["action"] == "create"
    assert logs["items"][0]["target_name"] == "审计密钥"
