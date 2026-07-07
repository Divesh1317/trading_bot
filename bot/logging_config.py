from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

# logs/ lives at the project root, one level up from bot/
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "trading_bot.log")

_LOGGER_NAME = "trading_bot"


def setup_logging(console_level: str = "INFO") -> None:
    
    os.makedirs(LOG_DIR, exist_ok=True)

    root_logger = logging.getLogger(_LOGGER_NAME)
    root_logger.setLevel(logging.DEBUG)
    root_logger.propagate = False

    if root_logger.handlers:
        # Already configured (e.g. tests calling this twice) — don't duplicate handlers.
        return

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, console_level.upper(), logging.INFO))
    console_handler.setFormatter(fmt)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
