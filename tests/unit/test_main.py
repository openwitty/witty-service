from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from witty_service import main as main_module


def test_create_app_closes_services_on_shutdown(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module.SkillManager,
        "sync_awesome_repository_in_background",
        lambda **_kwargs: None,
    )

    services = MagicMock()
    services.repository = MagicMock()
    services.repository.find_stale_generating_messages.return_value = []
    services.repository.list_agents_needing_recovery.return_value = []
    services.close = AsyncMock()

    with TestClient(main_module.create_app(services=services)):
        pass

    services.close.assert_awaited_once_with()
