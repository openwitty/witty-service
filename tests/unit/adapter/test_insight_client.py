from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from witty_service.adapter.insight_client import InsightClient
from witty_service.domain.errors import DomainError


def _make_response(*, payload=None) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload if payload is not None else {"status": "ok"}
    return response


def _build_client(
    *,
    payload: Any = None,
    bearer_token: str | None = None,
    side_effect: Exception | None = None,
) -> tuple[InsightClient, MagicMock, MagicMock]:
    http_client = MagicMock()
    if side_effect is not None:
        http_client.request.side_effect = side_effect
    else:
        http_client.request.return_value = _make_response(payload=payload)

    with patch("witty_service.adapter.insight_client.httpx.Client") as client_class:
        client_class.return_value = http_client
        client = InsightClient(
            base_url="http://localhost:7396",
            timeout_seconds=5.0,
            bearer_token=bearer_token,
        )

    return client, http_client, client_class


def test_client_strips_trailing_slash() -> None:
    with patch("witty_service.adapter.insight_client.httpx.Client") as client_class:
        client_class.return_value = MagicMock()

        client = InsightClient(base_url="http://localhost:7396/", timeout_seconds=5.0)

    assert client.base_url == "http://localhost:7396"


def test_client_adds_bearer_header_when_configured() -> None:
    client, http_client, _ = _build_client(payload=[], bearer_token="secret-token")
    client.get_sessions({"limit": 10})
    http_client.request.assert_called_once_with(
        "GET",
        "/api/sessions",
        params={"limit": 10},
        json=None,
        headers={"Authorization": "Bearer secret-token"},
    )


@pytest.mark.parametrize(
    ("method_name", "args", "kwargs", "payload", "expected_method", "expected_path", "expected_params"),
    [
        (
            "get_health",
            (),
            {},
            {"status": "ok"},
            "GET",
            "/health",
            None,
        ),
        (
            "get_trace_detail",
            ("trace-1",),
            {},
            [{"id": 1, "trace_id": "trace-1"}],
            "GET",
            "/api/traces/trace-1",
            None,
        ),
        (
            "get_session_interruptions",
            ("runtime-session-1",),
            {},
            [],
            "GET",
            "/api/sessions/runtime-session-1/interruptions",
            None,
        ),
        (
            "resolve_interruption",
            ("interrupt-1",),
            {},
            {"status": "resolved"},
            "POST",
            "/api/interruptions/interrupt-1/resolve",
            None,
        ),
        (
            "delete_agent_health",
            (101,),
            {},
            {"ok": True},
            "DELETE",
            "/api/agent-health/101",
            None,
        ),
        (
            "export_atif_session",
            ("runtime-session-1",),
            {},
            {"schema_version": "1.6", "session_id": "runtime-session-1", "agent": {}, "steps": []},
            "GET",
            "/api/export/atif/session/runtime-session-1",
            None,
        ),
        (
            "get_timeseries",
            (),
            {"params": {"start_ns": 100, "end_ns": 200, "buckets": 5}},
            {"token_series": [], "model_series": []},
            "GET",
            "/api/timeseries",
            {"start_ns": 100, "end_ns": 200, "buckets": 5},
        ),
        (
            "get_interruption_count",
            (),
            {"params": {"start_ns": 100, "end_ns": 200}},
            {"total": 0, "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0}},
            "GET",
            "/api/interruptions/count",
            {"start_ns": 100, "end_ns": 200},
        ),
    ],
)
def test_client_calls_expected_endpoint(
    method_name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    payload: Any,
    expected_method: str,
    expected_path: str,
    expected_params: dict[str, Any] | None,
) -> None:
    client, http_client, client_class = _build_client(payload=payload)

    result = getattr(client, method_name)(*args, **kwargs)

    assert result == payload
    client_class.assert_called_once_with(base_url="http://localhost:7396", timeout=5.0)
    http_client.request.assert_called_once_with(
        expected_method,
        expected_path,
        params=expected_params,
        json=None,
        headers={},
    )


@pytest.mark.parametrize(
    ("side_effect", "expected_code"),
    [
        (httpx.ConnectError("boom"), "INSIGHT_UNAVAILABLE"),
        (httpx.ReadTimeout("slow"), "INSIGHT_TIMEOUT"),
    ],
)
def test_client_maps_transport_errors_to_domain_error(
    side_effect: Exception,
    expected_code: str,
) -> None:
    client, _, _ = _build_client(side_effect=side_effect)

    with pytest.raises(DomainError) as exc_info:
        client.get_health()

    assert exc_info.value.code == expected_code


def test_client_maps_http_error_to_domain_error() -> None:
    request = httpx.Request("GET", "http://localhost:7396/health")
    response = httpx.Response(503, request=request)
    mocked_response = _make_response()
    mocked_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "bad gateway",
        request=request,
        response=response,
    )

    client, http_client, _ = _build_client()
    http_client.request.return_value = mocked_response

    with pytest.raises(DomainError) as exc_info:
        client.get_health()

    assert exc_info.value.code == "INSIGHT_UPSTREAM_ERROR"
    assert exc_info.value.details["status_code"] == 503


def test_client_maps_bad_json_to_domain_error() -> None:
    mocked_response = _make_response()
    mocked_response.json.side_effect = ValueError("invalid json")

    client, http_client, _ = _build_client()
    http_client.request.return_value = mocked_response

    with pytest.raises(DomainError) as exc_info:
        client.get_health()

    assert exc_info.value.code == "INSIGHT_BAD_RESPONSE"
