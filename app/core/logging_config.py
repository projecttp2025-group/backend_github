from logging.config import dictConfig

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "[{levelname}] {asctime} {name}: {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "file": {
            "format": "{asctime} | {levelname:<8} | {name} | {pathname}:{lineno} | {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "access": {
            "format": "{asctime} | {levelname:<8} | access | {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "console",
        },
        "file_app": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "file",
            "filename": "logs/app.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
        },
        "file_access": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "access",
            "filename": "logs/access.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "app": {
            "handlers": ["console", "file_app"],
            "level": "DEBUG",
            "propagate": False,
        },
        "uvicorn": {"level": "WARNING", "handlers": ["console"], "propagate": False},
        "uvicorn.error": {"level": "WARNING", "handlers": ["console"], "propagate": False},
        "uvicorn.access": {"level": "INFO", "handlers": ["file_access"], "propagate": False},
        "asyncio": {"level": "WARNING", "handlers": ["console"], "propagate": False},
        "passlib": {"level": "WARNING", "handlers": ["console"], "propagate": False},
        "sqlalchemy": {"level": "WARNING", "handlers": ["console"], "propagate": False},
    },
    "root": {
        "level": "WARNING",
        "handlers": ["console"],
    },
}


def setup_logging():
    dictConfig(LOGGING_CONFIG)
