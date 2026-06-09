from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import websockets

from witty_service.adapter.exceptions import (
    AdaptorConnectionError,
    AdaptorConnectionTimeout,
    AdaptorSendFailed,
    AdaptorReceiveError,
)
from witty_service.adapter.websocket_protocol import InboundEvent, OutboundMessage

logger = logging.getLogger(__name__)


def _log_prefix(session_id: str | None = None, url: str | None = None) -> str:
    parts = []
    if session_id:
        parts.append(f"session_id={session_id}")
    if url:
        parts.append(f"url={url}")
    if parts:
        return f"[{', '.join(parts)}] "
    return ""


class WebSocketClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._ws: websockets.WebSocketClientProtocol | None = None
        self._connected: bool = False
        self._session_id: str | None = None
        self._url: str | None = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    def _build_url(self, session_id: str) -> str:
        return f"{self._base_url}/sessions/{session_id}/ws"

    async def connect(self, session_id: str) -> None:
        url = self._build_url(session_id)
        prefix = _log_prefix(session_id=session_id, url=url)
        try:
            self._ws = await websockets.connect(url, ping_interval=None)
            self._connected = True
            self._session_id = session_id
            self._url = url
            logger.info(f"{prefix}WebSocket connected: client_id=%s", id(self))
        except Exception as exc:
            logger.error(f"{prefix}WebSocket connection failed: %s", exc)
            raise AdaptorConnectionError(
                message=f"WebSocket connection failed: {url}",
                details={"url": url, "error": str(exc)},
            ) from exc

    async def disconnect(self) -> None:
        if self._ws:
            prefix = _log_prefix(session_id=self._session_id, url=self._url)
            logger.info(f"{prefix}WebSocket disconnect requested: client_id=%s", id(self))
            self._connected = False
            await self._ws.close()
            self._ws = None

    async def send(self, message: OutboundMessage) -> None:
        if not self._ws or not self._connected:
            prefix = _log_prefix(session_id=self._session_id, url=self._url)
            logger.warning(f"{prefix}Cannot send - WebSocket not connected")
            raise AdaptorSendFailed(
                message=f"Cannot send message - WebSocket not connected for session '{self._session_id}'",
                details={},
            )
        try:
            await self._ws.send(json.dumps(message))
        except Exception as exc:
            prefix = _log_prefix(session_id=self._session_id, url=self._url)
            logger.error(f"{prefix}Failed to send WebSocket message: %s", exc)
            raise AdaptorSendFailed(
                message="Failed to send WebSocket message",
                details={"error": str(exc)},
            ) from exc

    async def recv(self) -> AsyncIterator[InboundEvent]:
        if not self._ws or not self._connected:
            prefix = _log_prefix(session_id=self._session_id, url=self._url)
            logger.warning(f"{prefix}Cannot recv - WebSocket not connected")
            raise AdaptorReceiveError(
                message=f"Cannot receive - WebSocket not connected for session '{self._session_id}'",
                details={},
            )
        try:
            async for raw in self._ws:
                try:
                    data = json.loads(raw)
                    event_type = data.get("type", "")

                    if event_type == "client.error":
                        yield InboundEvent(
                            type=event_type,
                            session_id=data.get("session_id", ""),
                            runtime_type=data.get("runtime_type", "unknown"),
                            event_id=data.get("event_id", ""),
                            ts_ms=data.get("ts_ms", 0),
                            payload=data.get("payload", {}),
                        )
                    else:
                        yield InboundEvent(
                            type=data["type"],
                            session_id=data["session_id"],
                            runtime_type=data["runtime_type"],
                            event_id=data["event_id"],
                            ts_ms=data["ts_ms"],
                            payload=data.get("payload", {}),
                        )
                except (json.JSONDecodeError, KeyError) as exc:
                    prefix = _log_prefix(session_id=self._session_id, url=self._url)
                    logger.error(f"{prefix}Failed to parse WebSocket message: %s", exc)
                    raise AdaptorReceiveError(
                        message=f"Failed to parse WebSocket message: {exc}",
                        details={"error": str(exc), "raw": raw[:200]},
                    ) from exc
        except websockets.ConnectionClosed as exc:
            self._connected = False
            prefix = _log_prefix(session_id=self._session_id, url=self._url)
            code = getattr(exc, "code", None)
            reason = getattr(exc, "reason", None)
            logger.warning(f"{prefix}WebSocket connection closed: code=%s reason=%s", code, reason)
            raise AdaptorReceiveError(
                message=f"WebSocket connection closed unexpectedly for session '{self._session_id}'",
                details={
                    "code": code,
                    "reason": reason,
                    "session_id": self._session_id,
                    "url": self._url,
                },
            ) from exc
        except AdaptorReceiveError:
            raise
        except Exception as exc:
            prefix = _log_prefix(session_id=self._session_id, url=self._url)
            logger.exception(f"{prefix}WebSocket receive exception")
            raise AdaptorReceiveError(
                message="WebSocket receive failed",
                details={"error": str(exc)},
            ) from exc

    async def close(self) -> None:
        await self.disconnect()
