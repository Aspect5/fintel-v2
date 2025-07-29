import logging
import sys
from config.settings import get_settings

def setup_logging():
    """Setup structured logging for the application"""
    settings = get_settings()
    
    # Suppress noisy loggers
    logging.getLogger("prefect").setLevel(logging.CRITICAL)
    logging.getLogger("prefect.events").setLevel(logging.CRITICAL)
    logging.getLogger("prefect.task_engine").setLevel(logging.CRITICAL)
    logging.getLogger("prefect._internal.concurrency").setLevel(logging.CRITICAL)
    logging.getLogger("prefect._internal.services").setLevel(logging.CRITICAL)
    logging.getLogger("prefect.events.worker").setLevel(logging.CRITICAL)
    logging.getLogger("langchain_google_genai").setLevel(logging.CRITICAL)
    logging.getLogger("tzlocal").setLevel(logging.CRITICAL)
    
    # Configure main logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)