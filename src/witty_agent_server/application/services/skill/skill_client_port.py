from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SkillClientPort(Protocol):
    """技能能力传输端口，屏蔽不同 runtime 的 skills 通信差异。"""

    def get_skills_status(self, *, agent_id: str | None = None) -> dict[str, Any]:
        """查询指定 agent 可见的技能状态。"""
        ...

    def install_skill(
        self,
        *,
        skill_name: str,
        agent_id: str | None = None,
        version: str | None = None,
        force: bool | None = None,
    ) -> dict[str, Any]:
        """安装技能。"""
        ...

    def enable_skill(self, *, skill_name: str, agent_id: str | None = None) -> None:
        """启用技能。"""
        ...

    def uninstall_skill(
        self,
        *,
        skill_name: str,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        """卸载/禁用技能。"""
        ...
