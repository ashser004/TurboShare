"""
TurboShare — Static file handler.

Serves the mobile web UI files (HTML, CSS, JS) and app assets
(Lottie animations, fonts, lottie-web library, logo).
"""

import mimetypes
import logging
from pathlib import Path

from aiohttp import web

from src.core.config import MOBILE_DIR, ASSETS_DIR

log = logging.getLogger(__name__)

# Ensure modern MIME types are registered
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/woff", ".woff")


async def serve_mobile_page(request: web.Request) -> web.StreamResponse:
    """Serve the mobile SPA entry point (index.html)."""
    index_path = MOBILE_DIR / "index.html"
    if not index_path.is_file():
        raise web.HTTPNotFound(text="Mobile UI not found")
    return web.FileResponse(index_path, headers={
        "Cache-Control": "no-cache, no-store, must-revalidate",
    })


async def serve_static(request: web.Request) -> web.StreamResponse:
    """Serve a static file from mobile/ or assets/ directories.

    Path format: /ts/{token}/static/{category}/{rest_of_path}
    Categories: css, js, fonts, animations, images
    """
    full_path_str = request.match_info.get("path", "")

    if not full_path_str:
        raise web.HTTPNotFound()

    # Security: prevent path traversal
    if ".." in full_path_str or full_path_str.startswith("/"):
        raise web.HTTPForbidden()

    # Try mobile/ first, then assets/
    candidate = MOBILE_DIR / full_path_str
    if not candidate.is_file():
        candidate = ASSETS_DIR / full_path_str
    if not candidate.is_file():
        # Also check under assets subdirectories directly
        for subdir in ["js", "fonts", "animations", "images"]:
            candidate = ASSETS_DIR / subdir / full_path_str
            if candidate.is_file():
                break
        else:
            log.warning("Static file not found: %s", full_path_str)
            raise web.HTTPNotFound()

    # Resolve and verify it's within allowed directories
    resolved = candidate.resolve()
    mobile_resolved = MOBILE_DIR.resolve()
    assets_resolved = ASSETS_DIR.resolve()

    if not (
        str(resolved).startswith(str(mobile_resolved))
        or str(resolved).startswith(str(assets_resolved))
    ):
        raise web.HTTPForbidden()

    # MIME type
    content_type, _ = mimetypes.guess_type(str(resolved))
    if content_type is None:
        content_type = "application/octet-stream"

    # Cache headers
    cache = "no-cache" if resolved.suffix in (".html",) else "public, max-age=3600"

    return web.FileResponse(resolved, headers={
        "Cache-Control": cache,
    })
