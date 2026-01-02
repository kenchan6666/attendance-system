import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "access": {
            "format": "[%(asctime)s] %(client_addr)s - %(method)s %(path)s - %(status_code)s - %(duration)sms",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO"
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "logs/attendance_api.log",
            "formatter": "default",
            "level": "DEBUG"
        }
    },
    "loggers": {
        "attendance_system": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False
        },
        "uvicorn": {
            "handlers": ["console"],
            "level": "INFO"
        }
    }
}

def setup_logging():
    """初始化日志配置"""
    try:
        logging.config.dictConfig(LOGGING_CONFIG)
    except Exception as e:
        # 备用方案
        import os
        os.makedirs("logs", exist_ok=True)
        logging.config.dictConfig(LOGGING_CONFIG)

# 初始化
setup_logging()
logger = logging.getLogger("attendance_system")
