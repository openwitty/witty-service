from __future__ import annotations

import json
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.main import create_app


def test_send_message_stream_returns_sse_events(monkeypatch):
    monkeypatch.setenv("AUTH_TOKEN", "test-token")

    async def event_stream():
        yield {
            "sandbox_type": "local_process",
            "event": {
                "type": "message.delta",
                "session_id": "session-1",
                "runtime_type": "openclaw",
                "event_id": "evt-1",
                "ts_ms": 123,
                "payload": {"delta": "hello"},
            },
        }
        yield {
            "sandbox_type": "local_process",
            "event": {
                "type": "message.completed",
                "session_id": "session-1",
                "runtime_type": "openclaw",
                "event_id": "evt-2",
                "ts_ms": 456,
                "payload": {},
            },
        }

    manager = MagicMock()
    manager.send_message_stream.return_value = event_stream()

    services = MagicMock()
    services.get_agent_manager_for_agent.return_value = manager

    client = TestClient(create_app(services=services))

    with client.stream(
        "POST",
        "/api/v1/agents/agent-1/sessions/session-1/messages/stream",
        headers={"Authorization": "Bearer test-token"},
        json={"content": "hello"},
    ) as resp:
        body = b"".join(resp.iter_bytes())

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    assert body.decode("utf-8").splitlines() == [
        "data: "
        + json.dumps(
            {
                "sandbox_type": "local_process",
                "event": {
                    "type": "message.delta",
                    "session_id": "session-1",
                    "runtime_type": "openclaw",
                    "event_id": "evt-1",
                    "ts_ms": 123,
                    "payload": {"delta": "hello"},
                },
            }
        ),
        "",
        "data: "
        + json.dumps(
            {
                "sandbox_type": "local_process",
                "event": {
                    "type": "message.completed",
                    "session_id": "session-1",
                    "runtime_type": "openclaw",
                    "event_id": "evt-2",
                    "ts_ms": 456,
                    "payload": {},
                },
            }
        ),
        "",
    ]
    manager.send_message_stream.assert_called_once_with(
        agent_id="agent-1",
        session_id="session-1",
        content="hello",
    )


def test_send_message_stream_reuses_send_message_request_validation(monkeypatch):
    monkeypatch.setenv("AUTH_TOKEN", "test-token")

    services = MagicMock()
    client = TestClient(create_app(services=services))

    resp = client.post(
        "/api/v1/agents/agent-1/sessions/session-1/messages/stream",
        headers={"Authorization": "Bearer test-token"},
        json={"content": ""},
    )

    assert resp.status_code == 422
    services.get_agent_manager_for_agent.assert_not_called()
