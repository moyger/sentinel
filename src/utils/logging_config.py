"""
Logging configuration for Sentinel.

Provides structured logging with file rotation and console output.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

import structlog

from .config import config


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Optional log level override (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Ensure logs directory exists
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Determine log level
    level = log_level or config.LOG_LEVEL
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=numeric_level,
        handlers=[],  # We'll add handlers manually
    )

    # Create file handler with rotation
    file_handler = RotatingFileHandler(
        filename=config.LOG_FILE_PATH,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Create formatters
    file_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
    )

    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=True),
    )

    # Assign formatters to handlers
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    # Add handlers to root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("slack_sdk").setLevel(logging.WARNING)
    logging.getLogger("slack_bolt").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("google.auth").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Name of the logger (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


# Convenience function for quick logging setup
def init_logging() -> structlog.stdlib.BoundLogger:
    """
    Initialize logging and return a logger instance.

    Returns:
        Configured logger for the main application
    """
    setup_logging()
    logger = get_logger("sentinel")
    logger.info("Logging initialized", log_level=config.LOG_LEVEL, log_file=str(config.LOG_FILE_PATH))
    return logger
