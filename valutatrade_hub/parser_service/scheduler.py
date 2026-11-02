import time

from valutatrade_hub import logging_config
from valutatrade_hub.core import exceptions, utils
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.updater import create_updater


def run(interval=None, updater=None):
    if interval is None:
        interval = ParserConfig().UPDATE_INTERVAL
    if not utils.is_positive(interval):
        raise exceptions.ValutaTradeExceptions('Интервал должен быть положительным')
    if updater is None:
        updater = create_updater()
    logger = logging_config.get_parser_logger()
    while True:
        try:
            updater.run_update()
        except exceptions.ApiRequestError:
            logger.exception('Scheduled update failed')
        time.sleep(interval)


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        pass
