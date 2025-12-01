import logging
from typing import Optional


def get_logger(name: str = "swift") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def redact(text: str, enabled: bool = True) -> str:
    if not enabled:
        return text
    # Very lightweight redaction: replace email-like patterns
    return text.replace("@", "[at]").replace(".", "[dot]")
