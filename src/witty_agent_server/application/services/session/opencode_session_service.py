from __future__ import annotations

from witty_agent_server.application.services.session.base import SessionServiceBase


class OpenCodeSessionService(SessionServiceBase):
    """opencode session 服务。

    直接继承 SessionServiceBase 复用通用 create/delete/abort/list 流程；
    runtime 差异由 OpenCodeRuntime 承载。
    """
