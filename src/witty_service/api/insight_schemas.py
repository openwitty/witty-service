from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class InsightCapabilitiesFeatures(BaseModel):
    sessions: bool
    timeseries: bool
    interruptions: bool
    health: bool


class InsightCapabilitiesResponse(BaseModel):
    enabled: bool
    reachable: bool
    features: InsightCapabilitiesFeatures


class InsightWittyAgentResponse(BaseModel):
    witty_agent_id: str
    witty_agent_name: str
    status: str


class InsightSessionSummaryResponse(BaseModel):
    session_id: str
    runtime_session_id: str | None = None
    witty_agent_id: str
    witty_agent_name: str
    agent_name: str | None = None
    conversation_count: int
    first_seen_ns: int
    last_seen_ns: int
    total_input_tokens: int
    total_output_tokens: int
    model: str | None = None


class InsightTraceSummaryResponse(BaseModel):
    trace_id: str
    conversation_id: str
    call_count: int
    total_input_tokens: int
    total_output_tokens: int
    start_ns: int
    end_ns: int | None = None
    model: str | None = None
    user_query: str | None = None


class InsightTraceDetailResponse(BaseModel):
    id: int
    call_id: str | None = None
    start_timestamp_ns: int
    end_timestamp_ns: int | None = None
    model: str | None = None
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_messages: str | None = None
    output_messages: str | None = None
    system_instructions: str | None = None
    agent_name: str | None = None
    process_name: str | None = None
    pid: int | None = None
    user_query: str | None = None
    event_json: str | None = None
    trace_id: str | None = None
    conversation_id: str | None = None
    cache_read_tokens: int | None = None
    status: str | None = None
    interruption_type: str | None = None


class InsightConversationDetailResponse(InsightTraceDetailResponse):
    pass


class InsightInterruptionRecordResponse(BaseModel):
    id: int | None = None
    interruption_id: str
    session_id: str | None = None
    runtime_session_id: str | None = None
    trace_id: str | None = None
    conversation_id: str | None = None
    call_id: str | None = None
    pid: int | None = None
    agent_name: str | None = None
    interruption_type: str
    severity: str
    occurred_at_ns: int
    detail: str | None = None
    resolved: bool


class InsightTimeseriesBucketResponse(BaseModel):
    bucket_start_ns: int
    input_tokens: int
    output_tokens: int
    total_tokens: int


class InsightModelTimeseriesBucketResponse(BaseModel):
    bucket_start_ns: int
    model: str
    total_tokens: int


class InsightTimeseriesResponse(BaseModel):
    token_series: list[InsightTimeseriesBucketResponse] = Field(default_factory=list)
    model_series: list[InsightModelTimeseriesBucketResponse] = Field(default_factory=list)


class InsightSeverityCounts(BaseModel):
    critical: int
    high: int
    medium: int
    low: int


class InsightInterruptionTypeStatResponse(BaseModel):
    interruption_type: str
    severity: str
    count: int


class InsightInterruptionCountResponse(BaseModel):
    total: int
    by_severity: InsightSeverityCounts


class InsightSessionInterruptionCountResponse(BaseModel):
    session_id: str
    runtime_session_id: str | None = None
    total: int
    by_severity: InsightSeverityCounts
    types: list[InsightInterruptionTypeStatResponse] = Field(default_factory=list)


class InsightConversationInterruptionCountResponse(BaseModel):
    conversation_id: str
    total: int
    by_severity: InsightSeverityCounts
    types: list[InsightInterruptionTypeStatResponse] = Field(default_factory=list)


class InsightInterruptionResolveResponse(BaseModel):
    status: str


class InsightAgentHealthActionResponse(BaseModel):
    ok: bool


class InsightRestartAgentHealthResponse(InsightAgentHealthActionResponse):
    new_pid: int
    cmd: list[str] = Field(default_factory=list)


class InsightAtifDocumentResponse(BaseModel):
    schema_version: str
    session_id: str
    runtime_session_id: str | None = None
    agent: dict[str, Any]
    steps: list[dict[str, Any]] = Field(default_factory=list)
    final_metrics: dict[str, Any] | None = None
    extra: Any | None = None


class InsightRuntimeHealthResponse(BaseModel):
    pid: int
    agent_name: str
    category: str
    exe_path: str
    ports: list[int] = Field(default_factory=list)
    status: str
    last_check_time: int
    latency_ms: int | None = None
    error_message: str | None = None


class InsightManagedAgentHealthResponse(BaseModel):
    witty_agent_id: str
    witty_agent_name: str
    witty_status: str | None = None
    overall_status: str
    status_reason: str | None = None
    adapter_type: str | None = None
    sandbox_type: str | None = None
    workspace_path: str | None = None
    gateway_port: int | None = None
    adapter_base_url: str | None = None
    adapter_ready: bool | None = None
    adapter_status: str | None = None
    adapter_latency_ms: int | None = None
    adapter_error_message: str | None = None
    adapter_pid: int | None = None
    stderr_log_path: str | None = None
    runtime: InsightRuntimeHealthResponse | None = None
    candidate_runtimes: list[InsightRuntimeHealthResponse] = Field(default_factory=list)


class InsightAgentHealthResponse(BaseModel):
    agents: list[InsightManagedAgentHealthResponse] = Field(default_factory=list)
    orphan_runtimes: list[InsightRuntimeHealthResponse] = Field(default_factory=list)
    last_scan_time: int


InsightOrphanRuntimeHealthResponse = InsightRuntimeHealthResponse
InsightTraceDetailListResponse = list[InsightTraceDetailResponse]
InsightConversationDetailListResponse = list[InsightConversationDetailResponse]
