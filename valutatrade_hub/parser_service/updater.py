from datetime import datetime, timezone

from valutatrade_hub import logging_config
from valutatrade_hub.core import currencies, exceptions, utils
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
                if not isinstance(rates, dict) or not rates:
                    raise exceptions.ApiRequestError('Источник вернул пустые курсы')
                if any(not utils.is_positive(rate) for rate in rates.values()):
                    raise exceptions.ApiRequestError('Источник вернул неверные курсы')
                try:
                    for pair in rates:
                        original, target = pair.split('_')
                        currencies.get_currency(original)
                        currencies.get_currency(target)
                except (
                    AttributeError, TypeError, ValueError,
                    exceptions.CurrencyNotFoundError,
                ) as e:
                    raise exceptions.ApiRequestError(
                        f'Источник вернул неверную валютную пару: {e}'
                    ) from e
                timestamp = datetime.now(timezone.utc).isoformat()
                timestamp = timestamp.replace('+00:00', 'Z')
                for pair, rate in rates.items():
                    pairs[pair] = {
                        'rate': rate, 'updated_at': timestamp,
                        'source': client.source,
                    }
                logger.info(
                    'Fetching from %s... OK (%s rates)', client.source, len(rates)
                )
            except exceptions.ApiRequestError as e:
                errors.append({'source': client.source, 'message': str(e)})
                logger.exception('Failed to fetch from %s: %s', client.source, e)
        if not pairs:
            logger.error('Rates update failed: no successful sources')
            reason = '; '.join(error['message'] for error in errors)
            raise exceptions.ApiRequestError(reason or 'Нет источников курсов')
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
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
    if source not in (None, 'coingecko', 'exchangerate'):
        raise exceptions.ValutaTradeExceptions(
            'Источник должен быть coingecko или exchangerate'
        )
    conf = config.ParserConfig()
    clients = []
    if source in (None, 'coingecko'):
        clients.append(api_clients.CoinGeckoClient(conf))
    if source in (None, 'exchangerate'):
        clients.append(api_clients.ExchangeRateApiClient(conf))
    return RatesUpdater(clients, api_clients.RatesStorage(conf))
