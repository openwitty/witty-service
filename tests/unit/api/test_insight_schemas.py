from __future__ import annotations

from witty_service.api.insight_schemas import (
    InsightAgentHealthResponse,
    InsightAtifDocumentResponse,
    InsightCapabilitiesResponse,
    InsightInterruptionCountResponse,
    InsightInterruptionRecordResponse,
    InsightSessionSummaryResponse,
    InsightTimeseriesBucketResponse,
    InsightTimeseriesResponse,
    InsightTraceSummaryResponse,
    InsightWittyAgentResponse,
)


def test_schema_smoke_validates_core_summary_payloads() -> None:
    capabilities = InsightCapabilitiesResponse.model_validate(
        {
            "enabled": True,
            "reachable": False,
            "features": {
                "sessions": True,
                "timeseries": True,
                "interruptions": True,
                "health": True,
            },
        }
    )
    agent = InsightWittyAgentResponse.model_validate(
        {
            "witty_agent_id": "agent-1",
            "witty_agent_name": "Alpha",
            "status": "running",
        }
    )
    session = InsightSessionSummaryResponse.model_validate(
        {
            "session_id": "session-1",
            "runtime_session_id": "runtime-1",
            "witty_agent_id": "agent-1",
            "witty_agent_name": "Alpha",
            "agent_name": "Alpha",
            "conversation_count": 3,
            "first_seen_ns": 100,
            "last_seen_ns": 200,
            "total_input_tokens": 10,
            "total_output_tokens": 5,
            "model": "gpt-4o",
        }
    )
    trace_summary = InsightTraceSummaryResponse.model_validate(
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
    )

    assert capabilities.features.health is True
    assert agent.status == "running"
    assert session.runtime_session_id == "runtime-1"
    assert trace_summary.trace_id == "trace-1"


def test_schema_smoke_validates_nested_operational_payloads() -> None:
    timeseries = InsightTimeseriesResponse.model_validate(
        {
            "token_series": [
                {
                    "bucket_start_ns": 100,
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "total_tokens": 15,
                }
            ],
            "model_series": [
                {
                    "bucket_start_ns": 100,
                    "model": "gpt-4o",
                    "total_tokens": 15,
                }
            ],
        }
    )
    interruption_count = InsightInterruptionCountResponse.model_validate(
        {
            "total": 2,
            "by_severity": {"critical": 1, "high": 1, "medium": 0, "low": 0},
        }
    )
    interruption = InsightInterruptionRecordResponse.model_validate(
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
    )
    health = InsightAgentHealthResponse.model_validate(
        {
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
    )
    atif = InsightAtifDocumentResponse.model_validate(
        {
            "schema_version": "1.6",
            "session_id": "session-1",
            "runtime_session_id": "runtime-1",
            "agent": {"name": "Alpha", "version": "test"},
            "steps": [{"step_id": 1, "source": "user", "message": "hello"}],
            "final_metrics": {"total_steps": 1},
        }
    )

    assert timeseries.token_series == [
        InsightTimeseriesBucketResponse(
            bucket_start_ns=100,
            input_tokens=10,
            output_tokens=5,
            total_tokens=15,
        )
    ]
    assert interruption_count.total == 2
    assert interruption.runtime_session_id == "runtime-1"
    assert health.orphan_runtimes[0].pid == 202
    assert atif.steps[0]["step_id"] == 1
