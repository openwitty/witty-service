"""Witty Service package."""

__all__ = ["create_app"]


def __getattr__(name: str):
    if name == "create_app":
        from witty_service.main import create_app

        return create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")