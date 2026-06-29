from __future__ import annotations

from witty_service.api.insight_schemas import (
    InsightAgentHealthResponse,
    InsightCapabilitiesResponse,
    InsightConversationInterruptionCountResponse,
    InsightInterruptionCountResponse,
    InsightInterruptionTypeStatResponse,
    InsightManagedAgentHealthResponse,
    InsightModelTimeseriesBucketResponse,
    InsightSessionInterruptionCountResponse,
    InsightSessionSummaryResponse,
    InsightTimeseriesBucketResponse,
    InsightTimeseriesResponse,
    InsightTraceDetailResponse,
    InsightTraceSummaryResponse,
    InsightWittyAgentResponse,
)


def test_capabilities_and_witty_agents_validate() -> None:
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

    assert capabilities.model_dump() == {
        "enabled": True,
        "reachable": False,
        "features": {
            "sessions": True,
            "timeseries": True,
            "interruptions": True,
            "health": True,
        },
    }
    assert agent.model_dump() == {
        "witty_agent_id": "agent-1",
        "witty_agent_name": "Alpha",
        "status": "running",
    }


def test_session_and_trace_payloads_validate() -> None:
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
    trace_detail = InsightTraceDetailResponse.model_validate(
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
    )

    assert session.session_id == "session-1"
    assert session.runtime_session_id == "runtime-1"
    assert trace_summary.trace_id == "trace-1"
    assert trace_detail.conversation_id == "conv-1"


def test_timeseries_and_interruption_payloads_validate() -> None:
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
    interruption_type = InsightInterruptionTypeStatResponse.model_validate(
        {
            "interruption_type": "agent_crash",
            "severity": "critical",
            "count": 1,
        }
    )
    session_count = InsightSessionInterruptionCountResponse.model_validate(
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
    )
    conversation_count = InsightConversationInterruptionCountResponse.model_validate(
        {
            "conversation_id": "conv-1",
            "total": 1,
            "by_severity": {"critical": 0, "high": 1, "medium": 0, "low": 0},
            "types": [
                {
                    "interruption_type": "tool_hang",
                    "severity": "high",
                    "count": 1,
                }
            ],
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
    assert timeseries.model_series == [
        InsightModelTimeseriesBucketResponse(
            bucket_start_ns=100,
            model="gpt-4o",
            total_tokens=15,
        )
    ]
    assert interruption_count.total == 2
    assert interruption_type.count == 1
    assert session_count.runtime_session_id == "runtime-1"
    assert conversation_count.conversation_id == "conv-1"


def test_health_payload_validates_managed_and_orphan_runtimes() -> None:
    response = InsightAgentHealthResponse.model_validate(
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

    assert response.last_scan_time == 999
    assert response.agents == [
        InsightManagedAgentHealthResponse.model_validate(
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
            }
        )
    ]
    assert response.orphan_runtimes[0].pid == 202

