"""
logging_config.py
Sets up logging: DEBUG+ goes to a rotating log file, INFO+ goes to the console.
"""

import logging
import logging.handlers
import os
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "trading_bot.log"


def setup_logging(log_level: str = "DEBUG") -> logging.Logger:
    """
    Configure root logger with:
      - RotatingFileHandler  → logs/trading_bot.log  (DEBUG and above)
      - StreamHandler        → console               (INFO and above)
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers if called more than once
    if root.handlers:
        return logging.getLogger("trading_bot")

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # --- file handler (rotating, max 5 MB × 3 backups) ---
    fh = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # --- console handler ---
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    return logging.getLogger("trading_bot")
