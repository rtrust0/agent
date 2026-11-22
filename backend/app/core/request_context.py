"""请求上下文：把 IP / User-Agent 注入 contextvar，供 Service 层写审计日志时读取。

Service 层不接触 HTTP 对象（分层约束），由中间件在请求入口写入、请求结束清理。
"""

from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_client_ip: ContextVar[str] = ContextVar("client_ip", default="")
_user_agent: ContextVar[str] = ContextVar("user_agent", default="")

MAX_USER_AGENT_LENGTH = 300


class RequestContextMiddleware(BaseHTTPMiddleware):
    """记录调用方 IP 与 User-Agent。"""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        ip_token = _client_ip.set(request.client.host if request.client else "")
        ua_token = _user_agent.set(
            (request.headers.get("user-agent") or "")[:MAX_USER_AGENT_LENGTH]
        )
        try:
            return await call_next(request)
        finally:
            _client_ip.reset(ip_token)
            _user_agent.reset(ua_token)


def client_ip() -> str:
    return _client_ip.get()


def user_agent() -> str:
    return _user_agent.get()
