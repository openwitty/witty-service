from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from witty_service.api.auth import require_bearer_auth
from witty_service.api.insight_schemas import (
    InsightAgentHealthResponse,
    InsightCapabilitiesResponse,
    InsightConversationDetailResponse,
    InsightConversationInterruptionCountResponse,
    InsightInterruptionCountResponse,
    InsightInterruptionTypeStatResponse,
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
def get_capabilities(
    services: ServiceContainer = Depends(get_services),
) -> InsightCapabilitiesResponse:
    return InsightCapabilitiesResponse.model_validate(
        services.get_insight_facade().get_capabilities()
    )


@router.get("/witty-agents", response_model=list[InsightWittyAgentResponse])
def list_witty_agents(
    services: ServiceContainer = Depends(get_services),
) -> list[InsightWittyAgentResponse]:
    return [
        InsightWittyAgentResponse.model_validate(item)
        for item in services.get_insight_facade().list_witty_agents()
    ]


@router.get("/sessions", response_model=list[InsightSessionSummaryResponse])
def list_sessions(
    witty_agent_id: str | None = None,
    start_ns: int | None = None,
    end_ns: int | None = None,
    services: ServiceContainer = Depends(get_services),
) -> list[InsightSessionSummaryResponse]:
    return [
        InsightSessionSummaryResponse.model_validate(item)
        for item in services.get_insight_facade().list_sessions(
            witty_agent_id=witty_agent_id,
            start_ns=start_ns,
            end_ns=end_ns,
        )
    ]


@router.get("/sessions/{session_id}/traces", response_model=list[InsightTraceSummaryResponse])
def get_session_traces(
    session_id: str,
    start_ns: int | None = None,
    end_ns: int | None = None,
    services: ServiceContainer = Depends(get_services),
) -> list[InsightTraceSummaryResponse]:
    return [
        InsightTraceSummaryResponse.model_validate(item)
        for item in services.get_insight_facade().get_session_traces(
            session_id,
            start_ns=start_ns,
            end_ns=end_ns,
        )
    ]


@router.get("/traces/{trace_id}", response_model=list[InsightTraceDetailResponse])
def get_trace_detail(
    trace_id: str,
    services: ServiceContainer = Depends(get_services),
) -> list[InsightTraceDetailResponse]:
    return [
        InsightTraceDetailResponse.model_validate(item)
        for item in services.get_insight_facade().get_trace_detail(trace_id)
    ]


@router.get(
    "/conversations/{conversation_id}",
    response_model=list[InsightConversationDetailResponse],
)
def get_conversation_detail(
    conversation_id: str,
    services: ServiceContainer = Depends(get_services),
) -> list[InsightConversationDetailResponse]:
    return [
        InsightConversationDetailResponse.model_validate(item)
        for item in services.get_insight_facade().get_conversation_detail(conversation_id)
    ]


@router.get("/timeseries", response_model=InsightTimeseriesResponse)
def get_timeseries(
    witty_agent_id: str | None = None,
    start_ns: int | None = None,
    end_ns: int | None = None,
    buckets: int | None = None,
    services: ServiceContainer = Depends(get_services),
) -> InsightTimeseriesResponse:
    return InsightTimeseriesResponse.model_validate(
        services.get_insight_facade().get_timeseries(
            witty_agent_id=witty_agent_id,
            start_ns=start_ns,
            end_ns=end_ns,
            buckets=buckets,
        )
    )


@router.get("/interruptions/count", response_model=InsightInterruptionCountResponse)
def get_interruption_count(
    witty_agent_id: str | None = None,
    start_ns: int | None = None,
    end_ns: int | None = None,
    services: ServiceContainer = Depends(get_services),
) -> InsightInterruptionCountResponse:
    return InsightInterruptionCountResponse.model_validate(
        services.get_insight_facade().get_interruption_count(
            witty_agent_id=witty_agent_id,
            start_ns=start_ns,
            end_ns=end_ns,
        )
    )


@router.get("/interruptions/stats", response_model=list[InsightInterruptionTypeStatResponse])
def get_interruption_stats(
    witty_agent_id: str | None = None,
    start_ns: int | None = None,
    end_ns: int | None = None,
    services: ServiceContainer = Depends(get_services),
) -> list[InsightInterruptionTypeStatResponse]:
    return [
        InsightInterruptionTypeStatResponse.model_validate(item)
        for item in services.get_insight_facade().get_interruption_stats(
            witty_agent_id=witty_agent_id,
            start_ns=start_ns,
            end_ns=end_ns,
        )
    ]


@router.get(
    "/interruptions/session-counts",
    response_model=list[InsightSessionInterruptionCountResponse],
)
def get_interruption_session_counts(
    witty_agent_id: str | None = None,
    start_ns: int | None = None,
    end_ns: int | None = None,
    services: ServiceContainer = Depends(get_services),
) -> list[InsightSessionInterruptionCountResponse]:
    return [
        InsightSessionInterruptionCountResponse.model_validate(item)
        for item in services.get_insight_facade().get_interruption_session_counts(
            witty_agent_id=witty_agent_id,
            start_ns=start_ns,
            end_ns=end_ns,
        )
    ]


@router.get(
    "/interruptions/conversation-counts",
    response_model=list[InsightConversationInterruptionCountResponse],
)
def get_interruption_conversation_counts(
    witty_agent_id: str | None = None,
    start_ns: int | None = None,
    end_ns: int | None = None,
    services: ServiceContainer = Depends(get_services),
) -> list[InsightConversationInterruptionCountResponse]:
    return [
        InsightConversationInterruptionCountResponse.model_validate(item)
        for item in services.get_insight_facade().get_interruption_conversation_counts(
            witty_agent_id=witty_agent_id,
            start_ns=start_ns,
            end_ns=end_ns,
        )
    ]


@router.get("/agent-health", response_model=InsightAgentHealthResponse)
def get_agent_health(
    services: ServiceContainer = Depends(get_services),
) -> InsightAgentHealthResponse:
    return InsightAgentHealthResponse.model_validate(
        services.get_insight_facade().get_agent_health()
    )
