import structlog
import logging
import sys
from src.mdb_sync.config import settings

def configure_logging():
    # Use standard logging as the backend for structlog
    log_level = settings.LOG_LEVEL.upper()
    
    # Detect if we should use console or JSON rendering
    use_json = settings.LOG_FORMAT == "json"
    if settings.LOG_FORMAT == "auto":
        use_json = not sys.stdout.isatty()
    
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if use_json:
        # Production: structured JSON
        processors = shared_processors + [
            structlog.processors.JSONRenderer()
        ]
    else:
        # Development: pretty-print to console
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Silence noisy third-party loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)
    logging.getLogger("pyodbc").setLevel(logging.WARNING)

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Returns a module-specific logger."""
    return structlog.get_logger(name)

# Default logger for root-level or legacy imports
logger = structlog.get_logger("mdb_sync")
