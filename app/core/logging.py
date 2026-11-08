"""Structured logging configuration with credential masking."""
import logging
import sys
import re
from typing import Any, Dict


SENSITIVE_PATTERNS = [
    re.compile(r'(password["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE),
    re.compile(r'(token["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE),
    re.compile(r'(authorization["\']?\s*[:=]\s*["\']bearer\s+)([^"\']+)(["\'])', re.IGNORECASE),
    re.compile(r'(secret["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE),
]


class SensitiveMaskingFormatter(logging.Formatter):
    """Formatter that redacts sensitive strings like passwords and tokens."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        masked = original
        for pattern in SENSITIVE_PATTERNS:
            masked = pattern.sub(r"\1***REDACTED***\3", masked)
        return masked


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Initialize structured application logging."""
    logger = logging.getLogger("telecom_connect")
    logger.setLevel(level)

    # Avoid duplicate handlers if reloaded
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = SensitiveMaskingFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()
