from datetime import datetime

from app.modules.conversation.model import ConversationTurn
from tests.helpers import AUTH, create_conversation, create_permission, create_role, create_user, login_token


async def _admin(client, db_session):
    await create_user(db_session, "admin", superuser=True)
    return await login_token(client, "admin")


async def _conv_user(db_session, username: str, codes: list[str], *, data_scope: str = "own"):
    permissions = [await create_permission(db_session, code) for code in codes]
    role = await create_role(db_session, f"{username}_role", permissions)
    return await create_user(db_session, username, roles=[role], data_scope=data_scope)


async def _seed_turns(db_session, conversation_id: int):
    db_session.add_all(
        [
            ConversationTurn(
                conversation_id=conversation_id,
                position=1,
                role="user",
                content="你好",
                timestamp=datetime.now(),
                trace={"step": "input"},
            ),
            ConversationTurn(
                conversation_id=conversation_id,
                position=2,
                role="assistant",
                content="你好，我是客服助手",
                timestamp=datetime.now(),
                trace={"step": "llm", "model": "gpt-4o"},
            ),
        ]
    )
    await db_session.commit()


async def test_conversations_require_permission(client, db_session):
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    response = await client.get("/api/v1/conversations", headers=AUTH(token))
    assert response.json()["code"] == 403


async def test_conversation_list_and_filters(client, db_session):
    token = await _admin(client, db_session)
    await create_conversation(db_session, status="completed")
    await create_conversation(db_session, status="error")

    all_rows = await client.get("/api/v1/conversations", headers=AUTH(token))
    errors = await client.get("/api/v1/conversations?status=error", headers=AUTH(token))
    assert all_rows.json()["data"]["total"] == 2
    assert errors.json()["data"]["total"] == 1
    assert errors.json()["data"]["items"][0]["status"] == "error"


async def test_conversation_data_scope(client, db_session):
    owner = await _conv_user(db_session, "owner", ["conversation:list"])
    await create_conversation(db_session, user_id=owner.id)
    other = await create_user(db_session, "other")
    await create_conversation(db_session, user_id=other.id)
    token = await login_token(client, "owner")
    body = (await client.get("/api/v1/conversations", headers=AUTH(token))).json()
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["user_id"] == owner.id


async def test_conversation_detail_forbidden_out_of_scope(client, db_session):
    await _conv_user(db_session, "reader", ["conversation:read"])
    other = await create_user(db_session, "stranger")
    foreign = await create_conversation(db_session, user_id=other.id)
    token = await login_token(client, "reader")
    response = await client.get(f"/api/v1/conversations/{foreign.id}", headers=AUTH(token))
    assert response.json()["code"] == 403


async def test_conversation_turns_and_trace(client, db_session):
    token = await _admin(client, db_session)
    conversation = await create_conversation(db_session)
    await _seed_turns(db_session, conversation.id)

    turns = await client.get(f"/api/v1/conversations/{conversation.id}/turns", headers=AUTH(token))
    items = turns.json()["data"]
    assert [t["role"] for t in items] == ["user", "assistant"]

    trace = await client.get(f"/api/v1/turns/{items[1]['id']}/trace", headers=AUTH(token))
    assert trace.json()["data"]["trace"]["model"] == "gpt-4o"
    assert trace.json()["data"]["content"].startswith("你好")

    missing = await client.get("/api/v1/turns/9999/trace", headers=AUTH(token))
    assert missing.json()["code"] == 404


async def test_conversation_annotate(client, db_session):
    token = await _admin(client, db_session)
    conversation = await create_conversation(db_session)
    response = await client.post(
        f"/api/v1/conversations/{conversation.id}/annotate",
        json={
            "rating": 5,
            "tags": ["高质量"],
            "needs_optimization": False,
            "annotation": {"note": "回答准确"},
            "satisfaction": "positive",
        },
        headers=AUTH(token),
    )
    body = response.json()["data"]
    assert body["rating"] == 5
    assert body["tags"] == ["高质量"]
    assert body["annotation"]["note"] == "回答准确"


async def test_conversation_annotate_invalid_rating(client, db_session):
    token = await _admin(client, db_session)
    conversation = await create_conversation(db_session)
    response = await client.post(
        f"/api/v1/conversations/{conversation.id}/annotate",
        json={"rating": 9},
        headers=AUTH(token),
    )
    assert response.status_code == 422


async def test_conversation_export_csv(client, db_session):
    token = await _admin(client, db_session)
    conversation = await create_conversation(db_session)
    await _seed_turns(db_session, conversation.id)
    response = await client.get(
        f"/api/v1/conversations/{conversation.id}/export", headers=AUTH(token)
    )
    assert "text/csv" in response.headers["content-type"]
    lines = response.text.strip().splitlines()
    assert lines[0].startswith("conversation_id,position,role")
    assert len(lines) == 3


async def test_conversation_not_found(client, db_session):
    token = await _admin(client, db_session)
    response = await client.get("/api/v1/conversations/9999", headers=AUTH(token))
    assert response.json()["code"] == 404
