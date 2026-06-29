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
