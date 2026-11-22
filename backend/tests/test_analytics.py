from app.modules.conversation.model import Conversation
from tests.helpers import (
    AUTH,
    create_agent,
    create_model,
    create_permission,
    create_provider,
    create_role,
    create_user,
    login_token,
)


async def _admin(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    return await login_token(client, "admin")


def _conversation(**kwargs) -> Conversation:
    defaults = dict(
        agent_name="客服助手",
        status="completed",
        total_tokens=100,
        total_cost=0.002,
        latency_ms=1000,
        satisfaction="positive",
        rating=5,
    )
    defaults.update(kwargs)
    return Conversation(**defaults)


async def test_analytics_requires_permission(client, db_session):
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    response = await client.get("/api/v1/analytics/overview", headers=AUTH(token))
    assert response.json()["code"] == 403


async def test_analytics_overview(client, db_session):
    token = await _admin(client, db_session)
    db_session.add_all(
        [
            _conversation(),
            _conversation(status="error", satisfaction="negative", rating=2),
            _conversation(total_tokens=200, total_cost=0.004, latency_ms=3000),
        ]
    )
    await db_session.commit()
    body = (await client.get("/api/v1/analytics/overview", headers=AUTH(token))).json()["data"]
    assert body["total_conversations"] == 3
    assert body["completed_conversations"] == 2
    assert body["error_conversations"] == 1
    assert body["total_tokens"] == 400
    assert round(body["total_cost"], 6) == 0.008
    assert body["avg_latency_ms"] == 1666
    assert body["success_rate"] == 66.67


async def test_analytics_daily(client, db_session):
    token = await _admin(client, db_session)
    db_session.add(_conversation())
    await db_session.commit()
    body = (await client.get("/api/v1/analytics/daily?days=5", headers=AUTH(token))).json()["data"]
    assert len(body) == 5
    assert body[-1]["conversations"] == 1


async def test_analytics_by_agent_and_model(client, db_session):
    token = await _admin(client, db_session)
    provider = await create_provider(db_session)
    model = await create_model(db_session, provider, "gpt-4o")
    support_agent = await create_agent(db_session, "客服助手")
    analysis_agent = await create_agent(db_session, "分析助手")
    db_session.add_all(
        [
            _conversation(agent_id=support_agent.id, agent_name="客服助手", model_id=model.id),
            _conversation(agent_id=support_agent.id, agent_name="客服助手", model_id=model.id),
            _conversation(agent_id=analysis_agent.id, agent_name="分析助手", model_id=None),
        ]
    )
    await db_session.commit()

    agents = (await client.get("/api/v1/analytics/by-agent", headers=AUTH(token))).json()["data"]
    assert agents[0]["agent_name"] == "客服助手"
    assert agents[0]["conversations"] == 2

    models = (await client.get("/api/v1/analytics/by-model", headers=AUTH(token))).json()["data"]
    named = [row for row in models if row["model_name"] == "GPT-4O"]
    assert named[0]["conversations"] == 2
    assert any(row["model_name"] == "未指定模型" for row in models)


async def test_analytics_costs(client, db_session):
    token = await _admin(client, db_session)
    db_session.add_all([_conversation(total_cost=0.01), _conversation(total_cost=0.03)])
    await db_session.commit()
    body = (await client.get("/api/v1/analytics/costs", headers=AUTH(token))).json()["data"]
    assert round(body["total_cost"], 6) == 0.04
    assert round(body["avg_cost_per_conversation"], 6) == 0.02
    assert len(body["daily"]) == 14


async def test_analytics_evaluation(client, db_session):
    token = await _admin(client, db_session)
    db_session.add_all(
        [
            _conversation(satisfaction="positive", rating=5),
            _conversation(satisfaction="positive", rating=4),
            _conversation(satisfaction="negative", rating=2, needs_optimization=True),
        ]
    )
    await db_session.commit()
    body = (await client.get("/api/v1/analytics/evaluation", headers=AUTH(token))).json()["data"]
    assert body["positive"] == 2
    assert body["negative"] == 1
    assert body["satisfaction_rate"] == 66.67
    assert body["avg_rating"] == 3.67
    assert body["needs_optimization"] == 1


async def test_analytics_respects_data_scope(client, db_session):
    permission = await create_permission(db_session, "analytics:read")
    role = await create_role(db_session, "metrics_reader", [permission])
    scoped = await create_user(db_session, "scoped", roles=[role], data_scope="own")
    other = await create_user(db_session, "outsider")
    db_session.add_all(
        [
            _conversation(user_id=scoped.id),
            _conversation(user_id=other.id),
            _conversation(user_id=other.id),
        ]
    )
    await db_session.commit()
    token = await login_token(client, "scoped")
    overview = (await client.get("/api/v1/analytics/overview", headers=AUTH(token))).json()["data"]
    assert overview["total_conversations"] == 1
    by_agent = (await client.get("/api/v1/analytics/by-agent", headers=AUTH(token))).json()["data"]
    assert sum(row["conversations"] for row in by_agent) == 1
    daily = (await client.get("/api/v1/analytics/daily?days=3", headers=AUTH(token))).json()["data"]
    assert sum(point["conversations"] for point in daily) == 1
