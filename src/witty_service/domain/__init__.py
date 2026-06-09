"""Domain primitives for witty service."""

from witty_service.domain.enums import AgentStatus, can_transition
from witty_service.domain.errors import (
    AgentConfigUpdateForbiddenError,
    AgentContextMismatchError,
    AgentDefaultNotConfiguredError,
    AgentIdNotConfiguredError,
    AgentServiceError,
    DomainError,
    InvalidAgentConfigError,
    InvalidAgentTransitionError,
    OpenClawAgentNotFoundError,
)
from witty_service.domain.models import ErrorPayload

__all__ = [
    "AgentConfigUpdateForbiddenError",
    "AgentContextMismatchError",
    "AgentDefaultNotConfiguredError",
    "AgentIdNotConfiguredError",
    "AgentServiceError",
    "AgentStatus",
    "DomainError",
    "ErrorPayload",
    "InvalidAgentConfigError",
    "InvalidAgentTransitionError",
    "OpenClawAgentNotFoundError",
    "can_transition",
]
