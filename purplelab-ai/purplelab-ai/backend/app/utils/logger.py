"""
utils/logger.py
=================
One-line logging setup shared across the app. Kept deliberately simple -
this is a lab tool, not a production service, so we log to stdout only.
"""
import logging


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
