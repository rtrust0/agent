import re
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import assert_in_scope, scope_condition
from app.core.deps import PageParams
from app.core.exceptions import BizException
from app.core.versioning import next_version
from app.modules.audit.service import AuditService
from app.modules.prompt.model import Prompt, PromptVersion
from app.modules.prompt.repository import PromptRepository, PromptVersionRepository
from app.modules.prompt.schema import (
    PromptCreate,
    PromptTestResult,
    PromptUpdate,
)
from app.modules.user.model import User

VARIABLE_PATTERN = re.compile(r"\{\{\s*(\w+)\s*\}\}")


class PromptService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = PromptRepository(db)
        self.version_repo = PromptVersionRepository(db)
        self.audit = AuditService(db)

    async def list_prompts(
        self,
        params: PageParams,
        current_user: User,
        *,
        category: str | None = None,
        status: str | None = None,
    ) -> tuple[list[Prompt], int]:
        conditions = []
        scope = scope_condition(Prompt, current_user)
        if scope is not None:
            conditions.append(scope)
        if category:
            conditions.append(Prompt.category == category)
        if status:
            conditions.append(Prompt.status == status)
        return await self.repo.get_page(
            params.offset, params.page_size, params.keyword, extra_conditions=conditions or None
        )

    async def get_prompt(self, prompt_id: int, current_user: User) -> Prompt:
        prompt = await self.repo.get_by_id(prompt_id)
        if not prompt:
            raise BizException(code=404, message="Prompt 不存在")
        assert_in_scope(prompt, current_user, message="没有权限访问该 Prompt")
        return prompt

    async def create(self, actor: User, data: PromptCreate) -> Prompt:
        prompt = Prompt(
            name=data.name.strip(),
            description=data.description,
            category=data.category,
            tags=data.tags,
            content=data.content,
            variables=data.variables,
            version="v0.1",
            status="draft",
            created_by=actor.username,
        )
        self.db.add(prompt)
        await self.db.flush()
        self.audit.record(
            actor,
            module="prompt",
            action="create",
            target_id=prompt.id,
            target_name=prompt.name,
            detail={"category": prompt.category},
        )
        await self.db.commit()
        await self.db.refresh(prompt)
        return prompt

    async def update(self, actor: User, prompt_id: int, data: PromptUpdate) -> Prompt:
        prompt = await self.get_prompt(prompt_id, actor)
        if data.status is not None and data.status != "draft":
            raise BizException(code=400, message="请使用发布接口发布 Prompt")
        before = {
            "name": prompt.name,
            "status": prompt.status,
            "version": prompt.version,
            "content_length": len(prompt.content),
        }
        for field in ("name", "description", "category", "tags", "content", "variables", "status"):
            value = getattr(data, field)
            if value is not None:
                setattr(prompt, field, value)
        self.audit.record(
            actor,
            module="prompt",
            action="update",
            target_id=prompt.id,
            target_name=prompt.name,
            detail={
                "before": before,
                "after": {
                    "name": prompt.name,
                    "status": prompt.status,
                    "version": prompt.version,
                    "content_length": len(prompt.content),
                },
            },
        )
        await self.db.commit()
        await self.db.refresh(prompt)
        return prompt

    async def delete(self, actor: User, prompt_id: int) -> None:
        prompt = await self.get_prompt(prompt_id, actor)
        self.audit.record(
            actor, module="prompt", action="delete", target_id=prompt.id, target_name=prompt.name
        )
        await self.repo.delete(prompt)
        await self.db.commit()

    async def publish(self, actor: User, prompt_id: int, changelog: str | None) -> Prompt:
        prompt = await self.get_prompt(prompt_id, actor)
        history = await self.version_repo.list_by_prompt(prompt.id)
        new_version = next_version(
            [item.version for item in history] + [prompt.version], prompt.version
        )
        await self.version_repo.clear_current(prompt.id)
        version = PromptVersion(
            prompt_id=prompt.id,
            version=new_version,
            content=prompt.content,
            changelog=changelog or "发布新版本",
            is_current=True,
            published_by=actor.username,
            published_at=datetime.now(),
        )
        self.db.add(version)
        prompt.version = new_version
        prompt.status = "published"
        self.audit.record(
            actor,
            module="prompt",
            action="publish",
            target_id=prompt.id,
            target_name=prompt.name,
            detail={"version": new_version, "changelog": changelog},
        )
        await self.db.commit()
        await self.db.refresh(prompt)
        return prompt

    async def list_versions(self, prompt_id: int, current_user: User) -> list[PromptVersion]:
        prompt = await self.get_prompt(prompt_id, current_user)
        return await self.version_repo.list_by_prompt(prompt.id)

    async def rollback(self, actor: User, prompt_id: int, version_name: str) -> Prompt:
        prompt = await self.get_prompt(prompt_id, actor)
        version = await self.version_repo.get_by_version(prompt.id, version_name)
        if not version:
            raise BizException(code=404, message="目标版本不存在")
        await self.version_repo.clear_current(prompt.id)
        version.is_current = True
        prompt.content = version.content
        prompt.version = version.version
        prompt.status = "published"
        self.audit.record(
            actor,
            module="prompt",
            action="rollback",
            target_id=prompt.id,
            target_name=prompt.name,
            detail={"version": version.version},
        )
        await self.db.commit()
        await self.db.refresh(prompt)
        return prompt

    async def test(
        self, actor: User, prompt_id: int, variables: dict[str, str]
    ) -> PromptTestResult:
        prompt = await self.get_prompt(prompt_id, actor)
        missing = [name for name in VARIABLE_PATTERN.findall(prompt.content) if name not in variables]

        def _replace(match: re.Match[str]) -> str:
            return variables.get(match.group(1), match.group(0))

        rendered = VARIABLE_PATTERN.sub(_replace, prompt.content)
        self.audit.record(
            actor,
            module="prompt",
            action="test",
            target_id=prompt.id,
            target_name=prompt.name,
            detail={"missing_variables": missing},
        )
        await self.db.commit()
        return PromptTestResult(
            prompt_id=prompt.id, rendered=rendered, missing_variables=sorted(set(missing))
        )
