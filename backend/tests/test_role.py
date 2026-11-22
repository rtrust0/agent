from tests.helpers import AUTH, create_permission, create_role, create_user, login_token


async def test_roles_list_login_only(client, db_session):
    await create_role(db_session, "viewer")
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    response = await client.get("/api/v1/roles/", headers=AUTH(token))
    body = response.json()
    assert body["code"] == 200
    assert body["data"][0]["code"] == "viewer"


async def test_roles_list_requires_login(client):
    response = await client.get("/api/v1/roles/")
    assert response.json()["code"] == 401


async def test_role_search_forbidden(client, db_session):
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    response = await client.get("/api/v1/roles/search", headers=AUTH(token))
    assert response.json()["code"] == 403


async def test_role_search_with_permission(client, db_session):
    perm = await create_permission(db_session, "role:list")
    role = await create_role(db_session, "lister", [perm])
    await create_user(db_session, "lister", roles=[role])
    await create_role(db_session, "ops_admin")
    token = await login_token(client, "lister")
    response = await client.get("/api/v1/roles/search?keyword=ops", headers=AUTH(token))
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["code"] == "ops_admin"


async def test_role_create_success(client, db_session):
    perm = await create_permission(db_session, "role:create")
    role = await create_role(db_session, "creator", [perm])
    await create_user(db_session, "creator", roles=[role])
    token = await login_token(client, "creator")
    response = await client.post(
        "/api/v1/roles",
        json={"code": "auditor", "name": "审计员", "description": "只读审计"},
        headers=AUTH(token),
    )
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["code"] == "auditor"
    assert body["data"]["permissions"] == []


async def test_role_create_duplicate_code(client, db_session):
    perm = await create_permission(db_session, "role:create")
    role = await create_role(db_session, "creator", [perm])
    await create_user(db_session, "creator", roles=[role])
    await create_role(db_session, "dup")
    token = await login_token(client, "creator")
    response = await client.post(
        "/api/v1/roles", json={"code": "dup", "name": "重复"}, headers=AUTH(token)
    )
    assert response.json()["code"] == 400


async def test_role_create_forbidden(client, db_session):
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    response = await client.post(
        "/api/v1/roles", json={"code": "x_role", "name": "x"}, headers=AUTH(token)
    )
    assert response.json()["code"] == 403


async def test_role_detail_and_not_found(client, db_session):
    perm = await create_permission(db_session, "role:read")
    role = await create_role(db_session, "reader", [perm])
    await create_user(db_session, "reader", roles=[role])
    target = await create_role(db_session, "target")
    token = await login_token(client, "reader")
    ok = await client.get(f"/api/v1/roles/{target.id}", headers=AUTH(token))
    missing = await client.get("/api/v1/roles/9999", headers=AUTH(token))
    assert ok.json()["data"]["code"] == "target"
    assert missing.json()["code"] == 404


async def test_role_update(client, db_session):
    perm = await create_permission(db_session, "role:update")
    role = await create_role(db_session, "updater", [perm])
    await create_user(db_session, "updater", roles=[role])
    target = await create_role(db_session, "target")
    token = await login_token(client, "updater")
    response = await client.put(
        f"/api/v1/roles/{target.id}",
        json={"name": "新名称", "description": "改过"},
        headers=AUTH(token),
    )
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["name"] == "新名称"


async def test_role_delete_and_builtin_guard(client, db_session):
    perm = await create_permission(db_session, "role:delete")
    role = await create_role(db_session, "deleter", [perm])
    await create_user(db_session, "deleter", roles=[role])
    target = await create_role(db_session, "temp")
    builtin = await create_role(db_session, "super_admin")
    token = await login_token(client, "deleter")
    ok = await client.delete(f"/api/v1/roles/{target.id}", headers=AUTH(token))
    blocked = await client.delete(f"/api/v1/roles/{builtin.id}", headers=AUTH(token))
    assert ok.json()["code"] == 200
    assert blocked.json()["code"] == 400


async def test_role_assign_permissions(client, db_session):
    assign_perm = await create_permission(db_session, "role:assign_permissions")
    role = await create_role(db_session, "assigner", [assign_perm])
    await create_user(db_session, "assigner", roles=[role])
    p1 = await create_permission(db_session, "agent:list")
    p2 = await create_permission(db_session, "agent:read")
    target = await create_role(db_session, "target")
    token = await login_token(client, "assigner")
    response = await client.put(
        f"/api/v1/roles/{target.id}/permissions",
        json={"permission_ids": [p1.id, p2.id]},
        headers=AUTH(token),
    )
    body = response.json()
    assert body["code"] == 200
    assert {p["code"] for p in body["data"]["permissions"]} == {"agent:list", "agent:read"}


async def test_role_assign_permissions_invalid_id(client, db_session):
    assign_perm = await create_permission(db_session, "role:assign_permissions")
    role = await create_role(db_session, "assigner", [assign_perm])
    await create_user(db_session, "assigner", roles=[role])
    target = await create_role(db_session, "target")
    token = await login_token(client, "assigner")
    response = await client.put(
        f"/api/v1/roles/{target.id}/permissions",
        json={"permission_ids": [9999]},
        headers=AUTH(token),
    )
    assert response.json()["code"] == 400
