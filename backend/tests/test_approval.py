from datetime import datetime, timedelta

from app.modules.approval.model import PermissionApplication
from tests.helpers import AUTH, create_permission, create_role, create_user, login_token


async def _applicant(db_session, name="applicant"):
    perm = await create_permission(db_session, "approval:apply")
    role = await create_role(db_session, f"{name}_role", [perm])
    return await create_user(db_session, name, roles=[role])


async def _auditor(db_session, name="auditor"):
    perm = await create_permission(db_session, "approval:audit")
    role = await create_role(db_session, f"{name}_role", [perm])
    return await create_user(db_session, name, roles=[role], data_scope="all")


async def test_apply_requires_login_and_permission(client, db_session):
    anonymous = await client.post(
        "/api/v1/approvals/apply", json={"permission_code": "agent:list", "reason": "x"}
    )
    await create_user(db_session, "plain")
    token = await login_token(client, "plain")
    forbidden = await client.post(
        "/api/v1/approvals/apply",
        json={"permission_code": "agent:list", "reason": "x"},
        headers=AUTH(token),
    )
    assert anonymous.json()["code"] == 401
    assert forbidden.json()["code"] == 403


async def test_apply_success_and_duplicate(client, db_session):
    await _applicant(db_session)
    await create_permission(db_session, "agent:list")
    token = await login_token(client, "applicant")
    payload = {"permission_code": "agent:list", "reason": "需要查看 Agent"}
    first = await client.post("/api/v1/approvals/apply", json=payload, headers=AUTH(token))
    second = await client.post("/api/v1/approvals/apply", json=payload, headers=AUTH(token))
    assert first.json()["code"] == 200
    assert first.json()["data"]["status"] == "pending"
    assert first.json()["data"]["applicant_name"] == "applicant"
    assert second.json()["code"] == 400


async def test_apply_unknown_permission_and_empty_reason(client, db_session):
    await _applicant(db_session)
    token = await login_token(client, "applicant")
    unknown = await client.post(
        "/api/v1/approvals/apply",
        json={"permission_code": "ghost:code", "reason": "x"},
        headers=AUTH(token),
    )
    empty = await client.post(
        "/api/v1/approvals/apply",
        json={"permission_code": "agent:list", "reason": "   "},
        headers=AUTH(token),
    )
    assert unknown.json()["code"] == 404
    assert empty.json()["code"] == 400


async def test_my_applications(client, db_session):
    await _applicant(db_session)
    await create_permission(db_session, "agent:list")
    token = await login_token(client, "applicant")
    await client.post(
        "/api/v1/approvals/apply",
        json={"permission_code": "agent:list", "reason": "需要"},
        headers=AUTH(token),
    )
    response = await client.get("/api/v1/approvals/my", headers=AUTH(token))
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["total"] == 1


async def test_approval_list_requires_audit_permission(client, db_session):
    await _applicant(db_session)
    token = await login_token(client, "applicant")
    response = await client.get("/api/v1/approvals/list", headers=AUTH(token))
    assert response.json()["code"] == 403


async def test_approve_grants_permission_immediately(client, db_session):
    await _applicant(db_session)
    await _auditor(db_session)
    await create_permission(db_session, "agent:list")

    applicant_token = await login_token(client, "applicant")
    auditor_token = await login_token(client, "auditor")

    before = (await client.get("/api/v1/users/me/permissions", headers=AUTH(applicant_token))).json()
    assert "agent:list" not in before["data"]

    created = await client.post(
        "/api/v1/approvals/apply",
        json={"permission_code": "agent:list", "reason": "需要"},
        headers=AUTH(applicant_token),
    )
    app_id = created.json()["data"]["id"]

    listed = await client.get("/api/v1/approvals/list?status=pending", headers=AUTH(auditor_token))
    assert listed.json()["data"]["total"] == 1

    audited = await client.put(
        f"/api/v1/approvals/{app_id}/audit",
        json={"approved": True, "comment": "同意"},
        headers=AUTH(auditor_token),
    )
    assert audited.json()["data"]["status"] == "approved"
    assert audited.json()["data"]["approver_name"] == "auditor"

    after = (await client.get("/api/v1/users/me/permissions", headers=AUTH(applicant_token))).json()
    assert "agent:list" in after["data"]


async def test_reject_does_not_grant(client, db_session):
    await _applicant(db_session)
    await _auditor(db_session)
    await create_permission(db_session, "agent:list")
    applicant_token = await login_token(client, "applicant")
    auditor_token = await login_token(client, "auditor")
    created = await client.post(
        "/api/v1/approvals/apply",
        json={"permission_code": "agent:list", "reason": "需要"},
        headers=AUTH(applicant_token),
    )
    app_id = created.json()["data"]["id"]
    rejected = await client.put(
        f"/api/v1/approvals/{app_id}/audit",
        json={"approved": False, "comment": "不通过"},
        headers=AUTH(auditor_token),
    )
    assert rejected.json()["data"]["status"] == "rejected"
    perms = (await client.get("/api/v1/users/me/permissions", headers=AUTH(applicant_token))).json()
    assert "agent:list" not in perms["data"]


async def test_audit_processed_application_twice(client, db_session):
    await _applicant(db_session)
    await _auditor(db_session)
    await create_permission(db_session, "agent:list")
    applicant_token = await login_token(client, "applicant")
    auditor_token = await login_token(client, "auditor")
    created = await client.post(
        "/api/v1/approvals/apply",
        json={"permission_code": "agent:list", "reason": "需要"},
        headers=AUTH(applicant_token),
    )
    app_id = created.json()["data"]["id"]
    await client.put(
        f"/api/v1/approvals/{app_id}/audit",
        json={"approved": True},
        headers=AUTH(auditor_token),
    )
    again = await client.put(
        f"/api/v1/approvals/{app_id}/audit",
        json={"approved": True},
        headers=AUTH(auditor_token),
    )
    missing = await client.put(
        "/api/v1/approvals/99999/audit", json={"approved": True}, headers=AUTH(auditor_token)
    )
    assert again.json()["code"] == 400
    assert missing.json()["code"] == 404


async def test_expired_grant_not_effective(client, db_session):
    applicant = await _applicant(db_session)
    await create_permission(db_session, "agent:list")
    db_session.add(
        PermissionApplication(
            applicant_id=applicant.id,
            applicant_name=applicant.username,
            permission_code="agent:list",
            reason="历史授权",
            status="approved",
            approver_name="auditor",
            approved_at=datetime.now() - timedelta(days=10),
            expired_at=datetime.now() - timedelta(days=1),
        )
    )
    await db_session.commit()
    token = await login_token(client, "applicant")
    perms = (await client.get("/api/v1/users/me/permissions", headers=AUTH(token))).json()
    assert "agent:list" not in perms["data"]
