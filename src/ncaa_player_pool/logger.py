"""Logging configuration for NCAA Player Pool application.

This module provides a centralized logging setup with support for both
console and file output. Log files support automatic rotation to prevent
unbounded growth.

The module follows a simple pattern:

- Use `setup_logger()` once at application startup to configure logging
- Use `get_logger()` in modules to retrieve the configured logger

Example:
    Application startup::

        from ncaa_player_pool.logger import setup_logger

        logger = setup_logger(
            name="ncaa_pool",
            level="DEBUG",
            log_file="logs/ncaa_pool.log"
        )
        logger.info("Application started")

    In other modules::

        from ncaa_player_pool.logger import get_logger

        logger = get_logger(__name__)
        logger.debug("Processing data...")

Log Format:
    The default log format includes:
    - Timestamp (YYYY-MM-DD HH:MM:SS)
    - Logger name
    - Log level (padded to 8 characters)
    - Function name and line number
    - Log message

    Example output::

        2026-03-16 14:30:00 | ncaa_pool | INFO     | main:42 | Starting tournament fetch
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(
    name: str = "ncaa_pool",
    level: str = "INFO",
    log_file: str | None = None,
    max_bytes: int = 10_485_760,
    backup_count: int = 5,
) -> logging.Logger:
    """Configure and return a logger with console and optional file output.

    Creates a logger with formatted output to stdout and optionally to a
    rotating log file. The file handler automatically rotates logs when
    they reach the specified size.

    Args:
        name: Logger name, typically the application or module name.
            Defaults to "ncaa_pool".
        level: Minimum logging level as string. One of: DEBUG, INFO,
            WARNING, ERROR, CRITICAL. Defaults to "INFO".
        log_file: Path to log file. If None, only logs to console.
            Parent directories are created automatically.
        max_bytes: Maximum size of each log file in bytes before
            rotation. Defaults to 10MB (10,485,760 bytes).
        backup_count: Number of rotated backup files to retain.
            Defaults to 5 (keeping ncaa_pool.log through ncaa_pool.log.5).

    Returns:
        Configured logging.Logger instance ready for use.

    Note:
        Calling this function multiple times with the same name will
        not add duplicate handlers - existing handlers are preserved.

    Example:
        Basic console-only logging::

            logger = setup_logger("my_app", level="DEBUG")
            logger.debug("This appears on console")

        With file output::

            logger = setup_logger(
                name="my_app",
                level="INFO",
                log_file="logs/app.log",
                max_bytes=5_000_000,  # 5MB
                backup_count=3
            )
            logger.info("This appears on console and in log file")
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Create formatter with comprehensive context
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler with rotation (if log_file specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str = "ncaa_pool") -> logging.Logger:
    """Retrieve an existing logger or create one with default settings.

    This is the primary function for obtaining a logger in application
    modules. If the logger hasn't been configured via `setup_logger()`,
    it will be initialized with default console-only output.

    Args:
        name: Logger name to retrieve. Use `__name__` for module-specific
            loggers, or "ncaa_pool" for the application-wide logger.

    Returns:
        The requested logging.Logger instance.

    Example:
        In a module file::

            from ncaa_player_pool.logger import get_logger

            logger = get_logger(__name__)

            def process_data():
                logger.info("Starting data processing")
                try:
                    # ... processing code ...
                    logger.debug("Processed 100 records")
                except Exception as e:
                    logger.exception(f"Processing failed: {e}")
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
