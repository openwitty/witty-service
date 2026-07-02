from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from witty_agent_server.application.services.skill.openclaw_skill_client import (
    OpenClawSkillClient,
)
from witty_agent_server.application.services.skill.skill_client_port import (
    SkillClientPort,
)


def _make_gateway() -> MagicMock:
    gw = MagicMock()
    gw.get_skills_status.return_value = {"skills": []}
    gw.install_skill.return_value = {"ok": True}
    gw.uninstall_skill.return_value = {"ok": True}
    return gw


def test_openclaw_skill_client_satisfies_port() -> None:
    client = OpenClawSkillClient(gateway_client=_make_gateway())
    assert isinstance(client, SkillClientPort)


def test_get_skills_status_delegates() -> None:
    gw = _make_gateway()
    client = OpenClawSkillClient(gateway_client=gw)
    client.get_skills_status(agent_id="a1")
    gw.get_skills_status.assert_called_once_with(agent_id="a1")


def test_install_skill_delegates() -> None:
    gw = _make_gateway()
    client = OpenClawSkillClient(gateway_client=gw)
    result = client.install_skill(skill_name="s", agent_id="a1", version="v", force=True)
    gw.install_skill.assert_called_once_with(
        skill_name="s", agent_id="a1", version="v", force=True
    )
    assert result == {"ok": True}


def test_enable_skill_delegates() -> None:
    gw = _make_gateway()
    client = OpenClawSkillClient(gateway_client=gw)
    client.enable_skill(skill_name="s", agent_id="a1")
    gw.enable_skill.assert_called_once_with(skill_name="s", agent_id="a1")


def test_uninstall_skill_delegates() -> None:
    gw = _make_gateway()
    client = OpenClawSkillClient(gateway_client=gw)
    result = client.uninstall_skill(skill_name="s", agent_id="a1")
    gw.uninstall_skill.assert_called_once_with(skill_name="s", agent_id="a1")
    assert result == {"ok": True}
