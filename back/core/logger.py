import logging
import os

from dotenv import load_dotenv
from uvicorn.logging import DefaultFormatter

load_dotenv()

levels = {
    'none': logging.NOTSET,
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}

def get_logger(name: str, file: str, level: str|None = None) -> logging.Logger:
    if level is None or level not in levels:
        level = os.getenv('LOG_LEVEL','warning')

    logger = logging.getLogger(name)

    file_handler = logging.FileHandler(f"logs/{file}.log", mode="a", encoding="utf-8")
    console_handler = logging.StreamHandler()

    file_formatter = logging.Formatter(
    "{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
    )

    # Formatter console : celui d'uvicorn, avec le même pattern que "uvicorn.error"
    console_formatter = DefaultFormatter(
        fmt="%(levelprefix)s %(message)s",
        use_colors=True,  # None = auto-détection du tty, True = forcé
    )

    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(levels[level])
    return logger