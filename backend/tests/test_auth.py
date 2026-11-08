from app.core.security import hash_password
from app.modules.user.model import User


async def _seed_user(db_session, username="admin", password="123456", active=True, superuser=True):
    user = User(
        username=username,
        email=f"{username}@chenguang.ai",
        hashed_password=hash_password(password),
        is_active=active,
        is_superuser=superuser,
    )
    db_session.add(user)
    await db_session.commit()
    return user


async def test_login_success(client, db_session):
    await _seed_user(db_session)
    response = await client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "123456"}
    )
    body = response.json()
    assert response.status_code == 200
    assert body["code"] == 200
    assert body["data"]["token"]
    assert body["data"]["user"]["username"] == "admin"


async def test_login_wrong_password(client, db_session):
    await _seed_user(db_session)
    response = await client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "bad"}
    )
    assert response.json()["code"] == 401


async def test_login_unknown_user(client, db_session):
    response = await client.post(
        "/api/v1/auth/login", json={"username": "nobody", "password": "123456"}
    )
    assert response.json()["code"] == 401


async def test_login_disabled_user(client, db_session):
    await _seed_user(db_session, username="disabled", active=False)
    response = await client.post(
        "/api/v1/auth/login", json={"username": "disabled", "password": "123456"}
    )
    assert response.json()["code"] == 401
