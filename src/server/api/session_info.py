"""
TurboShare — Session info endpoint.

GET /ts/{token}/api/session-info

Returns the file list, session mode, and total size so the mobile
browser can display what is about to be transferred.
"""

import math
from aiohttp import web
from src.core.config import CHUNK_SIZE


async def session_info(request: web.Request) -> web.Response:
    """Return session metadata for the mobile UI."""
    session = request.app["session"]

    files = []
    for f in session.files:
        total_chunks = max(1, math.ceil(f.size / CHUNK_SIZE))
        files.append({
            "id": f.id,
            "name": f.name,
            "size": f.size,
            "total_chunks": total_chunks,
            "chunk_size": CHUNK_SIZE,
        })

    return web.json_response({
        "mode": session.mode.value,
        "files": files,
        "total_size": session.total_size,
        "state": session.state.value,
    })
