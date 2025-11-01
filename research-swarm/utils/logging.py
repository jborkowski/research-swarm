import logging
import sys
from pythonjsonlogger import jsonlogger
from datetime import datetime

def setup_logging(app_name: str = "research-swarm"):
    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.INFO)
    
    # JSON formatter
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(f"/logs/{app_name}.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()