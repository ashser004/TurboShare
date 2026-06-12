"""
TurboShare — aiohttp server lifecycle manager.

Creates the aiohttp Application, wires up middleware, routes,
and shared state (session, transfer engine).  Starts and stops
the server on the qasync event loop.
"""

from __future__ import annotations

import asyncio
import logging

from aiohttp import web

from src.core.session import Session
from src.transfer.engine import TransferEngine
from src.server.routes import setup_routes
from src.server.middleware import (
    token_middleware,
    ip_lock_middleware,
    rate_limit_middleware,
)

log = logging.getLogger(__name__)


class TurboShareServer:
    """Manages the aiohttp web server lifecycle."""

    def __init__(self, session: Session, engine: TransferEngine) -> None:
        self.session = session
        self.engine = engine
        self._app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

    async def start(self) -> None:
        """Build and start the HTTPS server on the session's port."""
        self._app = web.Application(
            middlewares=[
                token_middleware,
                ip_lock_middleware,
                rate_limit_middleware,
            ]
        )

        # Shared state accessible in all handlers via request.app[...]
        self._app["session"] = self.session
        self._app["transfer_engine"] = self.engine

        setup_routes(self._app)

        self._runner = web.AppRunner(self._app)
        await self._runner.setup()

        self._site = web.TCPSite(
            self._runner,
            host="0.0.0.0",
            port=self.session.port,
            ssl_context=self.session.ssl_context,
        )
        await self._site.start()

        log.info(
            "HTTPS server started on port %d  (URL: %s)",
            self.session.port,
            self.session.session_url,
        )

    async def stop(self) -> None:
        """Gracefully shut down the server."""
        if self._site:
            await self._site.stop()
            self._site = None
        if self._runner:
            await self._runner.cleanup()
            self._runner = None
        self._app = None
        log.info("Server stopped")

    async def restart(self) -> None:
        """Stop and start with the current session (e.g. after regeneration)."""
        await self.stop()
        await self.start()

    @property
    def is_running(self) -> bool:
        return self._site is not None
