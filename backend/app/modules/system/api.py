from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_schema import ResponseSchema
from app.core.database import get_db
from app.core.deps import get_current_user_with_permission
from app.modules.system.schema import (
    AlertRead,
    AlertRuleCreate,
    AlertRuleRead,
    AlertRuleUpdate,
    ApiKeyCreate,
    ApiKeyRead,
    ApiKeyUpdate,
    SettingsRead,
    SettingsUpdate,
)
from app.modules.system.service import SystemService
from app.modules.user.model import User

router = APIRouter(prefix="/system", tags=["系统管理"])


def get_system_service(db: AsyncSession = Depends(get_db)) -> SystemService:
    return SystemService(db)


# ---------------- API 密钥 ----------------
@router.get("/api-keys", response_model=ResponseSchema[list[ApiKeyRead]], summary="API 密钥列表")
async def list_api_keys(
    svc: SystemService = Depends(get_system_service),
    _: User = Depends(get_current_user_with_permission("system:api_keys")),
) -> ResponseSchema[list[ApiKeyRead]]:
    keys = await svc.list_api_keys()
    return ResponseSchema(data=[ApiKeyRead.model_validate(k) for k in keys])


@router.post("/api-keys", response_model=ResponseSchema[ApiKeyRead], summary="创建 API 密钥")
async def create_api_key(
    data: ApiKeyCreate,
    svc: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user_with_permission("system:api_keys")),
) -> ResponseSchema[ApiKeyRead]:
    api_key = await svc.create_api_key(current_user, data)
    return ResponseSchema(data=ApiKeyRead.model_validate(api_key))


@router.put(
    "/api-keys/{key_id}", response_model=ResponseSchema[ApiKeyRead], summary="更新 API 密钥"
)
async def update_api_key(
    key_id: int,
    data: ApiKeyUpdate,
    svc: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user_with_permission("system:api_keys")),
) -> ResponseSchema[ApiKeyRead]:
    api_key = await svc.update_api_key(current_user, key_id, data)
    return ResponseSchema(data=ApiKeyRead.model_validate(api_key))


@router.delete(
    "/api-keys/{key_id}", response_model=ResponseSchema[None], summary="删除 API 密钥"
)
async def delete_api_key(
    key_id: int,
    svc: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user_with_permission("system:api_keys")),
) -> ResponseSchema[None]:
    await svc.delete_api_key(current_user, key_id)
    return ResponseSchema(data=None)


# ---------------- 告警规则 ----------------
@router.get(
    "/alerts/rules", response_model=ResponseSchema[list[AlertRuleRead]], summary="告警规则列表"
)
async def list_alert_rules(
    svc: SystemService = Depends(get_system_service),
    _: User = Depends(get_current_user_with_permission("system:alerts")),
) -> ResponseSchema[list[AlertRuleRead]]:
    rules = await svc.list_alert_rules()
    return ResponseSchema(data=[AlertRuleRead.model_validate(r) for r in rules])


@router.post(
    "/alerts/rules", response_model=ResponseSchema[AlertRuleRead], summary="创建告警规则"
)
async def create_alert_rule(
    data: AlertRuleCreate,
    svc: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user_with_permission("system:alerts")),
) -> ResponseSchema[AlertRuleRead]:
    rule = await svc.create_alert_rule(current_user, data)
    return ResponseSchema(data=AlertRuleRead.model_validate(rule))


@router.put(
    "/alerts/rules/{rule_id}",
    response_model=ResponseSchema[AlertRuleRead],
    summary="更新告警规则",
)
async def update_alert_rule(
    rule_id: int,
    data: AlertRuleUpdate,
    svc: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user_with_permission("system:alerts")),
) -> ResponseSchema[AlertRuleRead]:
    rule = await svc.update_alert_rule(current_user, rule_id, data)
    return ResponseSchema(data=AlertRuleRead.model_validate(rule))


@router.delete(
    "/alerts/rules/{rule_id}", response_model=ResponseSchema[None], summary="删除告警规则"
)
async def delete_alert_rule(
    rule_id: int,
    svc: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user_with_permission("system:alerts")),
) -> ResponseSchema[None]:
    await svc.delete_alert_rule(current_user, rule_id)
    return ResponseSchema(data=None)


@router.get(
    "/alerts/active", response_model=ResponseSchema[list[AlertRead]], summary="活跃告警"
)
async def list_active_alerts(
    svc: SystemService = Depends(get_system_service),
    _: User = Depends(get_current_user_with_permission("system:alerts")),
) -> ResponseSchema[list[AlertRead]]:
    alerts = await svc.active_alerts()
    return ResponseSchema(data=[AlertRead.model_validate(a) for a in alerts])


@router.post(
    "/alerts/{alert_id}/acknowledge",
    response_model=ResponseSchema[AlertRead],
    summary="确认告警",
)
async def acknowledge_alert(
    alert_id: int,
    svc: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user_with_permission("system:alerts")),
) -> ResponseSchema[AlertRead]:
    alert = await svc.acknowledge_alert(current_user, alert_id)
    return ResponseSchema(data=AlertRead.model_validate(alert))


@router.post(
    "/alerts/{alert_id}/resolve",
    response_model=ResponseSchema[AlertRead],
    summary="解决告警",
)
async def resolve_alert(
    alert_id: int,
    svc: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user_with_permission("system:alerts")),
) -> ResponseSchema[AlertRead]:
    alert = await svc.resolve_alert(current_user, alert_id)
    return ResponseSchema(data=AlertRead.model_validate(alert))


# ---------------- 系统配置 ----------------
@router.get("/settings", response_model=ResponseSchema[SettingsRead], summary="系统配置")
async def get_settings(
    svc: SystemService = Depends(get_system_service),
    _: User = Depends(get_current_user_with_permission("system:settings")),
) -> ResponseSchema[SettingsRead]:
    settings = await svc.get_settings()
    return ResponseSchema(data=SettingsRead.model_validate(settings))


@router.put("/settings", response_model=ResponseSchema[SettingsRead], summary="更新系统配置")
async def update_settings(
    data: SettingsUpdate,
    svc: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user_with_permission("system:settings")),
) -> ResponseSchema[SettingsRead]:
    settings = await svc.update_settings(current_user, data)
    return ResponseSchema(data=SettingsRead.model_validate(settings))
