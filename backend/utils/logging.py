import logging
import sys
from datetime import datetime
from pathlib import Path
from backend.config.settings import get_settings

def setup_logging():
    """Setup structured logging for the application with file output"""
    settings = get_settings()
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = logs_dir / f"fintel-backend_{timestamp}.log"
    
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
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(file_formatter)
    
    # Configure main logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))
    root_logger.handlers.clear()  # Clear any existing handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Log the setup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_filename}")
    
    return logger