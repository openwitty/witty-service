from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from witty_service.domain.errors import DomainError, insight_session_mapping_not_found
from witty_service.persistence.repositories import AgentRecord, AgentWithRuntimeStateRecord, SessionRecord


if TYPE_CHECKING:
    from witty_service.api.services import ServiceContainer


_RUNTIME_TYPE = "openclaw"
_INTERRUPTION_SEVERITIES = ("critical", "high", "medium", "low")


class InsightFacade:
    def __init__(self, services: ServiceContainer) -> None:
        self._services = services
        self._repository = services.repository

    def get_capabilities(self) -> dict[str, Any]:
        enabled = self._services.insight_client is not None
        if not enabled:
            return {
                "enabled": False,
                "reachable": False,
                "features": self._feature_flags(False),
            }

        try:
            self._services.get_insight_client().get_health()
        except DomainError:
            reachable = False
        else:
            reachable = True

        return {
            "enabled": True,
            "reachable": reachable,
            "features": self._feature_flags(True),
        }

    def list_witty_agents(self) -> list[dict[str, Any]]:
        return [
            {
                "witty_agent_id": agent.id,
                "witty_agent_name": agent.name,
                "status": agent.status.value,
            }
            for agent in self._repository.list_agents()
        ]

    def list_sessions(
        self,
        *,
        witty_agent_id: str | None = None,
        start_ns: int | None = None,
        end_ns: int | None = None,
    ) -> list[dict[str, Any]]:
        runtime_session_ids = self._list_managed_runtime_session_ids(witty_agent_id=witty_agent_id)
        if not runtime_session_ids:
            return []

        raw_sessions = self._services.get_insight_client().get_sessions(
            self._raw_params(
                start_ns=start_ns,
                end_ns=end_ns,
                session_ids=runtime_session_ids,
            )
        )
        if not isinstance(raw_sessions, list):
            return []

        sessions_by_runtime_id = {
            session.runtime_session_id: session
            for session in self._repository.list_sessions_by_runtime_session_ids(
                _RUNTIME_TYPE,
                runtime_session_ids,
            )
            if session.runtime_session_id is not None
        }
        agent_ids = self._dedupe_preserve_order(
            [
                session.agent_id
                for session in sessions_by_runtime_id.values()
            ]
        )
        agents_by_id = {
            agent.id: agent
            for agent in self._repository.list_agent_records_by_ids(agent_ids)
        }

        enriched: list[dict[str, Any]] = []
        for item in raw_sessions:
            if not isinstance(item, dict):
                continue
            runtime_session_id = item.get("session_id")
            if not isinstance(runtime_session_id, str):
                continue
            session = sessions_by_runtime_id.get(runtime_session_id)
            if session is None:
                continue
            agent = agents_by_id.get(session.agent_id)
            if agent is None:
                continue
            enriched.append(
                {
                    "session_id": session.id,
                    "runtime_session_id": runtime_session_id,
                    "witty_agent_id": agent.id,
                    "witty_agent_name": agent.name,
                    "agent_name": agent.name,
                    "conversation_count": int(item.get("conversation_count", 0) or 0),
                    "first_seen_ns": int(item.get("first_seen_ns", 0) or 0),
                    "last_seen_ns": int(item.get("last_seen_ns", 0) or 0),
                    "total_input_tokens": int(item.get("total_input_tokens", 0) or 0),
                    "total_output_tokens": int(item.get("total_output_tokens", 0) or 0),
                    "model": item.get("model"),
                }
            )
        return enriched

    def get_session_traces(
        self,
        witty_session_id: str,
        *,
        start_ns: int | None = None,
        end_ns: int | None = None,
    ) -> Any:
        session = self._require_runtime_session(witty_session_id)
        return self._services.get_insight_client().get_session_traces(
            session.runtime_session_id,
            self._raw_params(start_ns=start_ns, end_ns=end_ns),
        )

    def get_session_interruptions(self, witty_session_id: str) -> list[dict[str, Any]]:
        session = self._require_runtime_session(witty_session_id)
        result = self._services.get_insight_client().get_session_interruptions(
            session.runtime_session_id,
        )
        if not isinstance(result, list):
            return []
        return self._remap_interruption_records(result)

    def get_conversation_interruptions(self, conversation_id: str) -> list[dict[str, Any]]:
        result = self._services.get_insight_client().get_conversation_interruptions(conversation_id)
        if not isinstance(result, list):
            return []
        return self._remap_interruption_records(result)

    def get_trace_detail(self, trace_id: str) -> Any:
        return self._services.get_insight_client().get_trace_detail(trace_id)

    def get_conversation_detail(self, conversation_id: str) -> Any:
        return self._services.get_insight_client().get_conversation_detail(conversation_id)

    def resolve_interruption(self, interruption_id: str) -> dict[str, Any]:
        result = self._services.get_insight_client().resolve_interruption(interruption_id)
        return result if isinstance(result, dict) else {"status": "resolved"}

    def get_timeseries(
        self,
        *,
        witty_agent_id: str | None = None,
        start_ns: int | None = None,
        end_ns: int | None = None,
        buckets: int | None = None,
    ) -> dict[str, Any]:
        runtime_session_ids = self._list_managed_runtime_session_ids(witty_agent_id=witty_agent_id)
        if not runtime_session_ids:
            return {"token_series": [], "model_series": []}
        result = self._services.get_insight_client().get_timeseries(
            self._raw_params(
                start_ns=start_ns,
                end_ns=end_ns,
                buckets=buckets,
                session_ids=runtime_session_ids,
            )
        )
        return result if isinstance(result, dict) else {"token_series": [], "model_series": []}

    def get_interruption_count(
        self,
        *,
        witty_agent_id: str | None = None,
        start_ns: int | None = None,
        end_ns: int | None = None,
    ) -> dict[str, Any]:
        runtime_session_ids = self._list_managed_runtime_session_ids(witty_agent_id=witty_agent_id)
        if not runtime_session_ids:
            return self._empty_interruption_count()
        result = self._services.get_insight_client().get_interruption_count(
            self._raw_params(
                start_ns=start_ns,
                end_ns=end_ns,
                session_ids=runtime_session_ids,
            )
        )
        return result if isinstance(result, dict) else self._empty_interruption_count()

    def get_interruption_stats(
        self,
        *,
        witty_agent_id: str | None = None,
        start_ns: int | None = None,
        end_ns: int | None = None,
    ) -> list[dict[str, Any]]:
        runtime_session_ids = self._list_managed_runtime_session_ids(witty_agent_id=witty_agent_id)
        if not runtime_session_ids:
            return []
        result = self._services.get_insight_client().get_interruption_stats(
            self._raw_params(
                start_ns=start_ns,
                end_ns=end_ns,
                session_ids=runtime_session_ids,
            )
        )
        return result if isinstance(result, list) else []

    def get_interruption_session_counts(
        self,
        *,
        witty_agent_id: str | None = None,
        start_ns: int | None = None,
        end_ns: int | None = None,
    ) -> list[dict[str, Any]]:
        runtime_session_ids = self._list_managed_runtime_session_ids(witty_agent_id=witty_agent_id)
        if not runtime_session_ids:
            return []

        result = self._services.get_insight_client().get_interruption_session_counts(
            self._raw_params(
                start_ns=start_ns,
                end_ns=end_ns,
                session_ids=runtime_session_ids,
            )
        )
        if not isinstance(result, list):
            return []

        session_by_runtime_id = {
            session.runtime_session_id: session
            for session in self._repository.list_sessions_by_runtime_session_ids(
                _RUNTIME_TYPE,
                [item.get("session_id") for item in result if isinstance(item, dict) and isinstance(item.get("session_id"), str)],
            )
            if session.runtime_session_id is not None
        }

        remapped: list[dict[str, Any]] = []
        for item in result:
            if not isinstance(item, dict):
                continue
            runtime_session_id = item.get("session_id")
            if not isinstance(runtime_session_id, str):
                continue
            session = session_by_runtime_id.get(runtime_session_id)
            if session is None:
                continue
            remapped.append(
                {
                    "session_id": session.id,
                    "runtime_session_id": runtime_session_id,
                    "total": int(item.get("total", 0) or 0),
                    "by_severity": self._normalize_severity_counts(item.get("by_severity")),
                    "types": item.get("types") if isinstance(item.get("types"), list) else [],
                }
            )
        return remapped

    def get_interruption_conversation_counts(
        self,
        *,
        witty_agent_id: str | None = None,
        start_ns: int | None = None,
        end_ns: int | None = None,
    ) -> list[dict[str, Any]]:
        runtime_session_ids = self._list_managed_runtime_session_ids(witty_agent_id=witty_agent_id)
        if not runtime_session_ids:
            return []
        result = self._services.get_insight_client().get_interruption_conversation_counts(
            self._raw_params(
                start_ns=start_ns,
                end_ns=end_ns,
                session_ids=runtime_session_ids,
            )
        )
        return result if isinstance(result, list) else []

    def delete_agent_health(self, pid: int) -> dict[str, Any]:
        result = self._services.get_insight_client().delete_agent_health(pid)
        return result if isinstance(result, dict) else {"ok": True}

    def restart_agent_health(self, pid: int) -> dict[str, Any]:
        result = self._services.get_insight_client().restart_agent_health(pid)
        return result if isinstance(result, dict) else {"ok": True, "new_pid": 0, "cmd": []}

    def export_atif_session(self, witty_session_id: str) -> dict[str, Any]:
        session = self._require_runtime_session(witty_session_id)
        result = self._services.get_insight_client().export_atif_session(session.runtime_session_id)
        if not isinstance(result, dict):
            return {}
        document = dict(result)
        document["session_id"] = session.id
        document["runtime_session_id"] = session.runtime_session_id
        return document

    def export_atif_conversation(self, conversation_id: str) -> dict[str, Any]:
        result = self._services.get_insight_client().export_atif_conversation(conversation_id)
        return result if isinstance(result, dict) else {}

    def get_agent_health(self) -> dict[str, Any]:
        raw_result = self._services.get_insight_client().get_agent_health()
        raw_agents = raw_result.get("agents") if isinstance(raw_result, dict) else []
        runtimes = [
            self._normalize_runtime_health(item)
            for item in raw_agents
            if isinstance(item, dict)
        ]
        managed_records = self._repository.list_agents_with_runtime_state()

        agents: list[dict[str, Any]] = []
        matched_runtime_pids: set[int] = set()
        for record in managed_records:
            candidates = self._find_runtime_candidates(record, runtimes)
            matched_runtime_pids.update(
                runtime["pid"]
                for runtime in candidates
                if isinstance(runtime.get("pid"), int)
            )
            agents.append(self._build_managed_health_entry(record, candidates))

        orphan_runtimes = [
            runtime
            for runtime in runtimes
            if not isinstance(runtime.get("pid"), int) or runtime["pid"] not in matched_runtime_pids
        ]
        return {
            "agents": agents,
            "orphan_runtimes": orphan_runtimes,
            "last_scan_time": int(raw_result.get("last_scan_time", 0) or 0)
            if isinstance(raw_result, dict)
            else 0,
        }

    @staticmethod
    def _feature_flags(enabled: bool) -> dict[str, bool]:
        return {
            "sessions": enabled,
            "timeseries": enabled,
            "interruptions": enabled,
            "health": enabled,
        }

    @staticmethod
    def _raw_params(
        *,
        start_ns: int | None = None,
        end_ns: int | None = None,
        buckets: int | None = None,
        session_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if start_ns is not None:
            params["start_ns"] = start_ns
        if end_ns is not None:
            params["end_ns"] = end_ns
        if buckets is not None:
            params["buckets"] = buckets
        if session_ids:
            if len(session_ids) == 1:
                params["session_id"] = session_ids[0]
            else:
                params["session_ids"] = session_ids
        return params

    def _require_runtime_session(self, witty_session_id: str) -> SessionRecord:
        session = self._repository.get_session(witty_session_id)
        if (
            session is None
            or session.runtime_type != _RUNTIME_TYPE
            or not session.runtime_session_id
        ):
            raise insight_session_mapping_not_found(
                session_id=witty_session_id,
                runtime_type=None if session is None else session.runtime_type,
                runtime_session_id=None if session is None else session.runtime_session_id,
            )
        return session

    def _remap_interruption_records(self, records: list[Any]) -> list[dict[str, Any]]:
        runtime_session_ids = [
            item.get("session_id")
            for item in records
            if isinstance(item, dict) and isinstance(item.get("session_id"), str)
        ]
        sessions_by_runtime_id = {
            session.runtime_session_id: session
            for session in self._repository.list_sessions_by_runtime_session_ids(
                _RUNTIME_TYPE,
                runtime_session_ids,
            )
            if session.runtime_session_id is not None
        }

        remapped: list[dict[str, Any]] = []
        for item in records:
            if not isinstance(item, dict):
                continue
            payload = dict(item)
            runtime_session_id = payload.get("session_id")
            if isinstance(runtime_session_id, str):
                session = sessions_by_runtime_id.get(runtime_session_id)
                if session is not None:
                    payload["session_id"] = session.id
                    payload["runtime_session_id"] = runtime_session_id
            remapped.append(payload)
        return remapped

    def _list_managed_runtime_session_ids(
        self,
        *,
        witty_agent_id: str | None = None,
    ) -> list[str]:
        if witty_agent_id:
            return self._repository.list_runtime_session_ids_by_agent_id(
                witty_agent_id,
                runtime_type=_RUNTIME_TYPE,
            )

        runtime_session_ids: list[str] = []
        for agent in self._repository.list_agents():
            runtime_session_ids.extend(
                self._repository.list_runtime_session_ids_by_agent_id(
                    agent.id,
                    runtime_type=_RUNTIME_TYPE,
                )
            )
        return self._dedupe_preserve_order(runtime_session_ids)

    def _find_runtime_candidates(
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

    def _build_managed_health_entry(
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
        overall_status, status_reason = self._overall_health_status(
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
    def _overall_health_status(
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
    def _normalize_runtime_health(item: dict[str, Any]) -> dict[str, Any]:
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
    def _normalize_severity_counts(raw: Any) -> dict[str, int]:
        data = raw if isinstance(raw, dict) else {}
        return {
            severity: int(data.get(severity, 0) or 0)
            for severity in _INTERRUPTION_SEVERITIES
        }

    @staticmethod
    def _empty_interruption_count() -> dict[str, Any]:
        return {
            "total": 0,
            "by_severity": {
                severity: 0
                for severity in _INTERRUPTION_SEVERITIES
            },
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

    @staticmethod
    def _dedupe_preserve_order(values: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            ordered.append(value)
        return ordered
