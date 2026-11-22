from tests.helpers import AUTH, create_permission, create_role, create_user, login_token


async def test_permissions_list_login_only(client, db_session):
    await create_permission(db_session, "agent:list")
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    response = await client.get("/api/v1/permissions/", headers=AUTH(token))
    body = response.json()
    assert body["code"] == 200
    assert body["data"][0]["code"] == "agent:list"
    assert body["data"][0]["module"] == "agent"


async def test_permissions_list_requires_login(client):
    response = await client.get("/api/v1/permissions/")
    assert response.json()["code"] == 401


async def test_permission_search_forbidden(client, db_session):
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    response = await client.get("/api/v1/permissions/search", headers=AUTH(token))
    assert response.json()["code"] == 403


async def test_permission_create_and_search(client, db_session):
    perm = await create_permission(db_session, "permission:create")
    role = await create_role(db_session, "creator", [perm])
    lister_perm = await create_permission(db_session, "permission:list")
    role.permissions.append(lister_perm)
    await db_session.commit()
    await create_user(db_session, "creator", roles=[role])
    token = await login_token(client, "creator")
    created = await client.post(
        "/api/v1/permissions",
        json={"code": "report:read", "name": "报表查看", "description": "只读"},
        headers=AUTH(token),
    )
    searched = await client.get(
        "/api/v1/permissions/search?keyword=report", headers=AUTH(token)
    )
    assert created.json()["data"]["code"] == "report:read"
    assert searched.json()["data"]["total"] == 1


async def test_permission_create_invalid_code(client, db_session):
    perm = await create_permission(db_session, "permission:create")
    role = await create_role(db_session, "creator", [perm])
    await create_user(db_session, "creator", roles=[role])
    token = await login_token(client, "creator")
    response = await client.post(
        "/api/v1/permissions",
        json={"code": "Invalid Code", "name": "非法"},
        headers=AUTH(token),
    )
    assert response.json()["code"] == 400


async def test_permission_create_duplicate(client, db_session):
    perm = await create_permission(db_session, "permission:create")
    role = await create_role(db_session, "creator", [perm])
    await create_user(db_session, "creator", roles=[role])
    await create_permission(db_session, "dup:code")
    token = await login_token(client, "creator")
    response = await client.post(
        "/api/v1/permissions", json={"code": "dup:code", "name": "重复"}, headers=AUTH(token)
    )
    assert response.json()["code"] == 400


async def test_permission_detail_not_found(client, db_session):
    perm = await create_permission(db_session, "permission:read")
    role = await create_role(db_session, "reader", [perm])
    await create_user(db_session, "reader", roles=[role])
    token = await login_token(client, "reader")
    response = await client.get("/api/v1/permissions/9999", headers=AUTH(token))
    assert response.json()["code"] == 404


async def test_permission_update_keeps_code(client, db_session):
    perm = await create_permission(db_session, "permission:update")
    role = await create_role(db_session, "updater", [perm])
    await create_user(db_session, "updater", roles=[role])
    target = await create_permission(db_session, "agent:test")
    token = await login_token(client, "updater")
    response = await client.put(
        f"/api/v1/permissions/{target.id}",
        json={"name": "Agent 测试", "description": "更新后"},
        headers=AUTH(token),
    )
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["code"] == "agent:test"
    assert body["data"]["name"] == "Agent 测试"


async def test_permission_delete(client, db_session):
    perm = await create_permission(db_session, "permission:delete")
    read_perm = await create_permission(db_session, "permission:read")
    role = await create_role(db_session, "deleter", [perm, read_perm])
    await create_user(db_session, "deleter", roles=[role])
    target = await create_permission(db_session, "temp:code")
    token = await login_token(client, "deleter")
    response = await client.delete(f"/api/v1/permissions/{target.id}", headers=AUTH(token))
    assert response.json()["code"] == 200
    assert (await client.get(f"/api/v1/permissions/{target.id}", headers=AUTH(token))).json()[
        "code"
    ] == 404
