from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from witty_service.persistence.repositories import AgentWithRuntimeStateRecord


class HealthMatcher:
    def find_runtime_candidates(
        self,
        record: AgentWithRuntimeStateRecord,
        runtimes: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        runtime_state = record.runtime_state
        if runtime_state is None:
            return []

        metadata = self._metadata(runtime_state.sandbox_payload_json)
        port_candidates = {
            value
            for value in (
                self._extract_port(runtime_state.adapter_base_url),
                self._int_or_none(metadata.get("gateway_port")),
                self._int_or_none(metadata.get("host_port")),
            )
            if value is not None
        }
        if not port_candidates:
            return []

        return [
            runtime
            for runtime in runtimes
            if any(port in runtime.get("ports", []) for port in port_candidates)
        ]

    def build_managed_health_entry(
        self,
        record: AgentWithRuntimeStateRecord,
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        agent = record.agent
        runtime_state = record.runtime_state
        metadata = self._metadata(runtime_state.sandbox_payload_json) if runtime_state is not None else {}
        gateway_port = self._int_or_none(metadata.get("gateway_port"))
        stderr_log_path = metadata.get("stderr_log_path")
        matched_runtime = candidates[0] if len(candidates) == 1 else None
        overall_status, status_reason = self.overall_health_status(
            runtime_state=runtime_state,
            candidates=candidates,
        )

        adapter_status: str | None = None
        if runtime_state is not None:
            adapter_status = "ready" if runtime_state.adapter_ready else "not_ready"

        return {
            "witty_agent_id": agent.id,
            "witty_agent_name": agent.name,
            "witty_status": agent.status.value,
            "overall_status": overall_status,
            "status_reason": status_reason,
            "adapter_type": agent.adapter_type,
            "sandbox_type": agent.sandbox_type,
            "workspace_path": agent.workspace_path,
            "gateway_port": gateway_port,
            "adapter_base_url": None if runtime_state is None else runtime_state.adapter_base_url,
            "adapter_ready": None if runtime_state is None else runtime_state.adapter_ready,
            "adapter_status": adapter_status,
            "adapter_latency_ms": None if matched_runtime is None else matched_runtime.get("latency_ms"),
            "adapter_error_message": None if runtime_state is None else runtime_state.last_error,
            "adapter_pid": None if matched_runtime is None else matched_runtime.get("pid"),
            "stderr_log_path": stderr_log_path if isinstance(stderr_log_path, str) else None,
            "runtime": matched_runtime,
            "candidate_runtimes": candidates,
        }

    @staticmethod
    def overall_health_status(
        *,
        runtime_state: Any,
        candidates: list[dict[str, Any]],
    ) -> tuple[str, str | None]:
        if len(candidates) > 1:
            return "ambiguous", "Multiple runtime health entries matched this managed agent."
        if len(candidates) == 0:
            return "missing_runtime", "No matching runtime health entry found."

        runtime = candidates[0]
        status = str(runtime.get("status") or "unknown")
        if runtime_state is not None and not runtime_state.adapter_ready:
            return "degraded", "Adapter runtime state is not ready."
        if runtime_state is not None and runtime_state.last_error:
            return "degraded", runtime_state.last_error
        return status, None

    @staticmethod
    def normalize_runtime_health(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "pid": item.get("pid"),
            "agent_name": item.get("agent_name"),
            "category": item.get("category"),
            "exe_path": item.get("exe_path"),
            "ports": item.get("ports") if isinstance(item.get("ports"), list) else [],
            "status": item.get("status"),
            "last_check_time": int(item.get("last_check_time", 0) or 0),
            "latency_ms": item.get("latency_ms"),
            "error_message": item.get("error_message"),
        }

    @staticmethod
    def _metadata(payload: dict[str, Any]) -> dict[str, Any]:
        metadata = payload.get("metadata", {})
        return metadata if isinstance(metadata, dict) else {}

    @staticmethod
    def _extract_port(base_url: str | None) -> int | None:
        if not base_url:
            return None
        try:
            return urlparse(base_url).port
        except ValueError:
            return None

    @staticmethod
    def _int_or_none(value: Any) -> int | None:
        return value if isinstance(value, int) else None
