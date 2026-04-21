"""Logging setup for the application process."""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging once (idempotent enough for tests and reloads)."""
    numeric = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(numeric)
        return
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stderr,
    )
