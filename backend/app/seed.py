"""初始化数据脚本（对齐 docs/design/db/init-data.sql）。

用法：在 backend 目录执行 `python -m app.seed`（或 `.venv/Scripts/python.exe -m app.seed`）。
可重复执行：已存在的数据不会重复写入。
"""

import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.base_model import Base
from app.core.database import SessionLocal, engine
from app.core.permission_catalog import PERMISSION_CATALOG, ROLE_GRANTS
from app.core.security import hash_password
from app.modules.agent.model import Agent, AgentVersion
from app.modules.approval.model import PermissionApplication
from app.modules.audit.model import AuditLog
from app.modules.conversation.model import Conversation, ConversationTurn
from app.modules.knowledge.model import Document, KnowledgeBase, Segment
from app.modules.model.model import LLMModel, ModelProvider
from app.modules.permission.model import Permission
from app.modules.prompt.model import Prompt, PromptVersion
from app.modules.role.model import Role
from app.modules.system.model import Alert, AlertRule, ApiKey, SystemSetting
from app.modules.tool.model import Tool
from app.modules.user.model import User

DEFAULT_PASSWORD = "123456"


async def _ensure_permissions(db) -> dict[str, Permission]:
    mapping: dict[str, Permission] = {}
    for code, name, description in PERMISSION_CATALOG:
        permission = await db.scalar(select(Permission).where(Permission.code == code))
        if not permission:
            permission = Permission(code=code, name=name, description=description)
            db.add(permission)
            await db.flush()
        mapping[code] = permission
    await db.commit()
    return mapping


async def _ensure_roles(db, permissions: dict[str, Permission]) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    meta = {
        "super_admin": "超级管理员",
        "ops_admin": "运维管理员",
        "viewer": "只读用户",
    }
    for code, name in meta.items():
        role = await db.scalar(select(Role).where(Role.code == code))
        if not role:
            role = Role(code=code, name=name, description=name)
            db.add(role)
            await db.flush()
            await db.refresh(role)
        role.permissions = [permissions[item] for item in ROLE_GRANTS[code]]
        roles[code] = role
    await db.commit()
    return roles


async def _ensure_users(db, roles: dict[str, Role]) -> dict[str, User]:
    seed_users = [
        ("admin", "admin@chenguang.ai", "super_admin", True, "all"),
        ("ops", "ops@chenguang.ai", "ops_admin", False, "dept"),
        ("viewer", "viewer@chenguang.ai", "viewer", False, "own"),
    ]
    users: dict[str, User] = {}
    for username, email, role_code, is_superuser, data_scope in seed_users:
        user = await db.scalar(select(User).where(User.username == username))
        if not user:
            user = User(
                username=username,
                email=email,
                hashed_password=hash_password(DEFAULT_PASSWORD),
                is_active=True,
                is_superuser=is_superuser,
                data_scope=data_scope,
            )
            db.add(user)
            await db.flush()
            await db.refresh(user)
        user.roles = [roles[role_code]]
        users[username] = user
    await db.commit()
    return users


async def _ensure_business_data(db, users: dict[str, User]) -> None:
    if not await db.scalar(select(ModelProvider).limit(1)):
        openai = ModelProvider(
            name="OpenAI",
            type="openai",
            status="connected",
            endpoint="https://api.openai.com/v1",
            api_key="sk-demo-openai",
            description="OpenAI 官方接口",
        )
        anthropic = ModelProvider(
            name="Anthropic",
            type="anthropic",
            status="connected",
            endpoint="https://api.anthropic.com/v1",
            api_key="sk-demo-anthropic",
            description="Anthropic 官方接口",
        )
        db.add_all([openai, anthropic])
        await db.flush()
        gpt = LLMModel(
            name="GPT-4o",
            model_id="gpt-4o",
            provider_id=openai.id,
            capabilities=["chat", "vision"],
            context_length=128000,
            input_price=0.005,
            output_price=0.015,
            is_default=True,
        )
        claude = LLMModel(
            name="Claude Sonnet 4",
            model_id="claude-sonnet-4",
            provider_id=anthropic.id,
            capabilities=["chat", "reasoning"],
            context_length=200000,
            input_price=0.003,
            output_price=0.015,
        )
        db.add_all([gpt, claude])
        await db.flush()

        agents = []
        for name, type_, model, status in (
            ("客服助手", "conversation", gpt, "active"),
            ("数据分析助手", "analysis", claude, "draft"),
        ):
            agent = Agent(
                name=name,
                description=f"{name}（演示数据）",
                type=type_,
                status=status,
                model_id=model.id,
                config={"temperature": 0.7},
                success_rate=98.5 if status == "active" else 0,
                call_count_7d=1280 if status == "active" else 0,
                version="v1.0",
                created_by="admin",
            )
            db.add(agent)
            await db.flush()
            db.add(
                AgentVersion(
                    agent_id=agent.id,
                    version="v1.0",
                    config=agent.config,
                    changelog="初始发布",
                    is_current=True,
                    published_by="admin",
                    published_at=datetime.now(),
                )
            )
            agents.append(agent)

        for name, category, content, tags in (
            ("客服提示词", "customer_service", "你是 {{company}} 的客服，请礼貌回答：{{question}}", ["客服"]),
            ("数据分析提示词", "analysis", "请分析以下数据并给出结论：{{data}}", ["分析"]),
        ):
            prompt = Prompt(
                name=name,
                description=f"{name}（演示数据）",
                category=category,
                tags=tags,
                content=content,
                variables=["company", "question"] if category == "customer_service" else ["data"],
                version="v1.0",
                status="published",
                created_by="admin",
            )
            db.add(prompt)
            await db.flush()
            db.add(
                PromptVersion(
                    prompt_id=prompt.id,
                    version="v1.0",
                    content=content,
                    changelog="初始发布",
                    is_current=True,
                    published_by="admin",
                    published_at=datetime.now(),
                )
            )

        kb = KnowledgeBase(
            name="产品知识库",
            description="产品手册与常见问题",
            status="ready",
            embedding_model="text-embedding-ada-002",
            created_by="admin",
        )
        db.add(kb)
        await db.flush()
        document = Document(
            knowledge_base_id=kb.id,
            file_name="产品手册.pdf",
            file_type="pdf",
            file_size="2.4MB",
            status="completed",
            segment_count=2,
            word_count=120,
            uploaded_by="admin",
            processed_at=datetime.now(),
        )
        db.add(document)
        await db.flush()
        db.add_all(
            [
                Segment(
                    knowledge_base_id=kb.id,
                    document_id=document.id,
                    position=1,
                    content="辰光 Agent 平台支持 Agent 编排、知识库检索与工具调用。",
                    word_count=30,
                    token_count=30,
                ),
                Segment(
                    knowledge_base_id=kb.id,
                    document_id=document.id,
                    position=2,
                    content="平台默认使用 GPT-4o 模型，可在模型管理中切换。",
                    word_count=24,
                    token_count=24,
                ),
            ]
        )
        kb.document_count = 1
        kb.segment_count = 2

        db.add_all(
            [
                Tool(
                    name="天气查询",
                    description="查询指定城市天气",
                    type="http_api",
                    status="enabled",
                    config={"url": "https://api.weather.example.com"},
                    call_count_7d=320,
                    success_rate=99.2,
                    avg_latency=180,
                    created_by="admin",
                ),
                Tool(
                    name="HTTP 请求",
                    description="通用 HTTP 请求工具",
                    type="builtin",
                    status="disabled",
                    config={"methods": ["GET", "POST"]},
                    call_count_7d=48,
                    success_rate=95.0,
                    avg_latency=240,
                    created_by="admin",
                ),
            ]
        )

        conversations = [
            Conversation(
                agent_id=agents[0].id,
                agent_name=agents[0].name,
                model_id=gpt.id,
                user_id=users["admin"].id,
                status="completed",
                turn_count=2,
                input_tokens=120,
                output_tokens=180,
                total_tokens=300,
                total_cost=0.0032,
                latency_ms=1200,
                satisfaction="positive",
                rating=5,
                tags=["售前咨询"],
                started_at=datetime.now() - timedelta(hours=3),
                ended_at=datetime.now() - timedelta(hours=2),
            ),
            Conversation(
                agent_id=agents[0].id,
                agent_name=agents[0].name,
                model_id=gpt.id,
                user_id=users["ops"].id,
                status="completed",
                turn_count=1,
                input_tokens=60,
                output_tokens=90,
                total_tokens=150,
                total_cost=0.0016,
                latency_ms=900,
                satisfaction="positive",
                started_at=datetime.now() - timedelta(days=1),
            ),
            Conversation(
                agent_id=agents[1].id,
                agent_name=agents[1].name,
                model_id=claude.id,
                user_id=users["viewer"].id,
                status="error",
                turn_count=1,
                input_tokens=80,
                output_tokens=0,
                total_tokens=80,
                total_cost=0.0002,
                latency_ms=5000,
                satisfaction="negative",
                needs_optimization=True,
                started_at=datetime.now() - timedelta(days=2),
            ),
        ]
        db.add_all(conversations)
        await db.flush()
        db.add_all(
            [
                ConversationTurn(
                    conversation_id=conversations[0].id,
                    position=1,
                    role="user",
                    content="你们支持私有化部署吗？",
                    trace={"step": "input"},
                ),
                ConversationTurn(
                    conversation_id=conversations[0].id,
                    position=2,
                    role="assistant",
                    content="支持，提供 Docker 与 K8s 两种部署方式。",
                    trace={"step": "llm", "model": "gpt-4o", "latency_ms": 1200},
                ),
                ConversationTurn(
                    conversation_id=conversations[2].id,
                    position=1,
                    role="user",
                    content="分析一下上月用量",
                    trace={"step": "input"},
                ),
            ]
        )

        db.add(
            ApiKey(
                name="默认密钥",
                key="sk-demo-0123456789abcdef",
                permissions="all",
                status="active",
                rate_limit=60,
                created_by="admin",
            )
        )
        db.add(
            AlertRule(
                name="高错误率告警",
                description="错误率超过 5% 触发",
                condition={"metric": "error_rate", "operator": ">", "threshold": 5},
                notification={"channels": ["email"], "recipients": ["ops@chenguang.ai"]},
                created_by="admin",
            )
        )
        db.add(
            Alert(
                type="performance",
                title="Agent 响应超时",
                message="数据分析助手平均响应时间超过 5s",
                source="agent",
                severity="high",
                status="active",
            )
        )
        db.add(SystemSetting())

    if not await db.scalar(select(AuditLog).limit(1)):
        db.add_all(
            [
                AuditLog(
                    user_id=users["admin"].id,
                    username="admin",
                    action="create",
                    module="user",
                    target_id="2",
                    target_name="ops",
                    detail='{"data_scope": "dept"}',
                    ip_address="127.0.0.1",
                ),
                AuditLog(
                    user_id=users["admin"].id,
                    username="admin",
                    action="assign",
                    module="role",
                    target_id="2",
                    target_name="运维管理员",
                    detail='{"permission_count": 45}',
                    ip_address="127.0.0.1",
                ),
            ]
        )

    if not await db.scalar(select(PermissionApplication).limit(1)):
        db.add_all(
            [
                PermissionApplication(
                    applicant_id=users["viewer"].id,
                    applicant_name="viewer",
                    permission_code="agent:create",
                    reason="需要创建测试 Agent",
                    status="pending",
                ),
                PermissionApplication(
                    applicant_id=users["ops"].id,
                    applicant_name="ops",
                    permission_code="agent:create",
                    reason="运维需要创建 Agent",
                    status="approved",
                    approver_id=users["admin"].id,
                    approver_name="admin",
                    approved_at=datetime.now(),
                ),
            ]
        )
    await db.commit()


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        permissions = await _ensure_permissions(db)
        roles = await _ensure_roles(db, permissions)
        users = await _ensure_users(db, roles)
        await _ensure_business_data(db, users)
    print(
        f"seed 完成：权限 {len(PERMISSION_CATALOG)} 个、角色 {len(roles)} 个、"
        f"用户 {len(users)} 个（默认密码 {DEFAULT_PASSWORD}）"
    )


if __name__ == "__main__":
    asyncio.run(seed())
