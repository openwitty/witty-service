from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from witty_service.config import get_settings


def configure_logging() -> None:
    """统一配置日志系统。"""
    settings = get_settings()
    level_name = settings.logging.level
    level = getattr(logging, level_name, logging.INFO)
    
    root_logger = logging.getLogger()
    
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z"
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)
    
    log_file = settings.logging.file
    if log_file:
        Path(log_file).expanduser().parent.mkdir(parents=True, exist_ok=True)
        max_bytes = settings.logging.max_bytes
        backup_count = settings.logging.backup_count
        
        file_handler = RotatingFileHandler(
            str(Path(log_file).expanduser()),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)
    
    root_logger.setLevel(level)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


class LoggerAdapter(logging.LoggerAdapter):
    """增强的日志适配器，支持上下文信息注入。"""
    
    def __init__(self, logger: logging.Logger, extra: dict[str, Any]) -> None:
        super().__init__(logger, extra)
    
    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        context = []
        if self.extra.get("agent_id"):
            context.append(f"agent_id={self.extra['agent_id']}")
        if self.extra.get("session_id"):
            context.append(f"session_id={self.extra['session_id']}")
        if self.extra.get("request_id"):
            context.append(f"request_id={self.extra['request_id']}")
        
        if context:
            msg = f"[{', '.join(context)}] {msg}"
        
        return msg, kwargs


def get_logger(name: str, **extra: Any) -> logging.Logger | LoggerAdapter:
    """获取日志记录器，支持可选的上下文参数。
    
    Args:
        name: 日志记录器名称
        **extra: 上下文参数，如 agent_id, session_id, request_id
    
    Returns:
        LoggerAdapter 如果提供了上下文参数，否则返回标准 Logger
    """
    logger = logging.getLogger(name)
    
    if extra:
        return LoggerAdapter(logger, extra)
    
    return logger