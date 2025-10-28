import logger
import logging.config
import sys

def setup_logging(level: int = logging.INFO) -> None:
    """
    Thiết lập logging thống nhất cho toàn backend:
    - Format có màu khi chạy terminal.
    - Đồng bộ luôn cả log của Uvicorn.
    - Giữ output rõ ràng, dễ đọc.
    """
    # ---- Formatter có màu (tự động tắt khi redirect ra file) ----
    class ColorFormatter(logging.Formatter):
        COLORS = {
            "DEBUG": "\033[37m",   # Gray
            "INFO": "\033[36m",    # Cyan
            "WARNING": "\033[33m", # Yellow
            "ERROR": "\033[31m",   # Red
            "CRITICAL": "\033[41m" # Red background
        }
        RESET = "\033[0m"

        def format(self, record):
            color = self.COLORS.get(record.levelname, self.RESET)
            message = super().format(record)
            return f"{color}{message}{self.RESET}"

    formatter = ColorFormatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # ---- Cấu hình dictConfig để đồng bộ với Uvicorn ----
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"default": {"format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"}},
        "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
        "loggers": {
            "": {"handlers": ["console"], "level": level},
            "uvicorn": {"handlers": ["console"], "level": level, "propagate": False},
            "uvicorn.error": {"handlers": ["console"], "level": level, "propagate": False},
            "uvicorn.access": {"handlers": ["console"], "level": level, "propagate": False},
        },
    }

    logging.config.dictConfig(logging_config)
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(level)

    # ---- Log khởi động ----
    root_logger.info("✅ Logging system initialized.")
