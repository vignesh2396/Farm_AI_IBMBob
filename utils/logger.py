"""
utils/logger.py
---------------
Structured logging setup for FarmAI.
Writes to both console and a rotating log file.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from utils.config import config


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger with console + file handlers.

    Args:
        name: Logger name (typically __name__ of calling module)

    Returns:
        Configured Logger instance
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # Already configured; avoid duplicate handlers

    level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating file handler (10 MB max, keep 5 backups)
    log_path = Path(config.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
