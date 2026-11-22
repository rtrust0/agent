import secrets
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BizException
from app.modules.audit.service import AuditService
from app.modules.system.model import Alert, AlertRule, ApiKey, SystemSetting
from app.modules.system.repository import (
    AlertRepository,
    AlertRuleRepository,
    ApiKeyRepository,
    SystemSettingRepository,
)
from app.modules.system.schema import (
    AlertRuleCreate,
    AlertRuleUpdate,
    ApiKeyCreate,
    ApiKeyUpdate,
    SettingsUpdate,
)
from app.modules.user.model import User


class SystemService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.key_repo = ApiKeyRepository(db)
        self.rule_repo = AlertRuleRepository(db)
        self.alert_repo = AlertRepository(db)
        self.setting_repo = SystemSettingRepository(db)
        self.audit = AuditService(db)

    # ---------------- API 密钥 ----------------
    async def list_api_keys(self) -> list[ApiKey]:
        return list(await self.key_repo.get_all())

    async def _get_api_key(self, key_id: int) -> ApiKey:
        api_key = await self.key_repo.get_by_id(key_id)
        if not api_key:
            raise BizException(code=404, message="API 密钥不存在")
        return api_key

    async def create_api_key(self, actor: User, data: ApiKeyCreate) -> ApiKey:
        api_key = ApiKey(
            name=data.name.strip(),
            key=f"sk-{secrets.token_hex(16)}",
            permissions=data.permissions,
            status="active",
            rate_limit=data.rate_limit,
            expires_at=data.expires_at,
            allowed_agent_ids=data.allowed_agent_ids,
            created_by=actor.username,
        )
        self.db.add(api_key)
        await self.db.flush()
        self.audit.record(
            actor,
            module="system",
            action="create",
            target_id=api_key.id,
            target_name=api_key.name,
            detail={"permissions": api_key.permissions},
        )
        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key

    async def update_api_key(self, actor: User, key_id: int, data: ApiKeyUpdate) -> ApiKey:
        api_key = await self._get_api_key(key_id)
        before = {
            "name": api_key.name,
            "status": api_key.status,
            "rate_limit": api_key.rate_limit,
        }
        for field in ("name", "permissions", "status", "rate_limit", "expires_at", "allowed_agent_ids"):
            value = getattr(data, field)
            if value is not None:
                setattr(api_key, field, value)
        self.audit.record(
            actor,
            module="system",
            action="update",
            target_id=api_key.id,
            target_name=api_key.name,
            detail={
                "before": before,
                "after": {
                    "name": api_key.name,
                    "status": api_key.status,
                    "rate_limit": api_key.rate_limit,
                },
            },
        )
        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key

    async def delete_api_key(self, actor: User, key_id: int) -> None:
        api_key = await self._get_api_key(key_id)
        self.audit.record(
            actor,
            module="system",
            action="delete",
            target_id=api_key.id,
            target_name=api_key.name,
        )
        await self.key_repo.delete(api_key)
        await self.db.commit()

    # ---------------- 告警规则 ----------------
    async def list_alert_rules(self) -> list[AlertRule]:
        return list(await self.rule_repo.get_all())

    async def _get_rule(self, rule_id: int) -> AlertRule:
        rule = await self.rule_repo.get_by_id(rule_id)
        if not rule:
            raise BizException(code=404, message="告警规则不存在")
        return rule

    async def create_alert_rule(self, actor: User, data: AlertRuleCreate) -> AlertRule:
        rule = AlertRule(
            name=data.name.strip(),
            description=data.description,
            condition=data.condition,
            notification=data.notification,
            status=data.status,
            created_by=actor.username,
        )
        self.db.add(rule)
        await self.db.flush()
        self.audit.record(
            actor,
            module="system",
            action="create",
            target_id=rule.id,
            target_name=rule.name,
            detail={"condition": rule.condition},
        )
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def update_alert_rule(
        self, actor: User, rule_id: int, data: AlertRuleUpdate
    ) -> AlertRule:
        rule = await self._get_rule(rule_id)
        before = {"name": rule.name, "status": rule.status}
        for field in ("name", "description", "condition", "notification", "status"):
            value = getattr(data, field)
            if value is not None:
                setattr(rule, field, value)
        self.audit.record(
            actor,
            module="system",
            action="update",
            target_id=rule.id,
            target_name=rule.name,
            detail={"before": before, "after": {"name": rule.name, "status": rule.status}},
        )
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def delete_alert_rule(self, actor: User, rule_id: int) -> None:
        rule = await self._get_rule(rule_id)
        self.audit.record(
            actor, module="system", action="delete", target_id=rule.id, target_name=rule.name
        )
        await self.rule_repo.delete(rule)
        await self.db.commit()

    # ---------------- 告警记录 ----------------
    async def active_alerts(self) -> list[Alert]:
        return await self.alert_repo.list_active()

    async def _get_alert(self, alert_id: int) -> Alert:
        alert = await self.alert_repo.get_by_id(alert_id)
        if not alert:
            raise BizException(code=404, message="告警不存在")
        if alert.status == "resolved":
            raise BizException(code=400, message="告警已解决")
        return alert

    async def acknowledge_alert(self, actor: User, alert_id: int) -> Alert:
        alert = await self._get_alert(alert_id)
        alert.status = "acknowledged"
        alert.acknowledged_by = actor.username
        alert.acknowledged_at = datetime.now()
        self.audit.record(
            actor,
            module="system",
            action="acknowledge",
            target_id=alert.id,
            target_name=alert.title,
        )
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def resolve_alert(self, actor: User, alert_id: int) -> Alert:
        alert = await self._get_alert(alert_id)
        alert.status = "resolved"
        alert.resolved_at = datetime.now()
        if not alert.acknowledged_by:
            alert.acknowledged_by = actor.username
            alert.acknowledged_at = datetime.now()
        self.audit.record(
            actor,
            module="system",
            action="resolve",
            target_id=alert.id,
            target_name=alert.title,
        )
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    # ---------------- 系统配置 ----------------
    async def get_settings(self) -> SystemSetting:
        settings = await self.setting_repo.get_singleton()
        if not settings:
            settings = SystemSetting()
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)
        return settings

    async def update_settings(self, actor: User, data: SettingsUpdate) -> SystemSetting:
        settings = await self.get_settings()
        before = {
            "system_name": settings.system_name,
            "default_model": settings.default_model,
            "default_temperature": settings.default_temperature,
        }
        for field in (
            "system_name",
            "system_description",
            "default_language",
            "default_model",
            "default_temperature",
            "default_max_tokens",
            "smtp_server",
            "smtp_port",
            "sender_email",
        ):
            value = getattr(data, field)
            if value is not None:
                setattr(settings, field, value)
        self.audit.record(
            actor,
            module="system",
            action="update",
            target_id=settings.id,
            target_name="system_settings",
            detail={
                "before": before,
                "after": {
                    "system_name": settings.system_name,
                    "default_model": settings.default_model,
                    "default_temperature": settings.default_temperature,
                },
            },
        )
        await self.db.commit()
        await self.db.refresh(settings)
        return settings
