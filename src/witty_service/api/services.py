from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from witty_service.adapter.insight_client import InsightClient
from witty_service.adapter.websocket_client_pool import WebSocketClientPool
from witty_service.application.agent_manager import AGENT_NOT_FOUND, AgentManager
from witty_service.application.session_manager import SessionManager
from witty_service.config import get_settings
from witty_service.domain.errors import DomainError, insight_disabled
from witty_service.persistence.db import create_session_factory, create_sqlite_engine, init_db
from witty_service.persistence.repositories import SqliteRepository
from witty_service.sandbox.base import SandboxBackend
from witty_service.sandbox.factory import create_sandbox_backend
from witty_service.storage.workspace_store import LocalWorkspaceStore, WorkspaceStore


@dataclass(slots=True)
class ServiceContainer:
    repository: SqliteRepository
    workspace_store: WorkspaceStore
    sandbox_backends: dict[str, SandboxBackend] = field(default_factory=dict)
    ws_client_pool: WebSocketClientPool = field(default_factory=WebSocketClientPool)
    insight_client: InsightClient | None = None
    session_manager: SessionManager = field(init=False)

    def __post_init__(self) -> None:
        self.session_manager = SessionManager(repository=self.repository)

    def get_sandbox_backend(self, sandbox_type: str) -> SandboxBackend:
        key = sandbox_type.lower()
        backend = self.sandbox_backends.get(key)
        if backend is None:
            backend = create_sandbox_backend(key)
            self.sandbox_backends[key] = backend
        return backend

    def get_agent_manager_for_sandbox(self, sandbox_type: str) -> AgentManager:
        return AgentManager(
            repository=self.repository,
            session_manager=self.session_manager,
            workspace_store=self.workspace_store,
            sandbox_backend=self.get_sandbox_backend(sandbox_type),
            ws_client_pool=self.ws_client_pool,
        )

    def get_agent_manager_for_agent(self, agent_id: str) -> AgentManager:
        agent = self.repository.get_agent(agent_id)
        if agent is None:
            raise DomainError(
                code=AGENT_NOT_FOUND,
                message="Agent was not found.",
                details={"agent_id": agent_id},
        )
        return self.get_agent_manager_for_sandbox(agent.sandbox_type)

    def get_insight_client(self) -> InsightClient:
        if self.insight_client is None:
            raise insight_disabled()
        return self.insight_client


def _ensure_dir_exists(database_url: str) -> None:
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)


def build_default_services() -> ServiceContainer:
    settings = get_settings()
    database_url = settings.database.url
    workspace_root = settings.workspace.root
    insight_settings = settings.insight

    _ensure_dir_exists(database_url)
    engine = create_sqlite_engine(database_url)
    init_db(engine)

    insight_client = None
    if insight_settings.enabled:
        insight_client = InsightClient(
            base_url=insight_settings.base_url,
            timeout_seconds=insight_settings.timeout_seconds,
            bearer_token=insight_settings.bearer_token,
        )

    return ServiceContainer(
        repository=SqliteRepository(create_session_factory(engine)),
        workspace_store=LocalWorkspaceStore(base_path=workspace_root),
        insight_client=insight_client,
    )
