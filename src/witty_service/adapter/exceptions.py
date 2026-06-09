from __future__ import annotations

from typing import Any

from witty_service.domain.errors import DomainError


class AdaptorError(DomainError):
    pass


class AdaptorConnectionError(AdaptorError):
    def __init__(
        self,
        *,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="ADAPTOR_CONNECTION_ERROR",
            message=message,
            status_code=503,
            details=details,
        )


class AdaptorConnectionTimeout(AdaptorError):
    def __init__(
        self,
        *,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="ADAPTOR_CONNECTION_TIMEOUT",
            message=message,
            status_code=504,
            details=details,
        )


class AdaptorSendFailed(AdaptorError):
    def __init__(
        self,
        *,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="ADAPTOR_SEND_FAILED",
            message=message,
            status_code=500,
            details=details,
        )


class AdaptorReceiveError(AdaptorError):
    def __init__(
        self,
        *,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="ADAPTOR_RECEIVE_ERROR",
            message=message,
            status_code=500,
            details=details,
        )