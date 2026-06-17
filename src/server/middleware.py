"""
TurboShare — aiohttp middleware stack.

Three layers applied to every request:
  1. Token validation — reject unknown session tokens with 404
  2. IP lock — reject requests from non-locked IPs with 503
  3. Rate limiting — throttle PIN attempts to 1 per 2 seconds per IP
"""

import time
import logging

from aiohttp import web

from src.security.token_manager import validate_token

log = logging.getLogger(__name__)


def get_client_ip(request: web.Request) -> str:
    """Extract the real client IP from the request."""
    transport = request.transport
    if transport is not None:
        peername = transport.get_extra_info("peername")
        if peername:
            return peername[0]
    return request.remote or "0.0.0.0"


@web.middleware
async def token_middleware(request: web.Request, handler):
    """Validate the session token in the URL path."""
    session = request.app.get("session")
    if session is None:
        raise web.HTTPNotFound()

    # Extract token from the path: /ts/{token}/...
    token = request.match_info.get("token", "")
    if not token or not validate_token(token, session.token):
        raise web.HTTPNotFound()

    return await handler(request)


@web.middleware
async def ip_lock_middleware(request: web.Request, handler):
    """Reject requests from IPs that are not the locked session IP."""
    session = request.app.get("session")
    if session is None:
        raise web.HTTPNotFound()

    client_ip = get_client_ip(request)

    # Skip IP lock check for routes before authentication
    path = request.path
    if path.endswith("/api/verify-pin") or path.endswith("/"):
        return await handler(request)

    if not session.is_ip_allowed(client_ip):
        log.warning("Blocked request from non-locked IP %s", client_ip)
        raise web.HTTPServiceUnavailable(
            text='{"error": "Session Busy — another device is connected"}',
            content_type="application/json",
        )

    return await handler(request)


@web.middleware
async def rate_limit_middleware(request: web.Request, handler):
    """Rate-limit PIN verification to 1 attempt per 2 seconds per IP."""
    if not request.path.endswith("/api/verify-pin"):
        return await handler(request)

    client_ip = get_client_ip(request)
    rate_map: dict = request.app.setdefault("_rate_limits", {})
    last_attempt = rate_map.get(client_ip, 0)
    now = time.monotonic()

    from src.core.config import PIN_RATE_LIMIT_SECONDS

    if now - last_attempt < PIN_RATE_LIMIT_SECONDS:
        raise web.HTTPTooManyRequests(
            text='{"error": "Too many attempts. Wait 2 seconds."}',
            content_type="application/json",
        )

    rate_map[client_ip] = now
    return await handler(request)
