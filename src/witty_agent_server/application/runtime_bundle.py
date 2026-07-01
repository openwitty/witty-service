from __future__ import annotations

from dataclasses import dataclass

from witty_agent_server.application.materialization.ports import SpecMaterializerPort
from witty_agent_server.application.services.agent.base import (
    AgentServiceBase,
    RuntimeLifecyclePort,
)
from witty_agent_server.application.services.skill.base import AgentSkillServiceBase
from witty_agent_server.application.services.session.base import SessionServiceBase
from witty_agent_server.runtimes.runtime_base import RuntimeBase, RuntimeType


@dataclass(slots=True)
class RuntimeBundle:
    """单个 runtime 的装配单元，聚合该 runtime 所需的全部服务组件。"""

    runtime_type: RuntimeType
    runtime: RuntimeBase
    agent_service: AgentServiceBase
    session_service: SessionServiceBase
    skill_service: AgentSkillServiceBase
    lifecycle_service: RuntimeLifecyclePort | None = None
    materializer: SpecMaterializerPort | None = None


__all__ = ["RuntimeBundle"]
