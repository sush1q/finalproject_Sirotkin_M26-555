import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from valutatrade_hub.core import exceptions
from valutatrade_hub.infra import settings

LOGGER_NAME = 'valutatrade.actions'

def setup_logging():
    config = settings.SettingsLoader()
    logger = logging.getLogger(LOGGER_NAME)
    try:
        logger.setLevel(config.get('log_level', 'INFO'))
        path = Path(config.get('log_path', 'logs')) / 'actions.log'
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            path,
            maxBytes=config.get('log_max_bytes', 1000000),
            backupCount=config.get('log_backup_count', 3),
            encoding='utf-8',
        )
        handler.setFormatter(logging.Formatter(
            config.get('log_format', '%(levelname)s %(message)s')
        ))
    except (OSError, TypeError, ValueError) as e:
        raise exceptions.ValutaTradeExceptions(
            f'Не удалось настроить журнал действий: {e}'
        ) from e
    for previous in logger.handlers[:]:
        logger.removeHandler(previous)
        previous.close()
    logger.addHandler(handler)
    logger.propagate = False
    return logger

def get_logger():
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        return setup_logging()
    return logger
