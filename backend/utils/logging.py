import logging
import sys
from backend.config.settings import get_settings

def setup_logging():
    """Setup structured logging for the application"""
    settings = get_settings()
    
    # Suppress noisy loggers more aggressively
    noisy_loggers = [
        "prefect",
        "prefect.events", 
        "prefect.task_engine",
        "prefect._internal.concurrency",
        "prefect._internal.services",
        "prefect.events.worker",
        "prefect._internal.events",
        "prefect.engine",
        "prefect.client",
        "prefect.flows",
        "prefect.tasks",
        "langchain_google_genai",
        "tzlocal",
        "httpx",
        "httpcore"
    ]
    
    for logger_name in noisy_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)
        logger.disabled = True
    
    # Configure main logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)