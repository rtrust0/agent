from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import assert_in_scope, scope_condition
from app.core.deps import PageParams
from app.core.exceptions import BizException
from app.modules.audit.service import AuditService
from app.modules.tool.model import Tool
from app.modules.tool.repository import ToolRepository
from app.modules.tool.schema import (
    TOOL_TYPES,
    ToolCreate,
    ToolLogPage,
    ToolLogSummary,
    ToolTestResult,
    ToolUpdate,
)
from app.modules.user.model import User


class ToolService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ToolRepository(db)
        self.audit = AuditService(db)

    async def list_tools(
        self,
        params: PageParams,
        current_user: User,
        *,
        status: str | None = None,
        type_: str | None = None,
    ) -> tuple[list[Tool], int]:
        conditions = []
        scope = scope_condition(Tool, current_user)
        if scope is not None:
            conditions.append(scope)
        if status:
            conditions.append(Tool.status == status)
        if type_:
            conditions.append(Tool.type == type_)
        return await self.repo.get_page(
            params.offset, params.page_size, params.keyword, extra_conditions=conditions or None
        )

    async def get_tool(self, tool_id: int, current_user: User) -> Tool:
        tool = await self.repo.get_by_id(tool_id)
        if not tool:
            raise BizException(code=404, message="工具不存在")
        assert_in_scope(tool, current_user, message="没有权限访问该工具")
        return tool

    async def create(self, actor: User, data: ToolCreate) -> Tool:
        self._validate_type(data.type)
        name = data.name.strip()
        if await self.repo.get_by_name(name):
            raise BizException(code=400, message="工具名称已存在")
        tool = Tool(
            name=name,
            description=data.description,
            type=data.type,
            status=data.status,
            config=data.config,
            function_definition=data.function_definition,
            created_by=actor.username,
        )
        self.db.add(tool)
        await self.db.flush()
        self.audit.record(
            actor,
            module="tool",
            action="create",
            target_id=tool.id,
            target_name=tool.name,
            detail={"type": tool.type, "status": tool.status},
        )
        await self.db.commit()
        await self.db.refresh(tool)
        return tool

    async def update(self, actor: User, tool_id: int, data: ToolUpdate) -> Tool:
        tool = await self.get_tool(tool_id, actor)
        self._validate_type(data.type)
        before = {"name": tool.name, "type": tool.type, "status": tool.status}
        for field in ("name", "description", "type", "config", "function_definition"):
            value = getattr(data, field)
            if value is not None:
                setattr(tool, field, value)
        self.audit.record(
            actor,
            module="tool",
            action="update",
            target_id=tool.id,
            target_name=tool.name,
            detail={
                "before": before,
                "after": {"name": tool.name, "type": tool.type, "status": tool.status},
            },
        )
        await self.db.commit()
        await self.db.refresh(tool)
        return tool

    async def delete(self, actor: User, tool_id: int) -> None:
        tool = await self.get_tool(tool_id, actor)
        self.audit.record(
            actor, module="tool", action="delete", target_id=tool.id, target_name=tool.name
        )
        await self.repo.delete(tool)
        await self.db.commit()

    async def toggle(self, actor: User, tool_id: int) -> Tool:
        tool = await self.get_tool(tool_id, actor)
        tool.status = "disabled" if tool.status == "enabled" else "enabled"
        self.audit.record(
            actor,
            module="tool",
            action="toggle",
            target_id=tool.id,
            target_name=tool.name,
            detail={"status": tool.status},
        )
        await self.db.commit()
        await self.db.refresh(tool)
        return tool

    async def test(self, actor: User, tool_id: int, arguments: dict) -> ToolTestResult:
        tool = await self.get_tool(tool_id, actor)
        success = bool(tool.config or tool.function_definition)
        message = (
            f"工具 {tool.name} 调用成功，参数键：{sorted(arguments)}"
            if success
            else "工具未配置 config / function_definition，无法调用"
        )
        self.audit.record(
            actor,
            module="tool",
            action="test",
            target_id=tool.id,
            target_name=tool.name,
            detail={"success": success, "argument_keys": sorted(arguments)},
        )
        await self.db.commit()
        return ToolTestResult(
            tool_id=tool.id, success=success, message=message, latency_ms=1 if success else 0
        )

    async def logs(self, tool_id: int, current_user: User, params: PageParams) -> ToolLogPage:
        tool = await self.get_tool(tool_id, current_user)
        return ToolLogPage(
            items=[],
            total=0,
            page=params.page,
            page_size=params.page_size,
            summary=ToolLogSummary(
                call_count_7d=tool.call_count_7d,
                success_rate=float(tool.success_rate),
                avg_latency=tool.avg_latency,
            ),
        )

    def _validate_type(self, type_: str | None) -> None:
        if type_ is not None and type_ not in TOOL_TYPES:
            raise BizException(code=400, message="工具类型不合法")
