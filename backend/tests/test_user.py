from tests.helpers import AUTH, create_permission, create_role, create_user, login_token


async def test_users_list_requires_login(client):
    response = await client.get("/api/v1/users")
    assert response.json()["code"] == 401


async def test_users_list_login_only(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    response = await client.get("/api/v1/users", headers=AUTH(token))
    body = response.json()
    assert body["code"] == 200
    assert len(body["data"]) == 1


async def test_user_search_requires_permission(client, db_session):
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    response = await client.get("/api/v1/users/search", headers=AUTH(token))
    assert response.json()["code"] == 403


async def test_user_search_with_permission(client, db_session):
    perm = await create_permission(db_session, "user:list")
    role = await create_role(db_session, "lister", [perm])
    user = await create_user(db_session, "lister", roles=[role], data_scope="all")
    await create_user(db_session, "other", created_by=user.id)
    token = await login_token(client, "lister")
    response = await client.get(
        "/api/v1/users/search?page=1&page_size=10", headers=AUTH(token)
    )
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["total"] == 2
    # 列表必须内联角色，否则前端「角色」列只能显示 —
    lister_row = next(item for item in body["data"]["items"] if item["username"] == "lister")
    assert [role["code"] for role in lister_row["roles"]] == ["lister"]


async def test_user_search_keyword(client, db_session):
    perm = await create_permission(db_session, "user:list")
    role = await create_role(db_session, "lister", [perm])
    await create_user(db_session, "lister", roles=[role], superuser=False, data_scope="all")
    await create_user(db_session, "alice")
    token = await login_token(client, "lister")
    response = await client.get("/api/v1/users/search?keyword=alice", headers=AUTH(token))
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["total"] == 1


async def test_user_detail(client, db_session):
    perm = await create_permission(db_session, "user:read")
    role = await create_role(db_session, "reader", [perm])
    await create_user(db_session, "reader", roles=[role])
    target = await create_user(db_session, "target")
    token = await login_token(client, "reader")
    response = await client.get(f"/api/v1/users/{target.id}", headers=AUTH(token))
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["username"] == "target"


async def test_user_create_validation(client, db_session):
    perm = await create_permission(db_session, "user:create")
    role = await create_role(db_session, "creator", [perm])
    await create_user(db_session, "creator", roles=[role])
    token = await login_token(client, "creator")
    response = await client.post(
        "/api/v1/users", json={"username": "", "email": "x@x.com", "password": "123456"},
        headers=AUTH(token),
    )
    assert response.json()["code"] == 400


async def test_user_create_success(client, db_session):
    perm = await create_permission(db_session, "user:create")
    role = await create_role(db_session, "creator", [perm])
    await create_user(db_session, "creator", roles=[role])
    token = await login_token(client, "creator")
    response = await client.post(
        "/api/v1/users",
        json={"username": "newbie", "email": "newbie@x.com", "password": "123456"},
        headers=AUTH(token),
    )
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["username"] == "newbie"


async def test_user_create_forbidden(client, db_session):
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    response = await client.post(
        "/api/v1/users",
        json={"username": "x", "email": "x@x.com", "password": "123456"},
        headers=AUTH(token),
    )
    assert response.json()["code"] == 403


async def test_user_delete(client, db_session):
    perm = await create_permission(db_session, "user:delete")
    role = await create_role(db_session, "deleter", [perm])
    await create_user(db_session, "deleter", roles=[role])
    target = await create_user(db_session, "victim")
    token = await login_token(client, "deleter")
    response = await client.delete(f"/api/v1/users/{target.id}", headers=AUTH(token))
    assert response.json()["code"] == 200


async def test_user_delete_not_found(client, db_session):
    perm = await create_permission(db_session, "user:delete")
    role = await create_role(db_session, "deleter", [perm])
    await create_user(db_session, "deleter", roles=[role])
    token = await login_token(client, "deleter")
    response = await client.delete("/api/v1/users/9999", headers=AUTH(token))
    assert response.json()["code"] == 404


async def test_assign_roles(client, db_session):
    perm = await create_permission(db_session, "user:assign_roles")
    role = await create_role(db_session, "assigner", [perm])
    await create_user(db_session, "assigner", roles=[role])
    target_role = await create_role(db_session, "target_role")
    target = await create_user(db_session, "target")
    token = await login_token(client, "assigner")
    response = await client.put(
        f"/api/v1/users/{target.id}/roles",
        json={"role_ids": [target_role.id]},
        headers=AUTH(token),
    )
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["roles"][0]["code"] == "target_role"


async def test_get_user_roles(client, db_session):
    perm = await create_permission(db_session, "user:read_roles")
    role = await create_role(db_session, "roles_reader", [perm])
    await create_user(db_session, "roles_reader", roles=[role])
    target_role = await create_role(db_session, "demo_role")
    target = await create_user(db_session, "target", roles=[target_role])
    token = await login_token(client, "roles_reader")
    response = await client.get(f"/api/v1/users/{target.id}/roles", headers=AUTH(token))
    body = response.json()
    assert body["code"] == 200
    assert body["data"][0]["code"] == "demo_role"


async def test_me(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    response = await client.get("/api/v1/users/me", headers=AUTH(token))
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["username"] == "admin"


async def test_me_permissions_dedup_sorted(client, db_session):
    p1 = await create_permission(db_session, "user:read")
    p2 = await create_permission(db_session, "role:list")
    r1 = await create_role(db_session, "r1", [p1, p2])
    r2 = await create_role(db_session, "r2", [p1])
    await create_user(db_session, "multi", roles=[r1, r2])
    token = await login_token(client, "multi")
    response = await client.get("/api/v1/users/me/permissions", headers=AUTH(token))
    body = response.json()
    assert body["code"] == 200
    assert body["data"] == ["role:list", "user:read"]


async def test_me_permissions_superuser_all(client, db_session):
    await create_permission(db_session, "user:list")
    await create_permission(db_session, "role:delete")
    await create_user(db_session, "admin", superuser=True)
    token = await login_token(client, "admin")
    response = await client.get("/api/v1/users/me/permissions", headers=AUTH(token))
    body = response.json()
    assert body["code"] == 200
    assert body["data"] == ["role:delete", "user:list"]


async def test_user_search_is_platform_level(client, db_session):
    """用户目录属平台级数据：own 范围也能看到他人创建的用户，仅受 user:list 控制。"""
    perm = await create_permission(db_session, "user:list")
    role = await create_role(db_session, "lister", [perm])
    owner = await create_user(db_session, "owner", roles=[role], data_scope="own")
    await create_user(db_session, "mine", created_by=owner.id)
    await create_user(db_session, "others", created_by=None)
    token = await login_token(client, "owner")
    response = await client.get("/api/v1/users/search", headers=AUTH(token))
    body = response.json()
    assert body["code"] == 200
    names = {item["username"] for item in body["data"]["items"]}
    assert {"owner", "mine", "others"} <= names
