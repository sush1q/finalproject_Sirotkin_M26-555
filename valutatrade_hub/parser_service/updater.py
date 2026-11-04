from datetime import datetime, timezone

from valutatrade_hub import logging_config
from valutatrade_hub.core import exceptions
from valutatrade_hub.parser_service import api_clients, config, storage


class RatesUpdater:
    def __init__(self, clients, storage):
        self.clients = clients
        self.storage = storage

    def run_update(self):
        logger = logging_config.get_parser_logger()
        logger.info('Starting rates update...')
        pairs = {}
        errors = []
        for client in self.clients:
            try:
                rates = client.fetch_rates()
                if not rates:
                    raise exceptions.ApiRequestError('Источник вернул пустые курсы')
            except exceptions.ApiRequestError as e:
                errors.append({'source': client.source, 'message': str(e)})
                logger.error('Failed to fetch from %s: %s', client.source, e)
                logger.debug('Client failure details', exc_info=True)
                continue
            timestamp = datetime.now(timezone.utc).isoformat()
            for pair, rate in rates.items():
                pairs[pair] = {
                    'rate': rate,
                    'updated_at': timestamp,
                    'source': client.source,
                }
            logger.info(
                'Fetching from %s... OK (%s rates)', client.source, len(rates)
            )

        if not pairs:
            logger.error('Rates update failed: no successful sources')
            reasons = '; '.join(error['message'] for error in errors)
            raise exceptions.ApiRequestError(reasons or 'Нет источников курсов')
        timestamp = datetime.now(timezone.utc).isoformat()
        logger.info(
            'Writing %s rates to %s...', len(pairs),
            self.storage.config.RATES_FILE_PATH,
        )
        result = self.storage.save_rates(pairs, timestamp)
        result['errors'] = errors
        logger.info(
            'Rates update finished: %s updated, %s errors',
            result['updated_count'], len(errors),
        )
        return result

def create_updater(source=None):
    source = source or None
    if source not in (None, 'coingecko', 'exchangerate'):
        raise exceptions.ValutaTradeExceptions(
            'Источник должен быть coingecko или exchangerate'
        )
    parser_config = config.ParserConfig()
    clients = []
    if source in (None, 'coingecko'):
        clients.append(api_clients.CoinGeckoClient(parser_config))
    if source in (None, 'exchangerate'):
        clients.append(api_clients.ExchangeRateApiClient(parser_config))
    return RatesUpdater(clients, storage.RatesStorage(parser_config))
