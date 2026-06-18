"""
TurboShare — Three-stage confirmation handshake endpoints.

Stage 1: Receiver confirms intent   → POST /api/confirm
Stage 2: Sender verifies device     → POST /api/sender-confirm  (from desktop)
Stage 3: Protocol handshake         → GET  /api/handshake (SSE)
                                      POST /api/ready     (client ack)
"""

import asyncio
import json
import logging

from aiohttp import web

from src.core.session import SessionState

log = logging.getLogger(__name__)


async def receiver_confirm(request: web.Request) -> web.Response:
    """Stage 1: Mobile receiver taps Confirm after entering PIN.

    The mobile browser calls this after successful PIN verification.
    This tells the desktop app "I want these files."
    """
    session = request.app["session"]

    if session.state != SessionState.WAITING_FOR_RECEIVER:
        return web.json_response({
            "status": "error",
            "message": "Session is not waiting for receiver confirmation.",
        }, status=409)

    session.set_state(SessionState.RECEIVER_CONFIRMED)

    # Notify the desktop UI via signal
    if session.device_info:
        session.signals.receiver_connected.emit(session.device_info)

    if not session.safe_transfer:
        # Auto-confirm Stage 2
        session.set_state(SessionState.SENDER_CONFIRMED)
        log.info("Safe transfer is OFF: Stage 2 automatically confirmed")

    log.info("Stage 1 complete: receiver confirmed intent")
    return web.json_response({"status": "ok", "stage": 1})


async def sender_confirm(request: web.Request) -> web.Response:
    """Stage 2: Desktop sender verifies the receiver device and clicks Confirm.

    Called internally from the desktop app (not from the mobile browser).
    """
    session = request.app["session"]

    body = await request.json()
    action = body.get("action", "confirm")

    if action == "reject":
        log.info("Sender rejected the receiver — regenerating session")
        session.regenerate()
        return web.json_response({"status": "rejected"})

    if session.state != SessionState.RECEIVER_CONFIRMED:
        return web.json_response({
            "status": "error",
            "message": "Receiver has not confirmed yet.",
        }, status=409)

    session.set_state(SessionState.SENDER_CONFIRMED)
    log.info("Stage 2 complete: sender confirmed receiver")

    return web.json_response({"status": "ok", "stage": 2})


async def handshake_sse(request: web.Request) -> web.StreamResponse:
    """Stage 3: SSE endpoint — pushes handshake status to mobile browser.

    The browser connects here after Stage 1 and waits for the sender
    to confirm (Stage 2).  Once confirmed, the server pushes a 'ready'
    event.  The browser then calls POST /api/ready to acknowledge.
    """
    session = request.app["session"]

    response = web.StreamResponse()
    response.content_type = "text/event-stream"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["X-Accel-Buffering"] = "no"
    await response.prepare(request)

    try:
        # Poll until sender confirms or session changes
        while True:
            if session.state == SessionState.CANCELLED:
                data = json.dumps({"event": "session_cancelled"})
                await response.write(f"data: {data}\n\n".encode())
                break

            if session.state in (
                SessionState.SENDER_CONFIRMED,
                SessionState.HANDSHAKE_COMPLETE,
                SessionState.TRANSFERRING,
            ):
                data = json.dumps({"event": "ready", "stage": 2})
                await response.write(f"data: {data}\n\n".encode())
                break

            # Send heartbeat
            await response.write(f"data: {json.dumps({'event': 'waiting'})}\n\n".encode())
            await asyncio.sleep(1)

    except (ConnectionResetError, ConnectionAbortedError):
        log.debug("Handshake SSE connection closed by client")
    except asyncio.CancelledError:
        pass

    return response


async def client_ready(request: web.Request) -> web.Response:
    """Stage 3 completion: mobile browser acknowledges the 'ready' signal.

    After this, the actual file transfer begins.
    """
    session = request.app["session"]

    if session.state not in (SessionState.SENDER_CONFIRMED, SessionState.HANDSHAKE_COMPLETE):
        return web.json_response({
            "status": "error",
            "message": "Handshake not in correct state.",
        }, status=409)

    session.set_state(SessionState.HANDSHAKE_COMPLETE)
    log.info("Stage 3 complete: protocol handshake done — transfer can begin")

    # Signal UI to transition to transfer page
    import time
    session.start_time = time.time()
    
    # Restart the speed tracker timer so we don't count the handshake/idle waiting time!
    engine = request.app["transfer_engine"]
    engine.speed.start()

    session.set_state(SessionState.TRANSFERRING)

    return web.json_response({"status": "ok", "stage": 3})
