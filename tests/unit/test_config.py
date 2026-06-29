from __future__ import annotations

import witty_service.config as config_module


def _clear_insight_env(monkeypatch) -> None:
    for key in (
        "WITTY_INSIGHT_ENABLED",
        "WITTY_INSIGHT_BASE_URL",
        "WITTY_INSIGHT_TIMEOUT_SECONDS",
        "WITTY_INSIGHT_BEARER_TOKEN",
    ):
        monkeypatch.delenv(key, raising=False)


def test_insight_settings_defaults(monkeypatch) -> None:
    _clear_insight_env(monkeypatch)

    settings = config_module.InsightSettings.from_env()

    assert settings.enabled is False
    assert settings.base_url == "http://127.0.0.1:7396"
    assert settings.timeout_seconds == 10.0
    assert settings.bearer_token is None


def test_insight_settings_reads_env(monkeypatch) -> None:
    monkeypatch.setenv("WITTY_INSIGHT_ENABLED", "true")
    monkeypatch.setenv("WITTY_INSIGHT_BASE_URL", "http://10.0.0.8:7396")
    monkeypatch.setenv("WITTY_INSIGHT_TIMEOUT_SECONDS", "3.5")
    monkeypatch.setenv("WITTY_INSIGHT_BEARER_TOKEN", "secret-token")

    settings = config_module.InsightSettings.from_env()

    assert settings.enabled is True
    assert settings.base_url == "http://10.0.0.8:7396"
    assert settings.timeout_seconds == 3.5
    assert settings.bearer_token == "secret-token"


def test_insight_settings_normalizes_blank_token_to_none(monkeypatch) -> None:
    monkeypatch.setenv("WITTY_INSIGHT_BEARER_TOKEN", "   ")

    settings = config_module.InsightSettings.from_env()

    assert settings.bearer_token is None


def test_settings_from_env_includes_insight_settings(monkeypatch) -> None:
    monkeypatch.setenv("WITTY_INSIGHT_ENABLED", "true")
    monkeypatch.setenv("WITTY_INSIGHT_BASE_URL", "http://insight.internal:7396")

    settings = config_module.Settings.from_env()

    assert settings.insight.enabled is True
    assert settings.insight.base_url == "http://insight.internal:7396"
