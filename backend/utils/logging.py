import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.config.settings import get_settings

# In-memory log buffer to expose logs to the frontend
LOG_BUFFER: List[Dict[str, Any]] = []
MAX_BUFFER_SIZE: int = 2000

_LEVEL_MAP = {
    'DEBUG': 0,
    'INFO': 1,
    'WARNING': 2,
    'ERROR': 3,
    'CRITICAL': 4,
}

class InMemoryLogHandler(logging.Handler):
    """A logging handler that stores recent logs in memory for retrieval via API."""
    def emit(self, record: logging.LogRecord) -> None:
        try:
            entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': _LEVEL_MAP.get(record.levelname, 1),
                'level_name': record.levelname,
                'component': record.name,
                'message': record.getMessage(),
            }
            # Optional: attach exception info if present
            if record.exc_info:
                try:
                    formatter = logging.Formatter()
                    entry['error'] = formatter.formatException(record.exc_info)
                except Exception:
                    try:
                        entry['error'] = str(record.exc_info[1])
                    except Exception:
                        entry['error'] = 'Exception'
            LOG_BUFFER.append(entry)
            # cap size
            if len(LOG_BUFFER) > MAX_BUFFER_SIZE:
                del LOG_BUFFER[: len(LOG_BUFFER) - MAX_BUFFER_SIZE]
        except Exception:
            # Never raise from logging
            pass

def get_recent_logs(min_level: Optional[int] = None, component_filter: Optional[str] = None, limit: int = 500) -> List[Dict[str, Any]]:
    """Return recent logs filtered by level and component."""
    items = LOG_BUFFER
    if min_level is not None:
        items = [e for e in items if isinstance(e.get('level'), int) and e['level'] >= min_level]
    if component_filter:
        lowered = component_filter.lower()
        items = [e for e in items if lowered in str(e.get('component', '')).lower()]
    return items[-limit:]

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
    # Add in-memory handler for exposing logs to frontend
    root_logger.addHandler(InMemoryLogHandler())
    
    # Log the setup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_filename}")
    
    return logger