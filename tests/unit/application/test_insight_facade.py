from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from witty_service.api.services import ServiceContainer
from witty_service.domain.enums import AgentStatus
from witty_service.domain.errors import DomainError, insight_unavailable
from witty_service.persistence.db import create_session_factory, create_sqlite_engine, init_db
from witty_service.persistence.repositories import SqliteRepository


@pytest.fixture()
def repo() -> SqliteRepository:
    engine = create_sqlite_engine("sqlite:///:memory:")
    init_db(engine)
    factory = create_session_factory(engine)
    try:
        yield SqliteRepository(factory)
    finally:
        engine.dispose()


def _create_agent(repo: SqliteRepository, agent_id: str, name: str) -> None:
    repo.create_agent_with_id(
        agent_id=agent_id,
        name=name,
        description=f"{name} description",
        sandbox_type="local_process",
        adapter_type="http",
        workspace_path=f"/tmp/{agent_id}",
        idle_timeout_seconds=300,
        status=AgentStatus.running,
    )


def _create_session(
    repo: SqliteRepository,
    *,
    agent_id: str,
    session_id: str,
    runtime_session_id: str | None = None,
) -> None:
    repo.upsert_session(
        session_id=session_id,
        agent_id=agent_id,
        status="idle",
        runtime_type="openclaw",
        runtime_session_key=f"agent:{agent_id}:session:{session_id}",
        remote_runtime_agent_id=f"runtime-agent:{agent_id}",
    )
    if runtime_session_id is not None:
        repo.update_session_runtime_identity(
            session_id=session_id,
            runtime_type="openclaw",
            runtime_session_id=runtime_session_id,
            runtime_session_key=f"agent:{agent_id}:session:{session_id}",
        )


class FakeInsightClient:
    def __init__(self) -> None:
        self.health_result: Any = {"ok": True}
        self.sessions_result: Any = []
        self.session_traces_result: Any = []
        self.session_interruptions_result: Any = []
        self.conversation_interruptions_result: Any = []
        self.timeseries_result: Any = {"token_series": [], "model_series": []}
        self.interruption_count_result: Any = {
            "total": 0,
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        }
        self.interruption_stats_result: Any = []
        self.interruption_session_counts_result: Any = []
        self.interruption_conversation_counts_result: Any = []
        self.agent_health_result: Any = {"agents": [], "last_scan_time": 0}
        self.trace_detail_result: Any = []
        self.conversation_detail_result: Any = []
        self.resolve_interruption_result: Any = {"status": "resolved"}
        self.delete_agent_health_result: Any = {"ok": True}
        self.restart_agent_health_result: Any = {"ok": True, "new_pid": 0, "cmd": []}
        self.export_atif_session_result: Any = {
            "schema_version": "1.6",
            "session_id": "runtime-session-1",
            "agent": {},
            "steps": [],
        }
        self.export_atif_conversation_result: Any = {
            "schema_version": "1.6",
            "session_id": "conversation-1",
            "agent": {},
            "steps": [],
        }
        self.health_error: Exception | None = None
        self.calls: list[tuple[str, Any]] = []

    def get_health(self) -> Any:
        self.calls.append(("get_health", None))
        if self.health_error is not None:
            raise self.health_error
        return self.health_result

    def get_sessions(self, params: dict[str, Any] | None = None) -> Any:
        self.calls.append(("get_sessions", params))
        return self.sessions_result

    def get_session_traces(self, session_id: str, params: dict[str, Any] | None = None) -> Any:
        self.calls.append(("get_session_traces", {"session_id": session_id, "params": params}))
        return self.session_traces_result

    def get_session_interruptions(self, session_id: str) -> Any:
        self.calls.append(("get_session_interruptions", session_id))
        return self.session_interruptions_result

    def get_conversation_interruptions(self, conversation_id: str) -> Any:
        self.calls.append(("get_conversation_interruptions", conversation_id))
        return self.conversation_interruptions_result

    def get_trace_detail(self, trace_id: str) -> Any:
        self.calls.append(("get_trace_detail", trace_id))
        return self.trace_detail_result

    def get_conversation_detail(self, conversation_id: str) -> Any:
        self.calls.append(("get_conversation_detail", conversation_id))
        return self.conversation_detail_result

    def resolve_interruption(self, interruption_id: str) -> Any:
        self.calls.append(("resolve_interruption", interruption_id))
        return self.resolve_interruption_result

    def delete_agent_health(self, pid: int) -> Any:
        self.calls.append(("delete_agent_health", pid))
        return self.delete_agent_health_result

    def restart_agent_health(self, pid: int) -> Any:
        self.calls.append(("restart_agent_health", pid))
        return self.restart_agent_health_result

    def export_atif_session(self, session_id: str) -> Any:
        self.calls.append(("export_atif_session", session_id))
        return self.export_atif_session_result

    def export_atif_conversation(self, conversation_id: str) -> Any:
        self.calls.append(("export_atif_conversation", conversation_id))
        return self.export_atif_conversation_result

    def get_timeseries(self, params: dict[str, Any] | None = None) -> Any:
        self.calls.append(("get_timeseries", params))
        return self.timeseries_result

    def get_interruption_count(self, params: dict[str, Any] | None = None) -> Any:
        self.calls.append(("get_interruption_count", params))
        return self.interruption_count_result

    def get_interruption_stats(self, params: dict[str, Any] | None = None) -> Any:
        self.calls.append(("get_interruption_stats", params))
        return self.interruption_stats_result

    def get_interruption_session_counts(self, params: dict[str, Any] | None = None) -> Any:
        self.calls.append(("get_interruption_session_counts", params))
        return self.interruption_session_counts_result

    def get_interruption_conversation_counts(
        self,
        params: dict[str, Any] | None = None,
    ) -> Any:
        self.calls.append(("get_interruption_conversation_counts", params))
        return self.interruption_conversation_counts_result

    def get_agent_health(self) -> Any:
        self.calls.append(("get_agent_health", None))
        return self.agent_health_result


def test_get_capabilities_reports_disabled_without_upstream(repo: SqliteRepository) -> None:
    from witty_service.application.insight_facade import InsightFacade

    facade = InsightFacade(
        ServiceContainer(repository=repo, workspace_store=MagicMock()),
    )

    assert facade.get_capabilities() == {
        "enabled": False,
        "reachable": False,
        "features": {
            "sessions": False,
            "timeseries": False,
            "interruptions": False,
            "health": False,
        },
    }


def test_get_capabilities_reports_unreachable_when_health_probe_fails(
    repo: SqliteRepository,
) -> None:
    from witty_service.application.insight_facade import InsightFacade

    insight_client = FakeInsightClient()
    insight_client.health_error = insight_unavailable(
        base_url="http://127.0.0.1:7396",
        path="/health",
        reason="connection refused",
    )
    facade = InsightFacade(
        ServiceContainer(
            repository=repo,
            workspace_store=MagicMock(),
            insight_client=insight_client,
        ),
    )

    assert facade.get_capabilities() == {
        "enabled": True,
        "reachable": False,
        "features": {
            "sessions": True,
            "timeseries": True,
            "interruptions": True,
            "health": True,
        },
    }


def test_list_witty_agents_reads_managed_agents_from_repository(repo: SqliteRepository) -> None:
    from witty_service.application.insight_facade import InsightFacade

    _create_agent(repo, "agent-1", "Alpha")
    _create_agent(repo, "agent-2", "Beta")
    facade = InsightFacade(
        ServiceContainer(repository=repo, workspace_store=MagicMock()),
    )

    result = facade.list_witty_agents()

    assert result == [
        {
            "witty_agent_id": "agent-1",
            "witty_agent_name": "Alpha",
            "status": "running",
        },
        {
            "witty_agent_id": "agent-2",
            "witty_agent_name": "Beta",
            "status": "running",
        },
    ]


def test_list_sessions_filters_to_all_managed_runtime_sessions_and_enriches(
    repo: SqliteRepository,
) -> None:
    from witty_service.application.insight_facade import InsightFacade

    _create_agent(repo, "agent-1", "Alpha")
    _create_agent(repo, "agent-2", "Beta")
    _create_session(repo, agent_id="agent-1", session_id="session-1", runtime_session_id="runtime-1")
    _create_session(repo, agent_id="agent-2", session_id="session-2", runtime_session_id="runtime-2")

    insight_client = FakeInsightClient()
    insight_client.sessions_result = [
        {
            "session_id": "runtime-1",
            "conversation_count": 3,
            "first_seen_ns": 100,
            "last_seen_ns": 300,
            "total_input_tokens": 11,
            "total_output_tokens": 7,
            "model": "gpt-4o",
            "agent_name": "raw-alpha",
        },
        {
            "session_id": "runtime-2",
            "conversation_count": 2,
            "first_seen_ns": 200,
            "last_seen_ns": 400,
            "total_input_tokens": 5,
            "total_output_tokens": 6,
            "model": "gpt-4o-mini",
            "agent_name": "raw-beta",
        },
    ]
    facade = InsightFacade(
        ServiceContainer(
            repository=repo,
            workspace_store=MagicMock(),
            insight_client=insight_client,
        ),
    )

    result = facade.list_sessions()

    assert insight_client.calls[-1] == (
        "get_sessions",
        {"session_ids": ["runtime-1", "runtime-2"]},
    )
    assert result == [
        {
            "session_id": "session-1",
            "runtime_session_id": "runtime-1",
            "witty_agent_id": "agent-1",
            "witty_agent_name": "Alpha",
            "agent_name": "Alpha",
            "conversation_count": 3,
            "first_seen_ns": 100,
            "last_seen_ns": 300,
            "total_input_tokens": 11,
            "total_output_tokens": 7,
            "model": "gpt-4o",
        },
        {
            "session_id": "session-2",
            "runtime_session_id": "runtime-2",
            "witty_agent_id": "agent-2",
            "witty_agent_name": "Beta",
            "agent_name": "Beta",
            "conversation_count": 2,
            "first_seen_ns": 200,
            "last_seen_ns": 400,
            "total_input_tokens": 5,
            "total_output_tokens": 6,
            "model": "gpt-4o-mini",
        },
    ]


def test_get_session_traces_uses_witty_session_runtime_mapping(repo: SqliteRepository) -> None:
    from witty_service.application.insight_facade import InsightFacade

    _create_agent(repo, "agent-1", "Alpha")
    _create_session(repo, agent_id="agent-1", session_id="session-1", runtime_session_id="runtime-1")
    insight_client = FakeInsightClient()
    insight_client.session_traces_result = [{"trace_id": "trace-1"}]
    facade = InsightFacade(
        ServiceContainer(
            repository=repo,
            workspace_store=MagicMock(),
            insight_client=insight_client,
        ),
    )

    result = facade.get_session_traces("session-1", start_ns=10, end_ns=20)

    assert insight_client.calls[-1] == (
        "get_session_traces",
        {"session_id": "runtime-1", "params": {"start_ns": 10, "end_ns": 20}},
    )
    assert result == [{"trace_id": "trace-1"}]


def test_get_session_traces_raises_when_runtime_mapping_is_missing(
    repo: SqliteRepository,
) -> None:
    from witty_service.application.insight_facade import InsightFacade

    _create_agent(repo, "agent-1", "Alpha")
    _create_session(repo, agent_id="agent-1", session_id="session-1")
    facade = InsightFacade(
        ServiceContainer(
            repository=repo,
            workspace_store=MagicMock(),
            insight_client=FakeInsightClient(),
        ),
    )

    with pytest.raises(DomainError) as exc_info:
        facade.get_session_traces("session-1")

    assert exc_info.value.code == "INSIGHT_SESSION_MAPPING_NOT_FOUND"


def test_get_session_interruptions_uses_mapping_and_remaps_session_identity(
    repo: SqliteRepository,
) -> None:
    from witty_service.application.insight_facade import InsightFacade

    _create_agent(repo, "agent-1", "Alpha")
    _create_session(repo, agent_id="agent-1", session_id="session-1", runtime_session_id="runtime-1")
    insight_client = FakeInsightClient()
    insight_client.session_interruptions_result = [
        {
            "id": 1,
            "interruption_id": "interrupt-1",
            "session_id": "runtime-1",
            "trace_id": "trace-1",
            "conversation_id": "conv-1",
            "call_id": "call-1",
            "pid": 123,
            "agent_name": "raw-alpha",
            "interruption_type": "agent_crash",
            "severity": "critical",
            "occurred_at_ns": 100,
            "detail": "crashed",
            "resolved": False,
        }
    ]
    facade = InsightFacade(
        ServiceContainer(
            repository=repo,
            workspace_store=MagicMock(),
            insight_client=insight_client,
        ),
    )

    result = facade.get_session_interruptions("session-1")

    assert insight_client.calls[-1] == ("get_session_interruptions", "runtime-1")
    assert result[0]["session_id"] == "session-1"
    assert result[0]["runtime_session_id"] == "runtime-1"


def test_get_conversation_interruptions_remaps_managed_runtime_session_ids(
    repo: SqliteRepository,
) -> None:
    from witty_service.application.insight_facade import InsightFacade

    _create_agent(repo, "agent-1", "Alpha")
    _create_session(repo, agent_id="agent-1", session_id="session-1", runtime_session_id="runtime-1")
    insight_client = FakeInsightClient()
    insight_client.conversation_interruptions_result = [
        {
            "id": 1,
            "interruption_id": "interrupt-1",
            "session_id": "runtime-1",
            "trace_id": "trace-1",
            "conversation_id": "conv-1",
            "call_id": "call-1",
            "pid": 123,
            "agent_name": "raw-alpha",
            "interruption_type": "agent_crash",
            "severity": "critical",
            "occurred_at_ns": 100,
            "detail": "crashed",
            "resolved": False,
        }
    ]
    facade = InsightFacade(
        ServiceContainer(
            repository=repo,
            workspace_store=MagicMock(),
            insight_client=insight_client,
        ),
    )

    result = facade.get_conversation_interruptions("conv-1")

    assert insight_client.calls[-1] == ("get_conversation_interruptions", "conv-1")
    assert result[0]["session_id"] == "session-1"
    assert result[0]["runtime_session_id"] == "runtime-1"


def test_export_atif_session_uses_mapping_and_rewrites_session_id(
    repo: SqliteRepository,
) -> None:
    from witty_service.application.insight_facade import InsightFacade

    _create_agent(repo, "agent-1", "Alpha")
    _create_session(repo, agent_id="agent-1", session_id="session-1", runtime_session_id="runtime-1")
    insight_client = FakeInsightClient()
    insight_client.export_atif_session_result = {
        "schema_version": "1.6",
        "session_id": "runtime-1",
        "agent": {"name": "Alpha", "version": "test"},
        "steps": [],
    }
    facade = InsightFacade(
        ServiceContainer(
            repository=repo,
            workspace_store=MagicMock(),
            insight_client=insight_client,
        ),
    )

    result = facade.export_atif_session("session-1")

    assert insight_client.calls[-1] == ("export_atif_session", "runtime-1")
    assert result["session_id"] == "session-1"
    assert result["runtime_session_id"] == "runtime-1"


def test_get_timeseries_filters_to_selected_managed_agent_sessions(
    repo: SqliteRepository,
) -> None:
    from witty_service.application.insight_facade import InsightFacade

    _create_agent(repo, "agent-1", "Alpha")
    _create_agent(repo, "agent-2", "Beta")
    _create_session(repo, agent_id="agent-1", session_id="session-1", runtime_session_id="runtime-1")
    _create_session(repo, agent_id="agent-2", session_id="session-2", runtime_session_id="runtime-2")

    insight_client = FakeInsightClient()
    insight_client.timeseries_result = {
        "token_series": [{"bucket_start_ns": 100, "input_tokens": 1, "output_tokens": 2, "total_tokens": 3}],
        "model_series": [{"bucket_start_ns": 100, "model": "gpt-4o", "total_tokens": 3}],
    }
    facade = InsightFacade(
        ServiceContainer(
            repository=repo,
            workspace_store=MagicMock(),
            insight_client=insight_client,
        ),
    )

    result = facade.get_timeseries(witty_agent_id="agent-1", start_ns=10, end_ns=20, buckets=5)

    assert insight_client.calls[-1] == (
        "get_timeseries",
        {
            "start_ns": 10,
            "end_ns": 20,
            "buckets": 5,
            "session_id": "runtime-1",
        },
    )
    assert result == insight_client.timeseries_result


def test_raw_params_use_singular_session_id_for_single_runtime_session() -> None:
    from witty_service.application.insight_facade import InsightFacade

    params = InsightFacade._raw_params(session_ids=["runtime-1"])

    assert params == {"session_id": "runtime-1"}


def test_get_interruption_count_filters_to_all_managed_runtime_sessions(
    repo: SqliteRepository,
) -> None:
    from witty_service.application.insight_facade import InsightFacade

    _create_agent(repo, "agent-1", "Alpha")
    _create_agent(repo, "agent-2", "Beta")
    _create_session(repo, agent_id="agent-1", session_id="session-1", runtime_session_id="runtime-1")
    _create_session(repo, agent_id="agent-2", session_id="session-2", runtime_session_id="runtime-2")

    insight_client = FakeInsightClient()
    insight_client.interruption_count_result = {
        "total": 4,
        "by_severity": {"critical": 1, "high": 1, "medium": 1, "low": 1},
    }
    facade = InsightFacade(
        ServiceContainer(
            repository=repo,
            workspace_store=MagicMock(),
            insight_client=insight_client,
        ),
    )

    result = facade.get_interruption_count(start_ns=10, end_ns=20)

    assert insight_client.calls[-1] == (
        "get_interruption_count",
        {"start_ns": 10, "end_ns": 20, "session_ids": ["runtime-1", "runtime-2"]},
    )
    assert result == insight_client.interruption_count_result


def test_get_interruption_session_counts_remaps_runtime_session_ids_to_witty_ids(
    repo: SqliteRepository,
) -> None:
    from witty_service.application.insight_facade import InsightFacade

    _create_agent(repo, "agent-1", "Alpha")
    _create_session(repo, agent_id="agent-1", session_id="session-1", runtime_session_id="runtime-1")

    insight_client = FakeInsightClient()
    insight_client.interruption_session_counts_result = [
        {
            "session_id": "runtime-1",
            "total": 2,
            "by_severity": {"critical": 1, "high": 1, "medium": 0, "low": 0},
            "types": [{"interruption_type": "agent_crash", "severity": "critical", "count": 1}],
        },
        {
            "session_id": "heartbeat-runtime",
            "total": 1,
            "by_severity": {"critical": 0, "high": 1, "medium": 0, "low": 0},
            "types": [{"interruption_type": "tool_hang", "severity": "high", "count": 1}],
        },
    ]
    facade = InsightFacade(
        ServiceContainer(
            repository=repo,
            workspace_store=MagicMock(),
            insight_client=insight_client,
        ),
    )

    result = facade.get_interruption_session_counts()

    assert result == [
        {
            "session_id": "session-1",
            "runtime_session_id": "runtime-1",
            "total": 2,
            "by_severity": {"critical": 1, "high": 1, "medium": 0, "low": 0},
            "types": [{"interruption_type": "agent_crash", "severity": "critical", "count": 1}],
        }
    ]


def test_get_agent_health_joins_managed_agents_and_orphan_runtimes(
    repo: SqliteRepository,
) -> None:
    from witty_service.application.insight_facade import InsightFacade

    _create_agent(repo, "agent-1", "Alpha")
    _create_agent(repo, "agent-2", "Beta")
    repo.save_sandbox_state(
        "agent-1",
        sandbox_payload_json={
            "sandbox_id": "sandbox-1",
            "workspace_path": "/tmp/agent-1",
            "metadata": {"gateway_port": 18080, "stderr_log_path": "/tmp/alpha.err"},
        },
        adapter_base_url="http://127.0.0.1:18080",
        adapter_ready=True,
    )
    repo.save_sandbox_state(
        "agent-2",
        sandbox_payload_json={
            "sandbox_id": "sandbox-2",
            "workspace_path": "/tmp/agent-2",
            "metadata": {"gateway_port": 18081},
        },
        adapter_base_url="http://127.0.0.1:18081",
        adapter_ready=False,
    )

    insight_client = FakeInsightClient()
    insight_client.agent_health_result = {
        "agents": [
            {
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
            },
        ],
        "last_scan_time": 999,
    }
    facade = InsightFacade(
        ServiceContainer(
            repository=repo,
            workspace_store=MagicMock(),
            insight_client=insight_client,
        ),
    )

    result = facade.get_agent_health()

    assert result["last_scan_time"] == 999
    assert result["agents"] == [
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
            "candidate_runtimes": [
                {
                    "pid": 101,
                    "agent_name": "raw-alpha",
                    "category": "openclaw",
                    "exe_path": "/usr/bin/openclaw",
                    "ports": [18080],
                    "status": "healthy",
                    "last_check_time": 111,
                    "latency_ms": 12,
                    "error_message": None,
                }
            ],
        },
        {
            "witty_agent_id": "agent-2",
            "witty_agent_name": "Beta",
            "witty_status": "running",
            "overall_status": "missing_runtime",
            "status_reason": "No matching runtime health entry found.",
            "adapter_type": "http",
            "sandbox_type": "local_process",
            "workspace_path": "/tmp/agent-2",
            "gateway_port": 18081,
            "adapter_base_url": "http://127.0.0.1:18081",
            "adapter_ready": False,
            "adapter_status": "not_ready",
            "adapter_latency_ms": None,
            "adapter_error_message": None,
            "adapter_pid": None,
            "stderr_log_path": None,
            "runtime": None,
            "candidate_runtimes": [],
        },
    ]
    assert result["orphan_runtimes"] == [
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
    ]
