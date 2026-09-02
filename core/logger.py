import logging
import os

from dotenv import load_dotenv

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
    logger.addHandler(file_handler)
    formatter = logging.Formatter(
    "{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
    )
    file_handler.setFormatter(formatter)
    logger.setLevel(levels[level])
    return logger