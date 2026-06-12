"""
TurboShare — Real-time progress SSE endpoint.

GET /ts/{token}/api/progress

Pushes JSON progress snapshots every 500ms via Server-Sent Events.
The mobile browser UI connects here to show live transfer progress.
"""

import asyncio
import json
import logging

from aiohttp import web

from src.core.session import SessionState
from src.core.config import PROGRESS_SSE_INTERVAL_MS

log = logging.getLogger(__name__)


async def progress_sse(request: web.Request) -> web.StreamResponse:
    """SSE endpoint streaming transfer progress to the mobile browser."""
    session = request.app["session"]
    engine = request.app["transfer_engine"]

    response = web.StreamResponse()
    response.content_type = "text/event-stream"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["X-Accel-Buffering"] = "no"
    await response.prepare(request)

    interval = PROGRESS_SSE_INTERVAL_MS / 1000.0

    try:
        while True:
            state = session.state

            if state == SessionState.CANCELLED:
                data = json.dumps({"event": "cancelled"})
                await response.write(f"data: {data}\n\n".encode())
                break

            if state == SessionState.TRANSFERRING:
                snapshot = engine.get_progress_snapshot()
                snapshot["event"] = "progress"
                await response.write(
                    f"data: {json.dumps(snapshot)}\n\n".encode()
                )

            elif state == SessionState.COMPLETED:
                snapshot = engine.get_progress_snapshot()
                snapshot["event"] = "completed"
                await response.write(
                    f"data: {json.dumps(snapshot)}\n\n".encode()
                )
                break

            elif state == SessionState.ERROR:
                data = json.dumps({"event": "error", "message": "Transfer failed"})
                await response.write(f"data: {data}\n\n".encode())
                break

            else:
                # Not yet transferring — send a heartbeat
                data = json.dumps({"event": "waiting", "state": state.value})
                await response.write(f"data: {data}\n\n".encode())

            await asyncio.sleep(interval)

    except (ConnectionResetError, ConnectionAbortedError):
        log.debug("Progress SSE connection closed by client")
    except asyncio.CancelledError:
        pass

    return response
