from tests.helpers import AUTH, create_permission, create_role, create_user, login_token


async def _admin(db_session):
    return await create_user(db_session, "admin", superuser=True)


async def test_login_writes_audit_log(client, db_session):
    await _admin(db_session)
    token = await login_token(client, "admin")
    response = await client.get("/api/v1/system/audit-logs", headers=AUTH(token))
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["action"] == "login"
    assert body["data"]["items"][0]["module"] == "auth"


async def test_write_operation_writes_audit_log(client, db_session):
    await _admin(db_session)
    token = await login_token(client, "admin")
    created = await client.post(
        "/api/v1/roles", json={"code": "audited", "name": "被审计角色"}, headers=AUTH(token)
    )
    assert created.json()["code"] == 200
    body = (
        await client.get(
            "/api/v1/system/audit-logs?module=role&action=create", headers=AUTH(token)
        )
    ).json()
    assert body["data"]["total"] == 1
    item = body["data"]["items"][0]
    assert item["target_name"] == "被审计角色"
    assert item["detail"]["code"] == "audited"
    assert item["username"] == "admin"


async def test_read_operation_not_audited(client, db_session):
    await _admin(db_session)
    token = await login_token(client, "admin")
    before = (
        await client.get("/api/v1/system/audit-logs", headers=AUTH(token))
    ).json()["data"]["total"]
    await client.get("/api/v1/users", headers=AUTH(token))
    await client.get("/api/v1/roles/", headers=AUTH(token))
    after = (
        await client.get("/api/v1/system/audit-logs", headers=AUTH(token))
    ).json()["data"]["total"]
    assert after == before


async def test_audit_logs_require_permission(client, db_session):
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    response = await client.get("/api/v1/system/audit-logs", headers=AUTH(token))
    assert response.json()["code"] == 403


async def test_audit_logs_filter_by_username(client, db_session):
    admin = await _admin(db_session)
    await create_user(db_session, "second", superuser=True)
    token1 = await login_token(client, "admin")
    token2 = await login_token(client, "second")
    await client.post("/api/v1/roles", json={"code": "r_a", "name": "A"}, headers=AUTH(token1))
    await client.post("/api/v1/roles", json={"code": "r_b", "name": "B"}, headers=AUTH(token2))

    filtered = (
        await client.get("/api/v1/system/audit-logs?username=second", headers=AUTH(token1))
    ).json()
    assert filtered["data"]["total"] == 2  # login + role create
    assert all(item["username"] == "second" for item in filtered["data"]["items"])
    assert admin.id  # 保持引用，避免未使用告警


async def test_audit_logs_export_csv(client, db_session):
    await _admin(db_session)
    token = await login_token(client, "admin")
    await client.post("/api/v1/roles", json={"code": "csv_role", "name": "CSV"}, headers=AUTH(token))
    response = await client.get("/api/v1/system/audit-logs/export", headers=AUTH(token))
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment; filename=\"audit-logs.csv\"" == response.headers["content-disposition"]
    lines = response.text.strip().splitlines()
    assert lines[0].startswith("id,username,action,module")
    assert any("csv_role" in line or "CSV" in line for line in lines[1:])


async def test_audit_log_survives_user_deletion(client, db_session):
    admin = await _admin(db_session)
    token = await login_token(client, "admin")
    victim = await create_user(db_session, "victim")
    deleted = await client.delete(f"/api/v1/users/{victim.id}", headers=AUTH(token))
    assert deleted.json()["code"] == 200
    body = (
        await client.get("/api/v1/system/audit-logs?action=delete", headers=AUTH(token))
    ).json()
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["username"] == "admin"
    assert admin.id
