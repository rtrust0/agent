from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.database import init_db
from app.core.exceptions import register_exception_handlers
from app.core.request_context import RequestContextMiddleware
from app.modules.agent.api import router as agent_router
from app.modules.approval.api import router as approval_router
from app.modules.audit.api import router as audit_router
from app.modules.auth.api import router as auth_router
from app.modules.knowledge.api import router as knowledge_router
from app.modules.model.api import router as model_router
from app.modules.permission.api import router as permission_router
from app.modules.prompt.api import router as prompt_router
from app.modules.role.api import router as role_router
from app.modules.tool.api import router as tool_router
from app.modules.user.api import router as user_router

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        version="2.0.0",
        debug=settings.APP_DEBUG,
        lifespan=lifespan,
    )
    register_exception_handlers(app)
    app.add_middleware(RequestContextMiddleware)

    for router in (
        auth_router,
        user_router,
        role_router,
        permission_router,
        audit_router,
        approval_router,
        model_router,
        agent_router,
        prompt_router,
        knowledge_router,
        tool_router,
    ):
        app.include_router(router, prefix=API_PREFIX)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
