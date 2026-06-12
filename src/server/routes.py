"""
TurboShare — Route registration.

Maps URL paths to handler functions.  All routes are scoped under
``/ts/{token}/`` so the token middleware validates every request.
"""

from aiohttp import web

from src.server.static_handler import serve_mobile_page, serve_static
from src.server.api.auth import verify_pin
from src.server.api.handshake import (
    receiver_confirm,
    sender_confirm,
    handshake_sse,
    client_ready,
)
from src.server.api.transfer import (
    download_chunk,
    download_file,
    upload_chunk,
    upload_init,
)
from src.server.api.progress import progress_sse
from src.server.api.session_info import session_info


def setup_routes(app: web.Application) -> None:
    """Register all routes on the aiohttp application."""
    prefix = "/ts/{token}"

    app.router.add_routes([
        # ── Mobile UI pages ─────────────────────────────────────────
        web.get(f"{prefix}/", serve_mobile_page),
        web.get(f"{prefix}/static/{{path:.*}}", serve_static),

        # ── Authentication ──────────────────────────────────────────
        web.post(f"{prefix}/api/verify-pin", verify_pin),

        # ── Session info ────────────────────────────────────────────
        web.get(f"{prefix}/api/session-info", session_info),

        # ── Three-stage handshake ───────────────────────────────────
        web.post(f"{prefix}/api/confirm", receiver_confirm),
        web.post(f"{prefix}/api/sender-confirm", sender_confirm),
        web.get(f"{prefix}/api/handshake", handshake_sse),
        web.post(f"{prefix}/api/ready", client_ready),

        # ── Transfer ────────────────────────────────────────────────
        web.get(f"{prefix}/api/chunk/{{file_id}}/{{chunk_index}}", download_chunk),
        web.get(f"{prefix}/api/download/{{file_id}}", download_file),
        web.post(f"{prefix}/api/chunk/{{file_id}}/{{chunk_index}}", upload_chunk),
        web.post(f"{prefix}/api/upload-init", upload_init),

        # ── Progress ────────────────────────────────────────────────
        web.get(f"{prefix}/api/progress", progress_sse),
    ])
