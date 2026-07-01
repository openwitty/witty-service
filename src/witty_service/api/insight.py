from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from witty_service.api.auth import require_bearer_auth
from witty_service.api.insight_schemas import (
    InsightAgentHealthActionResponse,
    InsightAgentHealthResponse,
    InsightAtifDocumentResponse,
    InsightCapabilitiesResponse,
    InsightConversationDetailResponse,
    InsightConversationInterruptionCountResponse,
    InsightInterruptionCountResponse,
    InsightInterruptionRecordResponse,
    InsightInterruptionResolveResponse,
    InsightInterruptionTypeStatResponse,
    InsightRestartAgentHealthResponse,
    InsightSessionInterruptionCountResponse,
    InsightSessionSummaryResponse,
    InsightTimeseriesResponse,
    InsightTraceDetailResponse,
    InsightTraceSummaryResponse,
    InsightWittyAgentResponse,
)
from witty_service.api.services import ServiceContainer


router = APIRouter(
    prefix="/insight",
    tags=["insight"],
    dependencies=[Depends(require_bearer_auth)],
)


def get_services(request: Request) -> ServiceContainer:
    return request.app.state.services


@router.get("/capabilities", response_model=InsightCapabilitiesResponse)
async def get_capabilities(
    services: ServiceContainer = Depends(get_services),
) -> InsightCapabilitiesResponse:
    return InsightCapabilitiesResponse.model_validate(
        await services.get_insight_facade().get_capabilities()
    )


@router.get("/witty-agents", response_model=list[InsightWittyAgentResponse])
async def list_witty_agents(
    services: ServiceContainer = Depends(get_services),
) -> list[InsightWittyAgentResponse]:
    return [
        InsightWittyAgentResponse.model_validate(item)
        for item in await services.get_insight_facade().list_witty_agents()
    ]


@router.get("/sessions", response_model=list[InsightSessionSummaryResponse])
async def list_sessions(
    witty_agent_id: str | None = None,
    start_ns: int | None = None,
    end_ns: int | None = None,
    services: ServiceContainer = Depends(get_services),
) -> list[InsightSessionSummaryResponse]:
    return [
        InsightSessionSummaryResponse.model_validate(item)
        for item in await services.get_insight_facade().list_sessions(
            witty_agent_id=witty_agent_id,
            start_ns=start_ns,
            end_ns=end_ns,
        )
    ]


@router.get("/sessions/{session_id}/traces", response_model=list[InsightTraceSummaryResponse])
async def get_session_traces(
    session_id: str,
    start_ns: int | None = None,
    end_ns: int | None = None,
    services: ServiceContainer = Depends(get_services),
) -> list[InsightTraceSummaryResponse]:
    return [
        InsightTraceSummaryResponse.model_validate(item)
        for item in await services.get_insight_facade().get_session_traces(
            session_id,
            start_ns=start_ns,
            end_ns=end_ns,
        )
    ]


@router.get(
    "/sessions/{session_id}/interruptions",
    response_model=list[InsightInterruptionRecordResponse],
)
async def get_session_interruptions(
    session_id: str,
    services: ServiceContainer = Depends(get_services),
) -> list[InsightInterruptionRecordResponse]:
    return [
        InsightInterruptionRecordResponse.model_validate(item)
        for item in await services.get_insight_facade().get_session_interruptions(session_id)
    ]


@router.get("/traces/{trace_id}", response_model=list[InsightTraceDetailResponse])
async def get_trace_detail(
    trace_id: str,
    services: ServiceContainer = Depends(get_services),
) -> list[InsightTraceDetailResponse]:
    return [
        InsightTraceDetailResponse.model_validate(item)
        for item in await services.get_insight_facade().get_trace_detail(trace_id)
    ]


@router.get(
    "/conversations/{conversation_id}",
    response_model=list[InsightConversationDetailResponse],
)
async def get_conversation_detail(
    conversation_id: str,
    services: ServiceContainer = Depends(get_services),
) -> list[InsightConversationDetailResponse]:
    return [
        InsightConversationDetailResponse.model_validate(item)
        for item in await services.get_insight_facade().get_conversation_detail(conversation_id)
    ]


@router.get(
    "/conversations/{conversation_id}/interruptions",
    response_model=list[InsightInterruptionRecordResponse],
)
async def get_conversation_interruptions(
    conversation_id: str,
    services: ServiceContainer = Depends(get_services),
) -> list[InsightInterruptionRecordResponse]:
    return [
        InsightInterruptionRecordResponse.model_validate(item)
        for item in await services.get_insight_facade().get_conversation_interruptions(conversation_id)
    ]


@router.get("/timeseries", response_model=InsightTimeseriesResponse)
async def get_timeseries(
    witty_agent_id: str | None = None,
    start_ns: int | None = None,
    end_ns: int | None = None,
    buckets: int | None = None,
    services: ServiceContainer = Depends(get_services),
) -> InsightTimeseriesResponse:
    return InsightTimeseriesResponse.model_validate(
        await services.get_insight_facade().get_timeseries(
            witty_agent_id=witty_agent_id,
            start_ns=start_ns,
            end_ns=end_ns,
            buckets=buckets,
        )
    )


@router.get("/interruptions/count", response_model=InsightInterruptionCountResponse)
async def get_interruption_count(
    witty_agent_id: str | None = None,
    start_ns: int | None = None,
    end_ns: int | None = None,
    services: ServiceContainer = Depends(get_services),
) -> InsightInterruptionCountResponse:
    return InsightInterruptionCountResponse.model_validate(
        await services.get_insight_facade().get_interruption_count(
            witty_agent_id=witty_agent_id,
            start_ns=start_ns,
            end_ns=end_ns,
        )
    )


@router.get("/interruptions/stats", response_model=list[InsightInterruptionTypeStatResponse])
async def get_interruption_stats(
    witty_agent_id: str | None = None,
    start_ns: int | None = None,
    end_ns: int | None = None,
    services: ServiceContainer = Depends(get_services),
) -> list[InsightInterruptionTypeStatResponse]:
    return [
        InsightInterruptionTypeStatResponse.model_validate(item)
        for item in await services.get_insight_facade().get_interruption_stats(
            witty_agent_id=witty_agent_id,
            start_ns=start_ns,
            end_ns=end_ns,
        )
    ]


@router.get(
    "/interruptions/session-counts",
    response_model=list[InsightSessionInterruptionCountResponse],
)
async def get_interruption_session_counts(
    witty_agent_id: str | None = None,
    start_ns: int | None = None,
    end_ns: int | None = None,
    services: ServiceContainer = Depends(get_services),
) -> list[InsightSessionInterruptionCountResponse]:
    return [
        InsightSessionInterruptionCountResponse.model_validate(item)
        for item in await services.get_insight_facade().get_interruption_session_counts(
            witty_agent_id=witty_agent_id,
            start_ns=start_ns,
            end_ns=end_ns,
        )
    ]


@router.get(
    "/interruptions/conversation-counts",
    response_model=list[InsightConversationInterruptionCountResponse],
)
async def get_interruption_conversation_counts(
    witty_agent_id: str | None = None,
    start_ns: int | None = None,
    end_ns: int | None = None,
    services: ServiceContainer = Depends(get_services),
) -> list[InsightConversationInterruptionCountResponse]:
    return [
        InsightConversationInterruptionCountResponse.model_validate(item)
        for item in await services.get_insight_facade().get_interruption_conversation_counts(
            witty_agent_id=witty_agent_id,
            start_ns=start_ns,
            end_ns=end_ns,
        )
    ]


@router.post(
    "/interruptions/{interruption_id}/resolve",
    response_model=InsightInterruptionResolveResponse,
)
async def resolve_interruption(
    interruption_id: str,
    services: ServiceContainer = Depends(get_services),
) -> InsightInterruptionResolveResponse:
    return InsightInterruptionResolveResponse.model_validate(
        await services.get_insight_facade().resolve_interruption(interruption_id)
    )


@router.get("/agent-health", response_model=InsightAgentHealthResponse)
async def get_agent_health(
    services: ServiceContainer = Depends(get_services),
) -> InsightAgentHealthResponse:
    return InsightAgentHealthResponse.model_validate(
        await services.get_insight_facade().get_agent_health()
    )


@router.delete("/agent-health/{pid}", response_model=InsightAgentHealthActionResponse)
async def delete_agent_health(
    pid: int,
    services: ServiceContainer = Depends(get_services),
) -> InsightAgentHealthActionResponse:
    return InsightAgentHealthActionResponse.model_validate(
        await services.get_insight_facade().delete_agent_health(pid)
    )


@router.post("/agent-health/{pid}/restart", response_model=InsightRestartAgentHealthResponse)
async def restart_agent_health(
    pid: int,
    services: ServiceContainer = Depends(get_services),
) -> InsightRestartAgentHealthResponse:
    return InsightRestartAgentHealthResponse.model_validate(
        await services.get_insight_facade().restart_agent_health(pid)
    )


@router.get(
    "/export/atif/session/{session_id}",
    response_model=InsightAtifDocumentResponse,
)
async def export_atif_session(
    session_id: str,
    services: ServiceContainer = Depends(get_services),
) -> InsightAtifDocumentResponse:
    return InsightAtifDocumentResponse.model_validate(
        await services.get_insight_facade().export_atif_session(session_id)
    )


@router.get(
    "/export/atif/conversation/{conversation_id}",
    response_model=InsightAtifDocumentResponse,
)
async def export_atif_conversation(
    conversation_id: str,
    services: ServiceContainer = Depends(get_services),
) -> InsightAtifDocumentResponse:
    return InsightAtifDocumentResponse.model_validate(
        await services.get_insight_facade().export_atif_conversation(conversation_id)
    )
