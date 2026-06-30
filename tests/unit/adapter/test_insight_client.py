from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from witty_service.adapter.insight_client import InsightClient
from witty_service.domain.errors import DomainError


def _make_response(*, payload=None) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload if payload is not None else {"status": "ok"}
    return response


def test_client_strips_trailing_slash() -> None:
    with patch("witty_service.adapter.insight_client.httpx.Client") as client_class:
        client_class.return_value = MagicMock()

        client = InsightClient(base_url="http://localhost:7396/", timeout_seconds=5.0)

    assert client.base_url == "http://localhost:7396"


def test_get_health_calls_health_endpoint() -> None:
    with patch("witty_service.adapter.insight_client.httpx.Client") as client_class:
        http_client = MagicMock()
        http_client.request.return_value = _make_response(payload={"status": "ok"})
        client_class.return_value = http_client

        client = InsightClient(base_url="http://localhost:7396", timeout_seconds=5.0)
        result = client.get_health()

    assert result == {"status": "ok"}
    client_class.assert_called_once_with(base_url="http://localhost:7396", timeout=5.0)
    http_client.request.assert_called_once_with(
        "GET",
        "/health",
        params=None,
        json=None,
        headers={},
    )


def test_client_adds_bearer_header_when_configured() -> None:
    with patch("witty_service.adapter.insight_client.httpx.Client") as client_class:
        http_client = MagicMock()
        http_client.request.return_value = _make_response(payload=[])
        client_class.return_value = http_client

        client = InsightClient(
            base_url="http://localhost:7396",
            timeout_seconds=5.0,
            bearer_token="secret-token",
        )
        client.get_sessions({"limit": 10})

    http_client.request.assert_called_once_with(
        "GET",
        "/api/sessions",
        params={"limit": 10},
        json=None,
        headers={"Authorization": "Bearer secret-token"},
    )


def test_get_session_interruptions_calls_expected_endpoint() -> None:
    with patch("witty_service.adapter.insight_client.httpx.Client") as client_class:
        http_client = MagicMock()
        http_client.request.return_value = _make_response(payload=[])
        client_class.return_value = http_client

        client = InsightClient(base_url="http://localhost:7396", timeout_seconds=5.0)
        client.get_session_interruptions("runtime-session-1")

    http_client.request.assert_called_once_with(
        "GET",
        "/api/sessions/runtime-session-1/interruptions",
        params=None,
        json=None,
        headers={},
    )


def test_get_conversation_interruptions_calls_expected_endpoint() -> None:
    with patch("witty_service.adapter.insight_client.httpx.Client") as client_class:
        http_client = MagicMock()
        http_client.request.return_value = _make_response(payload=[])
        client_class.return_value = http_client

        client = InsightClient(base_url="http://localhost:7396", timeout_seconds=5.0)
        client.get_conversation_interruptions("conversation-1")

    http_client.request.assert_called_once_with(
        "GET",
        "/api/conversations/conversation-1/interruptions",
        params=None,
        json=None,
        headers={},
    )


def test_resolve_interruption_posts_expected_endpoint() -> None:
    with patch("witty_service.adapter.insight_client.httpx.Client") as client_class:
        http_client = MagicMock()
        http_client.request.return_value = _make_response(payload={"status": "resolved"})
        client_class.return_value = http_client

        client = InsightClient(base_url="http://localhost:7396", timeout_seconds=5.0)
        result = client.resolve_interruption("interrupt-1")

    assert result == {"status": "resolved"}
    http_client.request.assert_called_once_with(
        "POST",
        "/api/interruptions/interrupt-1/resolve",
        params=None,
        json=None,
        headers={},
    )


def test_delete_agent_health_calls_expected_endpoint() -> None:
    with patch("witty_service.adapter.insight_client.httpx.Client") as client_class:
        http_client = MagicMock()
        http_client.request.return_value = _make_response(payload={"ok": True})
        client_class.return_value = http_client

        client = InsightClient(base_url="http://localhost:7396", timeout_seconds=5.0)
        result = client.delete_agent_health(101)

    assert result == {"ok": True}
    http_client.request.assert_called_once_with(
        "DELETE",
        "/api/agent-health/101",
        params=None,
        json=None,
        headers={},
    )


def test_restart_agent_health_posts_expected_endpoint() -> None:
    with patch("witty_service.adapter.insight_client.httpx.Client") as client_class:
        http_client = MagicMock()
        http_client.request.return_value = _make_response(
            payload={"ok": True, "new_pid": 202, "cmd": ["python", "agent.py"]}
        )
        client_class.return_value = http_client

        client = InsightClient(base_url="http://localhost:7396", timeout_seconds=5.0)
        result = client.restart_agent_health(101)

    assert result == {"ok": True, "new_pid": 202, "cmd": ["python", "agent.py"]}
    http_client.request.assert_called_once_with(
        "POST",
        "/api/agent-health/101/restart",
        params=None,
        json=None,
        headers={},
    )


def test_export_atif_session_calls_expected_endpoint() -> None:
    with patch("witty_service.adapter.insight_client.httpx.Client") as client_class:
        http_client = MagicMock()
        http_client.request.return_value = _make_response(
            payload={"schema_version": "1.6", "session_id": "runtime-session-1", "agent": {}, "steps": []}
        )
        client_class.return_value = http_client

        client = InsightClient(base_url="http://localhost:7396", timeout_seconds=5.0)
        result = client.export_atif_session("runtime-session-1")

    assert result["session_id"] == "runtime-session-1"
    http_client.request.assert_called_once_with(
        "GET",
        "/api/export/atif/session/runtime-session-1",
        params=None,
        json=None,
        headers={},
    )


def test_export_atif_conversation_calls_expected_endpoint() -> None:
    with patch("witty_service.adapter.insight_client.httpx.Client") as client_class:
        http_client = MagicMock()
        http_client.request.return_value = _make_response(
            payload={"schema_version": "1.6", "session_id": "conversation-1", "agent": {}, "steps": []}
        )
        client_class.return_value = http_client

        client = InsightClient(base_url="http://localhost:7396", timeout_seconds=5.0)
        result = client.export_atif_conversation("conversation-1")

    assert result["session_id"] == "conversation-1"
    http_client.request.assert_called_once_with(
        "GET",
        "/api/export/atif/conversation/conversation-1",
        params=None,
        json=None,
        headers={},
    )


def test_client_maps_connect_error_to_domain_error() -> None:
    with patch("witty_service.adapter.insight_client.httpx.Client") as client_class:
        http_client = MagicMock()
        http_client.request.side_effect = httpx.ConnectError("boom")
        client_class.return_value = http_client

        client = InsightClient(base_url="http://localhost:7396", timeout_seconds=5.0)

        with pytest.raises(DomainError) as exc_info:
            client.get_health()

    assert exc_info.value.code == "INSIGHT_UNAVAILABLE"


def test_client_maps_timeout_to_domain_error() -> None:
    with patch("witty_service.adapter.insight_client.httpx.Client") as client_class:
        http_client = MagicMock()
        http_client.request.side_effect = httpx.ReadTimeout("slow")
        client_class.return_value = http_client

        client = InsightClient(base_url="http://localhost:7396", timeout_seconds=5.0)

        with pytest.raises(DomainError) as exc_info:
            client.get_health()

    assert exc_info.value.code == "INSIGHT_TIMEOUT"


def test_client_maps_http_error_to_domain_error() -> None:
    request = httpx.Request("GET", "http://localhost:7396/health")
    response = httpx.Response(503, request=request)
    mocked_response = _make_response()
    mocked_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "bad gateway",
        request=request,
        response=response,
    )

    with patch("witty_service.adapter.insight_client.httpx.Client") as client_class:
        http_client = MagicMock()
        http_client.request.return_value = mocked_response
        client_class.return_value = http_client

        client = InsightClient(base_url="http://localhost:7396", timeout_seconds=5.0)

        with pytest.raises(DomainError) as exc_info:
            client.get_health()

    assert exc_info.value.code == "INSIGHT_UPSTREAM_ERROR"
    assert exc_info.value.details["status_code"] == 503


def test_client_maps_bad_json_to_domain_error() -> None:
    mocked_response = _make_response()
    mocked_response.json.side_effect = ValueError("invalid json")

    with patch("witty_service.adapter.insight_client.httpx.Client") as client_class:
        http_client = MagicMock()
        http_client.request.return_value = mocked_response
        client_class.return_value = http_client

        client = InsightClient(base_url="http://localhost:7396", timeout_seconds=5.0)

        with pytest.raises(DomainError) as exc_info:
            client.get_health()

    assert exc_info.value.code == "INSIGHT_BAD_RESPONSE"
