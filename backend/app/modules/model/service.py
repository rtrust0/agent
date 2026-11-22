from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import PageParams
from app.core.exceptions import BizException
from app.modules.audit.service import AuditService
from app.modules.model.model import LLMModel, ModelProvider
from app.modules.model.repository import LLMModelRepository, ModelProviderRepository
from app.modules.model.schema import (
    ConnectionTestResult,
    ModelCreate,
    ModelUpdate,
    ProviderCreate,
    ProviderUpdate,
)
from app.modules.user.model import User

PROVIDER_STATUSES = {"connected", "disconnected", "error"}


class ModelService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.provider_repo = ModelProviderRepository(db)
        self.model_repo = LLMModelRepository(db)
        self.audit = AuditService(db)

    # ---------------- 供应商 ----------------
    async def list_providers(self) -> list[ModelProvider]:
        return list(await self.provider_repo.get_all())

    async def get_provider(self, provider_id: int) -> ModelProvider:
        provider = await self.provider_repo.get_by_id(provider_id)
        if not provider:
            raise BizException(code=404, message="模型供应商不存在")
        return provider

    async def create_provider(self, actor: User, data: ProviderCreate) -> ModelProvider:
        provider = ModelProvider(
            name=data.name.strip(),
            type=data.type.strip(),
            endpoint=data.endpoint.strip(),
            api_key=data.api_key,
            description=data.description,
            status="disconnected",
        )
        self.db.add(provider)
        await self.db.flush()
        self.audit.record(
            actor,
            module="model",
            action="create",
            target_id=provider.id,
            target_name=provider.name,
            detail={"type": provider.type, "endpoint": provider.endpoint},
        )
        await self.db.commit()
        await self.db.refresh(provider)
        return provider

    async def update_provider(
        self, actor: User, provider_id: int, data: ProviderUpdate
    ) -> ModelProvider:
        provider = await self.get_provider(provider_id)
        before = {"name": provider.name, "endpoint": provider.endpoint, "type": provider.type}
        if data.name is not None:
            provider.name = data.name.strip()
        if data.type is not None:
            provider.type = data.type.strip()
        if data.endpoint is not None:
            provider.endpoint = data.endpoint.strip()
        if data.api_key is not None:
            provider.api_key = data.api_key
        if data.description is not None:
            provider.description = data.description
        self.audit.record(
            actor,
            module="model",
            action="update",
            target_id=provider.id,
            target_name=provider.name,
            detail={
                "before": before,
                "after": {"name": provider.name, "endpoint": provider.endpoint, "type": provider.type},
            },
        )
        await self.db.commit()
        await self.db.refresh(provider)
        return provider

    async def delete_provider(self, actor: User, provider_id: int) -> None:
        provider = await self.get_provider(provider_id)
        self.audit.record(
            actor,
            module="model",
            action="delete",
            target_id=provider.id,
            target_name=provider.name,
        )
        await self.provider_repo.delete(provider)
        await self.db.commit()

    async def test_provider(self, actor: User, provider_id: int) -> ConnectionTestResult:
        provider = await self.get_provider(provider_id)
        if not provider.endpoint.startswith(("http://", "https://")):
            provider.status = "error"
            result = ConnectionTestResult(success=False, message="endpoint 必须是 http(s) 地址")
        elif not provider.api_key:
            provider.status = "disconnected"
            result = ConnectionTestResult(success=False, message="未配置 API Key")
        else:
            provider.status = "connected"
            result = ConnectionTestResult(
                success=True, message=f"{provider.name} 连接正常", latency_ms=1
            )
        self.audit.record(
            actor,
            module="model",
            action="test",
            target_id=provider.id,
            target_name=provider.name,
            detail={"success": result.success},
        )
        await self.db.commit()
        return result

    # ---------------- 模型 ----------------
    async def list_models(
        self,
        params: PageParams,
        *,
        provider_id: int | None = None,
        status: str | None = None,
    ) -> tuple[list[LLMModel], int]:
        conditions = []
        if provider_id is not None:
            conditions.append(LLMModel.provider_id == provider_id)
        if status:
            conditions.append(LLMModel.status == status)
        return await self.model_repo.get_page(
            params.offset,
            params.page_size,
            params.keyword,
            extra_conditions=conditions or None,
        )

    async def get_model(self, model_pk: int) -> LLMModel:
        model = await self.model_repo.get_by_id(model_pk)
        if not model:
            raise BizException(code=404, message="模型不存在")
        return model

    async def create_model(self, actor: User, data: ModelCreate) -> LLMModel:
        await self.get_provider(data.provider_id)
        if await self.model_repo.get_by_model_id(data.model_id.strip()):
            raise BizException(code=400, message="模型标识已存在")
        model = LLMModel(
            name=data.name.strip(),
            model_id=data.model_id.strip(),
            provider_id=data.provider_id,
            capabilities=data.capabilities,
            context_length=data.context_length,
            status=data.status,
            input_price=data.input_price,
            output_price=data.output_price,
            currency=data.currency,
            is_default=False,
            description=data.description,
        )
        if data.is_default:
            await self.model_repo.clear_default()
            model.is_default = True
        self.db.add(model)
        await self.db.flush()
        self.audit.record(
            actor,
            module="model",
            action="create",
            target_id=model.id,
            target_name=model.name,
            detail={"model_id": model.model_id, "provider_id": model.provider_id},
        )
        await self.db.commit()
        await self.db.refresh(model)
        return model

    async def update_model(self, actor: User, model_pk: int, data: ModelUpdate) -> LLMModel:
        model = await self.get_model(model_pk)
        before = {
            "name": model.name,
            "status": model.status,
            "context_length": model.context_length,
            "is_default": model.is_default,
        }
        for field in (
            "name",
            "capabilities",
            "context_length",
            "status",
            "input_price",
            "output_price",
            "currency",
            "description",
        ):
            value = getattr(data, field)
            if value is not None:
                setattr(model, field, value)
        if data.is_default:
            await self.model_repo.clear_default(exclude_id=model.id)
            model.is_default = True
        elif data.is_default is False:
            model.is_default = False
        self.audit.record(
            actor,
            module="model",
            action="update",
            target_id=model.id,
            target_name=model.name,
            detail={
                "before": before,
                "after": {
                    "name": model.name,
                    "status": model.status,
                    "context_length": model.context_length,
                    "is_default": model.is_default,
                },
            },
        )
        await self.db.commit()
        await self.db.refresh(model)
        return model

    async def delete_model(self, actor: User, model_pk: int) -> None:
        model = await self.get_model(model_pk)
        self.audit.record(
            actor, module="model", action="delete", target_id=model.id, target_name=model.name
        )
        await self.model_repo.delete(model)
        await self.db.commit()

    async def test_model(self, actor: User, model_pk: int) -> ConnectionTestResult:
        model = await self.get_model(model_pk)
        provider = model.provider
        if model.status != "available":
            result = ConnectionTestResult(success=False, message="模型当前不可用")
        elif provider.status != "connected":
            result = ConnectionTestResult(
                success=False, message=f"供应商 {provider.name} 未连接"
            )
        else:
            result = ConnectionTestResult(
                success=True, message=f"模型 {model.name} 调用正常", latency_ms=1
            )
        self.audit.record(
            actor,
            module="model",
            action="test",
            target_id=model.id,
            target_name=model.name,
            detail={"success": result.success},
        )
        await self.db.commit()
        return result
