from __future__ import annotations

from copy import deepcopy
from typing import Any

from witty_service.domain.models import ErrorPayload


class DomainError(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = deepcopy(details or {})

    def to_payload(self) -> ErrorPayload:
        return ErrorPayload(
            code=self.code,
            message=self.message,
            details=deepcopy(self.details),
        )

    def __str__(self) -> str:
        return self.message


class AgentServiceError(DomainError):
    pass


class InvalidAgentTransitionError(AgentServiceError):
    def __init__(self, *, current: str, target: str) -> None:
        super().__init__(
            code="INVALID_AGENT_TRANSITION",
            message="invalid agent state transition",
            status_code=400,
            details={"current": current, "target": target},
        )


class AgentConfigUpdateForbiddenError(AgentServiceError):
    def __init__(self) -> None:
        super().__init__(
            code="AGENT_CONFIG_UPDATE_FORBIDDEN",
            message="cannot update agent config while running",
            status_code=409,
        )


class InvalidAgentConfigError(AgentServiceError):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_AGENT_CONFIG",
            message="invalid agent config",
            status_code=400,
        )


class AgentIdNotConfiguredError(AgentServiceError):
    def __init__(self, *, agent_id: str, configured_ids: list[str]) -> None:
        super().__init__(
            code="AGENT_ID_NOT_CONFIGURED",
            message="agent id is not configured in openclaw agents.list",
            status_code=400,
            details={"agent_id": agent_id, "configured_ids": configured_ids},
        )


class AgentDefaultNotConfiguredError(AgentServiceError):
    def __init__(self) -> None:
        super().__init__(
            code="AGENT_DEFAULT_NOT_CONFIGURED",
            message="default agent is not configured in openclaw agents.list",
            status_code=500,
        )


class AgentContextMismatchError(AgentServiceError):
    def __init__(self, *, requested_agent_id: str, current_agent_id: str | None) -> None:
        super().__init__(
            code="AGENT_CONTEXT_MISMATCH",
            message="requested agent id does not match current agent context",
            status_code=409,
            details={
                "requested_agent_id": requested_agent_id,
                "current_agent_id": current_agent_id,
            },
        )


class OpenClawAgentNotFoundError(AgentServiceError):
    def __init__(self, *, agent_id: str) -> None:
        super().__init__(
            code="OPENCLAW_AGENT_NOT_FOUND",
            message="openclaw gateway did not load configured agent",
            status_code=500,
            details={"agent_id": agent_id},
        )
