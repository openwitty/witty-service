from collections.abc import Iterator
from typing import Any

from witty_agent_server.runtimes.runtime_base import (
    RuntimeBase,
    RuntimeChunk,
    RuntimeResult,
    RuntimeTurnEvent,
    RuntimeType,
)


class OpenCodeRuntime(RuntimeBase):
    runtime_type: RuntimeType = "opencode"

    def list_sessions(self, *, agent_id: str) -> list[dict[str, Any]]:
        del agent_id
        raise NotImplementedError("opencode runtime is not implemented yet")

    def create_session(self, *, session_key: str) -> None:
        del session_key
        raise NotImplementedError("opencode runtime is not implemented yet")

    def delete_session(self, *, session_key: str) -> None:
        del session_key
        raise NotImplementedError("opencode runtime is not implemented yet")

    def abort_session(self, *, session_key: str) -> None:
        del session_key
        raise NotImplementedError("opencode runtime is not implemented yet")

    def run_turn(
        self,
        *,
        session_key: str,
        message: str,
    ) -> Iterator[RuntimeTurnEvent]:
        del session_key, message
        raise NotImplementedError("opencode runtime is not implemented yet")

    def send_message(self, session_id: str, message: str) -> RuntimeResult:
        raise NotImplementedError("opencode runtime is not implemented yet")

    def stream_message(self, session_id: str, message: str) -> Iterator[RuntimeChunk]:
        raise NotImplementedError("opencode runtime is not implemented yet")
