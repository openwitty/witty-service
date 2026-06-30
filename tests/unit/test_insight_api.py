from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from witty_service.domain.errors import DomainError
from witty_service.main import create_app


def _client_with_facade(monkeypatch, facade: MagicMock) -> TestClient:
    monkeypatch.setenv("AUTH_TOKEN", "test-token")
    services = MagicMock()
    services.get_insight_facade.return_value = facade
    services.repository = MagicMock()
    return TestClient(create_app(services=services))


def test_get_insight_capabilities_returns_probe_result(monkeypatch) -> None:
    facade = MagicMock()
    facade.get_capabilities.return_value = {
        "enabled": False,
        "reachable": False,
        "features": {
            "sessions": False,
            "timeseries": False,
            "interruptions": False,
            "health": False,
        },
    }
    client = _client_with_facade(monkeypatch, facade)

    resp = client.get(
        "/insight/capabilities",
        headers={"Authorization": "Bearer test-token"},
    )

    assert resp.status_code == 200
    assert resp.json() == {
        "enabled": False,
        "reachable": False,
        "features": {
            "sessions": False,
            "timeseries": False,
            "interruptions": False,
            "health": False,
        },
    }


def test_get_insight_sessions_passes_managed_filters(monkeypatch) -> None:
    facade = MagicMock()
    facade.list_sessions.return_value = [
        {
            "session_id": "session-1",
            "runtime_session_id": "runtime-1",
            "witty_agent_id": "agent-1",
            "witty_agent_name": "Alpha",
            "agent_name": "Alpha",
            "conversation_count": 1,
            "first_seen_ns": 100,
            "last_seen_ns": 200,
            "total_input_tokens": 10,
            "total_output_tokens": 5,
            "model": "gpt-4o",
        }
    ]
    client = _client_with_facade(monkeypatch, facade)

    resp = client.get(
        "/insight/sessions",
        headers={"Authorization": "Bearer test-token"},
        params={
            "witty_agent_id": "agent-1",
            "start_ns": 100,
            "end_ns": 200,
        },
    )

    assert resp.status_code == 200
    assert resp.json()[0]["session_id"] == "session-1"
    facade.list_sessions.assert_called_once_with(
        witty_agent_id="agent-1",
        start_ns=100,
        end_ns=200,
    )


def test_get_insight_timeseries_passes_buckets(monkeypatch) -> None:
    facade = MagicMock()
    facade.get_timeseries.return_value = {
        "token_series": [
            {
                "bucket_start_ns": 100,
                "input_tokens": 1,
                "output_tokens": 2,
                "total_tokens": 3,
            }
        ],
        "model_series": [
            {
                "bucket_start_ns": 100,
                "model": "gpt-4o",
                "total_tokens": 3,
            }
        ],
    }
    client = _client_with_facade(monkeypatch, facade)

    resp = client.get(
        "/insight/timeseries",
        headers={"Authorization": "Bearer test-token"},
        params={
            "witty_agent_id": "agent-1",
            "start_ns": 100,
            "end_ns": 200,
            "buckets": 5,
        },
    )

    assert resp.status_code == 200
    assert resp.json()["token_series"][0]["total_tokens"] == 3
    facade.get_timeseries.assert_called_once_with(
        witty_agent_id="agent-1",
        start_ns=100,
        end_ns=200,
        buckets=5,
    )


def test_get_session_traces_passes_path_and_query_params(monkeypatch) -> None:
    facade = MagicMock()
    facade.get_session_traces.return_value = [
        {
            "trace_id": "trace-1",
            "conversation_id": "conv-1",
            "call_count": 2,
            "total_input_tokens": 10,
            "total_output_tokens": 5,
            "start_ns": 100,
            "end_ns": 200,
            "model": "gpt-4o",
            "user_query": "hello",
        }
    ]
    client = _client_with_facade(monkeypatch, facade)

    resp = client.get(
        "/insight/sessions/session-1/traces",
        headers={"Authorization": "Bearer test-token"},
        params={"start_ns": 100, "end_ns": 200},
    )

    assert resp.status_code == 200
    assert resp.json()[0]["trace_id"] == "trace-1"
    facade.get_session_traces.assert_called_once_with(
        "session-1",
        start_ns=100,
        end_ns=200,
    )


def test_get_trace_detail_returns_list_payload(monkeypatch) -> None:
    facade = MagicMock()
    facade.get_trace_detail.return_value = [
        {
            "id": 1,
            "call_id": "call-1",
            "start_timestamp_ns": 100,
            "end_timestamp_ns": 200,
            "model": "gpt-4o",
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
            "input_messages": "in",
            "output_messages": "out",
            "system_instructions": "sys",
            "agent_name": "Alpha",
            "process_name": "openclaw",
            "pid": 123,
            "user_query": "hello",
            "event_json": "{}",
            "trace_id": "trace-1",
            "conversation_id": "conv-1",
            "cache_read_tokens": 0,
            "status": "ok",
            "interruption_type": None,
        }
    ]
    client = _client_with_facade(monkeypatch, facade)

    resp = client.get(
        "/insight/traces/trace-1",
        headers={"Authorization": "Bearer test-token"},
    )

    assert resp.status_code == 200
    assert resp.json()[0]["id"] == 1
    facade.get_trace_detail.assert_called_once_with("trace-1")


def test_get_session_interruptions_returns_record_list(monkeypatch) -> None:
    facade = MagicMock()
    facade.get_session_interruptions.return_value = [
        {
            "id": 1,
            "interruption_id": "interrupt-1",
            "session_id": "session-1",
            "runtime_session_id": "runtime-1",
            "trace_id": "trace-1",
            "conversation_id": "conv-1",
            "call_id": "call-1",
            "pid": 123,
            "agent_name": "Alpha",
            "interruption_type": "agent_crash",
            "severity": "critical",
            "occurred_at_ns": 100,
            "detail": "crashed",
            "resolved": False,
        }
    ]
    client = _client_with_facade(monkeypatch, facade)

    resp = client.get(
        "/insight/sessions/session-1/interruptions",
        headers={"Authorization": "Bearer test-token"},
    )

    assert resp.status_code == 200
    assert resp.json()[0]["runtime_session_id"] == "runtime-1"
    facade.get_session_interruptions.assert_called_once_with("session-1")


def test_get_conversation_interruptions_returns_record_list(monkeypatch) -> None:
    facade = MagicMock()
    facade.get_conversation_interruptions.return_value = [
        {
            "id": 1,
            "interruption_id": "interrupt-1",
            "session_id": "session-1",
            "runtime_session_id": "runtime-1",
            "trace_id": "trace-1",
            "conversation_id": "conv-1",
            "call_id": "call-1",
            "pid": 123,
            "agent_name": "Alpha",
            "interruption_type": "agent_crash",
            "severity": "critical",
            "occurred_at_ns": 100,
            "detail": "crashed",
            "resolved": False,
        }
    ]
    client = _client_with_facade(monkeypatch, facade)

    resp = client.get(
        "/insight/conversations/conv-1/interruptions",
        headers={"Authorization": "Bearer test-token"},
    )

    assert resp.status_code == 200
    assert resp.json()[0]["conversation_id"] == "conv-1"
    facade.get_conversation_interruptions.assert_called_once_with("conv-1")


def test_resolve_interruption_returns_action_payload(monkeypatch) -> None:
    facade = MagicMock()
    facade.resolve_interruption.return_value = {"status": "resolved"}
    client = _client_with_facade(monkeypatch, facade)

    resp = client.post(
        "/insight/interruptions/interrupt-1/resolve",
        headers={"Authorization": "Bearer test-token"},
    )

    assert resp.status_code == 200
    assert resp.json() == {"status": "resolved"}
    facade.resolve_interruption.assert_called_once_with("interrupt-1")


def test_get_interruption_session_counts_returns_schema_shape(monkeypatch) -> None:
    facade = MagicMock()
    facade.get_interruption_session_counts.return_value = [
        {
            "session_id": "session-1",
            "runtime_session_id": "runtime-1",
            "total": 2,
            "by_severity": {"critical": 1, "high": 1, "medium": 0, "low": 0},
            "types": [
                {
                    "interruption_type": "agent_crash",
                    "severity": "critical",
                    "count": 1,
                }
            ],
        }
    ]
    client = _client_with_facade(monkeypatch, facade)

    resp = client.get(
        "/insight/interruptions/session-counts",
        headers={"Authorization": "Bearer test-token"},
    )

    assert resp.status_code == 200
    assert resp.json() == [
        {
            "session_id": "session-1",
            "runtime_session_id": "runtime-1",
            "total": 2,
            "by_severity": {"critical": 1, "high": 1, "medium": 0, "low": 0},
            "types": [
                {
                    "interruption_type": "agent_crash",
                    "severity": "critical",
                    "count": 1,
                }
            ],
        }
    ]


def test_get_interruption_count_returns_count_payload(monkeypatch) -> None:
    facade = MagicMock()
    facade.get_interruption_count.return_value = {
        "total": 2,
        "by_severity": {"critical": 1, "high": 1, "medium": 0, "low": 0},
    }
    client = _client_with_facade(monkeypatch, facade)

    resp = client.get(
        "/insight/interruptions/count",
        headers={"Authorization": "Bearer test-token"},
        params={"witty_agent_id": "agent-1", "start_ns": 100, "end_ns": 200},
    )

    assert resp.status_code == 200
    assert resp.json()["total"] == 2
    facade.get_interruption_count.assert_called_once_with(
        witty_agent_id="agent-1",
        start_ns=100,
        end_ns=200,
    )


def test_get_agent_health_returns_managed_and_orphan_runtimes(monkeypatch) -> None:
    facade = MagicMock()
    facade.get_agent_health.return_value = {
        "agents": [
            {
                "witty_agent_id": "agent-1",
                "witty_agent_name": "Alpha",
                "witty_status": "running",
                "overall_status": "healthy",
                "status_reason": None,
                "adapter_type": "http",
                "sandbox_type": "local_process",
                "workspace_path": "/tmp/agent-1",
                "gateway_port": 18080,
                "adapter_base_url": "http://127.0.0.1:18080",
                "adapter_ready": True,
                "adapter_status": "ready",
                "adapter_latency_ms": 12,
                "adapter_error_message": None,
                "adapter_pid": 101,
                "stderr_log_path": "/tmp/alpha.err",
                "runtime": {
                    "pid": 101,
                    "agent_name": "raw-alpha",
                    "category": "openclaw",
                    "exe_path": "/usr/bin/openclaw",
                    "ports": [18080],
                    "status": "healthy",
                    "last_check_time": 111,
                    "latency_ms": 12,
                    "error_message": None,
                },
                "candidate_runtimes": [],
            }
        ],
        "orphan_runtimes": [
            {
                "pid": 202,
                "agent_name": "orphan-runtime",
                "category": "openclaw",
                "exe_path": "/usr/bin/openclaw",
                "ports": [19999],
                "status": "offline",
                "last_check_time": 222,
                "latency_ms": None,
                "error_message": "exited",
            }
        ],
        "last_scan_time": 999,
    }
    client = _client_with_facade(monkeypatch, facade)

    resp = client.get(
        "/insight/agent-health",
        headers={"Authorization": "Bearer test-token"},
    )

    assert resp.status_code == 200
    assert resp.json()["last_scan_time"] == 999
    assert resp.json()["orphan_runtimes"][0]["pid"] == 202


def test_delete_agent_health_returns_action_payload(monkeypatch) -> None:
    facade = MagicMock()
    facade.delete_agent_health.return_value = {"ok": True}
    client = _client_with_facade(monkeypatch, facade)

    resp = client.delete(
        "/insight/agent-health/101",
        headers={"Authorization": "Bearer test-token"},
    )

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    facade.delete_agent_health.assert_called_once_with(101)


def test_restart_agent_health_returns_restart_payload(monkeypatch) -> None:
    facade = MagicMock()
    facade.restart_agent_health.return_value = {
        "ok": True,
        "new_pid": 202,
        "cmd": ["python", "agent.py"],
    }
    client = _client_with_facade(monkeypatch, facade)

    resp = client.post(
        "/insight/agent-health/101/restart",
        headers={"Authorization": "Bearer test-token"},
    )

    assert resp.status_code == 200
    assert resp.json()["new_pid"] == 202
    facade.restart_agent_health.assert_called_once_with(101)


def test_export_atif_session_returns_document(monkeypatch) -> None:
    facade = MagicMock()
    facade.export_atif_session.return_value = {
        "schema_version": "1.6",
        "session_id": "session-1",
        "runtime_session_id": "runtime-1",
        "agent": {"name": "Alpha", "version": "test"},
        "steps": [{"step_id": 1, "source": "user", "message": "hello"}],
    }
    client = _client_with_facade(monkeypatch, facade)

    resp = client.get(
        "/insight/export/atif/session/session-1",
        headers={"Authorization": "Bearer test-token"},
    )

    assert resp.status_code == 200
    assert resp.json()["runtime_session_id"] == "runtime-1"
    facade.export_atif_session.assert_called_once_with("session-1")


def test_export_atif_conversation_returns_document(monkeypatch) -> None:
    facade = MagicMock()
    facade.export_atif_conversation.return_value = {
        "schema_version": "1.6",
        "session_id": "conv-1",
        "agent": {"name": "Alpha", "version": "test"},
        "steps": [{"step_id": 1, "source": "user", "message": "hello"}],
    }
    client = _client_with_facade(monkeypatch, facade)

    resp = client.get(
        "/insight/export/atif/conversation/conv-1",
        headers={"Authorization": "Bearer test-token"},
    )

    assert resp.status_code == 200
    assert resp.json()["session_id"] == "conv-1"
    facade.export_atif_conversation.assert_called_once_with("conv-1")


def test_domain_error_is_returned_in_standard_error_shape(monkeypatch) -> None:
    facade = MagicMock()
    facade.get_session_traces.side_effect = DomainError(
        code="INSIGHT_SESSION_MAPPING_NOT_FOUND",
        message="witty session is not mapped to a runtime insight session",
        status_code=404,
        details={"session_id": "missing"},
    )
    client = _client_with_facade(monkeypatch, facade)

    resp = client.get(
        "/insight/sessions/missing/traces",
        headers={"Authorization": "Bearer test-token"},
    )

    assert resp.status_code == 404
    assert resp.json() == {
        "error": {
            "code": "INSIGHT_SESSION_MAPPING_NOT_FOUND",
            "message": "witty session is not mapped to a runtime insight session",
            "details": {"session_id": "missing"},
        }
    }
