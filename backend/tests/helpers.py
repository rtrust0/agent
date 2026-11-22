from app.core.security import hash_password
from app.modules.permission.model import Permission
from app.modules.role.model import Role
from app.modules.user.model import User

AUTH = lambda token: {"Authorization": f"Bearer {token}"}


async def create_permission(db, code: str, name: str | None = None) -> Permission:
    from sqlalchemy import select

    existing = await db.scalar(select(Permission).where(Permission.code == code))
    if existing:
        return existing
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


# ---------------- 业务模块夹具 ----------------
async def create_provider(db, name: str = "OpenAI", api_key: str = "sk-demo"):
    from app.modules.model.model import ModelProvider

    provider = ModelProvider(
        name=name,
        type=name.lower(),
        status="connected",
        endpoint="https://api.example.com/v1",
        api_key=api_key,
    )
    db.add(provider)
    await db.commit()
    await db.refresh(provider)
    return provider


async def create_model(db, provider, model_key: str = "gpt-4o"):
    from app.modules.model.model import LLMModel

    model = LLMModel(
        name=model_key.upper(),
        model_id=model_key,
        provider_id=provider.id,
        capabilities=["chat"],
        context_length=8192,
        input_price=0.01,
        output_price=0.03,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model


async def create_agent(
    db, name: str = "客服助手", *, created_by: str | None = None, status: str = "draft"
):
    from app.modules.agent.model import Agent

    agent = Agent(
        name=name,
        description="测试 Agent",
        type="conversation",
        status=status,
        config={"temperature": 0.7},
        version="v0.1",
        created_by=created_by,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


async def create_prompt(
    db,
    name: str = "客服提示词",
    *,
    created_by: str | None = None,
    content: str = "你好 {{name}}",
):
    from app.modules.prompt.model import Prompt

    prompt = Prompt(
        name=name,
        category="general",
        content=content,
        variables=["name"],
        version="v0.1",
        status="draft",
        created_by=created_by,
    )
    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)
    return prompt


async def create_knowledge_base(db, name: str = "产品知识库", *, created_by: str | None = None):
    from app.modules.knowledge.model import KnowledgeBase

    kb = KnowledgeBase(name=name, description="测试知识库", created_by=created_by)
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return kb


async def create_tool(
    db, name: str = "天气查询", *, created_by: str | None = None, status: str = "disabled"
):
    from app.modules.tool.model import Tool

    tool = Tool(
        name=name,
        description="测试工具",
        type="http_api",
        status=status,
        config={"url": "https://api.example.com"},
        created_by=created_by,
    )
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    return tool


async def create_conversation(db, *, user_id: int | None = None, status: str = "completed"):
    from app.modules.conversation.model import Conversation

    conversation = Conversation(
        agent_id=None,
        agent_name="客服助手",
        model_id=None,
        user_id=user_id,
        status=status,
        turn_count=0,
        input_tokens=10,
        output_tokens=20,
        total_tokens=30,
        total_cost=0.001,
        latency_ms=800,
        satisfaction="positive",
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation
