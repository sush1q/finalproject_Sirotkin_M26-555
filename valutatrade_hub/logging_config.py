import logging
import time
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

from valutatrade_hub.core import exceptions
from valutatrade_hub.infra import settings

LOGGER_NAME = 'valutatrade.actions'
PARSER_LOGGER_NAME = 'valutatrade.parser'

def setup_logging():
    '''Настраивает логирование с заданными форматом и ротацией'''
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
    '''Возвращает логгер, при необходимости настраивая его'''
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        return setup_logging()
    return logger

def get_parser_logger():
    '''Возвращает файловый DEBUG-логгер использующийся для модуля парсинга'''
    logger = logging.getLogger(PARSER_LOGGER_NAME)
    if logger.handlers:
        return logger
    config = settings.SettingsLoader()
    try:
        path = Path(config.get('log_path', 'logs')) / 'parser.log'
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            path, maxBytes=config.get('log_max_bytes', 1000000),
            backupCount=config.get('log_backup_count', 3), encoding='utf-8',
        )
    except OSError as e:
        raise exceptions.ValutaTradeExceptions(
            f'Не удалось настроить журнал Parser: {e}'
        ) from e
    formatter = logging.Formatter(
        '%(asctime)sZ %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S',
    )
    formatter.converter = time.gmtime
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.propagate = False
    return logger

@contextmanager
def parser_console():
    logger = get_parser_logger()
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(handler)
    try:
        yield
    finally:
        logger.removeHandler(handler)
        handler.close()
