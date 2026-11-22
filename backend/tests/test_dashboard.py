from app.modules.conversation.model import Conversation
from app.modules.system.model import Alert
from tests.helpers import (
    AUTH,
    create_agent,
    create_conversation,
    create_knowledge_base,
    create_model,
    create_permission,
    create_provider,
    create_tool,
    create_user,
    login_token,
)


async def _admin(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    return await login_token(client, "admin")


async def test_dashboard_requires_permission(client, db_session):
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    response = await client.get("/api/v1/dashboard/stats", headers=AUTH(token))
    assert response.json()["code"] == 403


async def test_dashboard_stats(client, db_session):
    token = await _admin(client, db_session)
    await create_permission(db_session, "dashboard:read")
    provider = await create_provider(db_session)
    await create_model(db_session, provider)
    agent = await create_agent(db_session, "统计 Agent", status="active")
    await create_knowledge_base(db_session, "统计库")
    await create_tool(db_session, "统计工具")
    await create_conversation(db_session)

    body = (await client.get("/api/v1/dashboard/stats", headers=AUTH(token))).json()["data"]
    assert body["total_users"] == 1
    assert body["total_permissions"] >= 1
    assert body["total_models"] == 1
    assert body["total_agents"] == 1
    assert body["active_agents"] == 1
    assert body["total_knowledge_bases"] == 1
    assert body["total_tools"] == 1
    assert body["total_conversations"] == 1
    assert body["today_conversations"] == 1
    assert agent.id


async def test_dashboard_trends_fill_missing_days(client, db_session):
    token = await _admin(client, db_session)
    await create_conversation(db_session)
    body = (await client.get("/api/v1/dashboard/trends?days=7", headers=AUTH(token))).json()["data"]
    assert len(body) == 7
    assert sum(point["conversations"] for point in body) == 1
    assert body[-1]["conversations"] == 1


async def test_dashboard_top_agents(client, db_session):
    token = await _admin(client, db_session)
    busy = await create_agent(db_session, "高频 Agent", status="active")
    idle = await create_agent(db_session, "低频 Agent", status="active")
    for _ in range(3):
        db_session.add(Conversation(agent_id=busy.id, agent_name=busy.name, status="completed"))
    db_session.add(Conversation(agent_id=idle.id, agent_name=idle.name, status="completed"))
    await db_session.commit()

    body = (await client.get("/api/v1/dashboard/top-agents", headers=AUTH(token))).json()["data"]
    assert body[0]["name"] == "高频 Agent"
    assert body[0]["conversation_count"] == 3


async def test_dashboard_recent_alerts(client, db_session):
    token = await _admin(client, db_session)
    db_session.add(
        Alert(
            type="performance",
            title="响应超时",
            message="平均响应时间超过 5s",
            source="agent",
            severity="high",
            status="active",
        )
    )
    await db_session.commit()
    body = (await client.get("/api/v1/dashboard/recent-alerts", headers=AUTH(token))).json()["data"]
    assert body[0]["title"] == "响应超时"
    assert body[0]["severity"] == "high"


async def test_dashboard_resource_usage(client, db_session):
    token = await _admin(client, db_session)
    kb = await create_knowledge_base(db_session, "资源库")
    await create_tool(db_session, "资源工具")
    await client.post(
        f"/api/v1/knowledge-bases/{kb.id}/documents",
        json={"file_name": "r.txt", "file_type": "txt", "content": "资源用量测试内容"},
        headers=AUTH(token),
    )
    body = (await client.get("/api/v1/dashboard/resource-usage", headers=AUTH(token))).json()["data"]
    assert body["document_count"] == 1
    assert body["segment_count"] == 1
    assert body["storage_mb"] >= 0
