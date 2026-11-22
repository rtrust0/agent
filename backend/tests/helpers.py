from app.core.security import hash_password
from app.modules.permission.model import Permission
from app.modules.role.model import Role
from app.modules.user.model import User

AUTH = lambda token: {"Authorization": f"Bearer {token}"}


async def create_permission(db, code: str, name: str | None = None) -> Permission:
    perm = Permission(code=code, name=name or code)
    db.add(perm)
    await db.commit()
    await db.refresh(perm)
    return perm


async def create_role(db, code: str, perms: list[Permission] | None = None) -> Role:
    role = Role(code=code, name=code)
    if perms:
        role.permissions = perms
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def create_user(
    db,
    username: str,
    password: str = "123456",
    *,
    superuser: bool = False,
    active: bool = True,
    data_scope: str = "own",
    roles: list[Role] | None = None,
    created_by: int | None = None,
) -> User:
    user = User(
        username=username,
        email=f"{username}@chenguang.ai",
        hashed_password=hash_password(password),
        is_active=active,
        is_superuser=superuser,
        data_scope=data_scope,
        created_by=created_by,
    )
    if roles:
        user.roles = roles
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login_token(client, username: str, password: str = "123456") -> str:
    response = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    return response.json()["data"]["token"]
