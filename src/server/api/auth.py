"""
TurboShare — PIN verification endpoint.

POST /ts/{token}/api/verify-pin
Body: {"pin": "123456"}
Returns: {"status": "ok"|"wrong"|"rate_limited"|"max_attempts"|"expired",
          "remaining": N}

On successful verification, locks the session to the requester's IP
and captures device info from User-Agent.
"""

import logging
from aiohttp import web

from src.server.middleware import get_client_ip

log = logging.getLogger(__name__)


def _parse_user_agent(ua: str) -> dict:
    """Extract browser and OS from a User-Agent string."""
    browser = "Unknown"
    os_name = "Unknown"

    ua_lower = ua.lower()

    # OS detection
    if "iphone" in ua_lower or "ipad" in ua_lower:
        os_name = "iOS"
    elif "android" in ua_lower:
        os_name = "Android"
    elif "windows" in ua_lower:
        os_name = "Windows"
    elif "macintosh" in ua_lower or "mac os" in ua_lower:
        os_name = "macOS"
    elif "linux" in ua_lower:
        os_name = "Linux"

    # Browser detection (order matters — check specific before generic)
    if "edg/" in ua_lower:
        browser = "Edge"
    elif "opr/" in ua_lower or "opera" in ua_lower:
        browser = "Opera"
    elif "firefox" in ua_lower:
        browser = "Firefox"
    elif "samsungbrowser" in ua_lower:
        browser = "Samsung Internet"
    elif "crios" in ua_lower:
        browser = "Chrome (iOS)"
    elif "fxios" in ua_lower:
        browser = "Firefox (iOS)"
    elif "chrome" in ua_lower and "safari" in ua_lower:
        browser = "Chrome"
    elif "safari" in ua_lower:
        browser = "Safari"

    return {"browser": browser, "os": os_name}


async def verify_pin(request: web.Request) -> web.Response:
    """Handle PIN verification."""
    session = request.app["session"]

    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"status": "error", "message": "Invalid request body"}, status=400
        )

    provided_pin = str(body.get("pin", "")).strip()
    if not provided_pin:
        return web.json_response(
            {"status": "error", "message": "PIN is required"}, status=400
        )

    client_ip = get_client_ip(request)
    result = session.pin_manager.verify(client_ip, provided_pin)

    if result == "ok":
        # Lock session to this IP
        session.lock_to_ip(client_ip)

        # Capture device info
        ua = request.headers.get("User-Agent", "")
        device = _parse_user_agent(ua)

        from src.core.session import DeviceInfo
        session.device_info = DeviceInfo(
            browser=device["browser"],
            os=device["os"],
            ip=client_ip,
        )

        return web.json_response({"status": "ok"})

    elif result == "wrong":
        remaining = 3 - session.pin_manager.failures
        return web.json_response({
            "status": "wrong",
            "message": f"Incorrect PIN. {remaining} attempt(s) remaining.",
            "remaining": remaining,
        })

    elif result == "rate_limited":
        return web.json_response({
            "status": "rate_limited",
            "message": "Too many attempts. Wait 2 seconds.",
        }, status=429)

    elif result == "max_attempts":
        # Kill session, regenerate
        log.warning("Max PIN attempts reached — regenerating session")
        session.regenerate()
        return web.json_response({
            "status": "max_attempts",
            "message": "Too many failed attempts. Session has been reset. Scan the new QR code.",
        }, status=403)

    elif result == "expired":
        session.regenerate()
        return web.json_response({
            "status": "expired",
            "message": "PIN has expired. Session has been reset. Scan the new QR code.",
        }, status=403)

    return web.json_response({"status": "error"}, status=500)
