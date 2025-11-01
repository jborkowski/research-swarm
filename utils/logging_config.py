import logging
import sys
from pythonjsonlogger import jsonlogger


def setup_logging(app_name: str = "research-swarm", log_level: str = "INFO"):
    """Configure structured JSON logging."""

    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper()))

    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        from pathlib import Path
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(log_dir / f"{app_name}.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not set up file logging: {e}")

    return logger
