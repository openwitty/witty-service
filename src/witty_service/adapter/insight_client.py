from __future__ import annotations

from typing import Any

import httpx

from witty_service.domain.errors import (
    insight_bad_response,
    insight_timeout,
    insight_unavailable,
    insight_upstream_error,
)


class InsightClient:
    """HTTP client for raw witty-insight API calls."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        bearer_token: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.bearer_token = bearer_token
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout_seconds)

    def close(self) -> None:
        self._client.close()

    def _headers(self) -> dict[str, str]:
        if not self.bearer_token:
            return {}
        return {"Authorization": f"Bearer {self.bearer_token}"}

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        try:
            response = self._client.request(
                method,
                path,
                params=params,
                json=json,
                headers=self._headers(),
            )
        except httpx.ConnectError as exc:
            raise insight_unavailable(
                base_url=self.base_url,
                path=path,
                reason=str(exc),
            ) from exc
        except httpx.TimeoutException as exc:
            raise insight_timeout(
                base_url=self.base_url,
                path=path,
                timeout_seconds=self.timeout_seconds,
            ) from exc

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise insight_upstream_error(
                base_url=self.base_url,
                path=path,
                status_code=exc.response.status_code,
                response_text=exc.response.text,
            ) from exc

        try:
            return response.json()
        except ValueError as exc:
            raise insight_bad_response(
                base_url=self.base_url,
                path=path,
                reason=str(exc),
            ) from exc

    def get_health(self) -> Any:
        return self._request_json("GET", "/health")

    def get_sessions(self, params: dict[str, Any] | None = None) -> Any:
        return self._request_json("GET", "/api/sessions", params=params)

    def get_session_traces(self, session_id: str, params: dict[str, Any] | None = None) -> Any:
        return self._request_json("GET", f"/api/sessions/{session_id}/traces", params=params)

    def get_trace_detail(self, trace_id: str) -> Any:
        return self._request_json("GET", f"/api/traces/{trace_id}")

    def get_conversation_detail(self, conversation_id: str) -> Any:
        return self._request_json("GET", f"/api/conversations/{conversation_id}")

    def get_timeseries(self, params: dict[str, Any] | None = None) -> Any:
        return self._request_json("GET", "/api/timeseries", params=params)

    def get_agent_health(self) -> Any:
        return self._request_json("GET", "/api/agent-health")

    def delete_agent_health(self, pid: int) -> Any:
        return self._request_json("DELETE", f"/api/agent-health/{pid}")

    def restart_agent_health(self, pid: int) -> Any:
        return self._request_json("POST", f"/api/agent-health/{pid}/restart")

    def get_interruption_count(self, params: dict[str, Any] | None = None) -> Any:
        return self._request_json("GET", "/api/interruptions/count", params=params)

    def get_interruption_stats(self, params: dict[str, Any] | None = None) -> Any:
        return self._request_json("GET", "/api/interruptions/stats", params=params)

    def get_interruption_session_counts(self, params: dict[str, Any] | None = None) -> Any:
        return self._request_json("GET", "/api/interruptions/session-counts", params=params)

    def get_interruption_conversation_counts(
        self,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return self._request_json("GET", "/api/interruptions/conversation-counts", params=params)

    def get_session_interruptions(self, session_id: str) -> Any:
        return self._request_json("GET", f"/api/sessions/{session_id}/interruptions")

    def get_conversation_interruptions(self, conversation_id: str) -> Any:
        return self._request_json("GET", f"/api/conversations/{conversation_id}/interruptions")

    def resolve_interruption(self, interruption_id: str) -> Any:
        return self._request_json("POST", f"/api/interruptions/{interruption_id}/resolve")

    def export_atif_session(self, session_id: str) -> Any:
        return self._request_json("GET", f"/api/export/atif/session/{session_id}")

    def export_atif_conversation(self, conversation_id: str) -> Any:
        return self._request_json("GET", f"/api/export/atif/conversation/{conversation_id}")
