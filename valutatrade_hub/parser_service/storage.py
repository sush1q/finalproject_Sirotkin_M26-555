from datetime import datetime, timezone

from valutatrade_hub.core import currencies, exceptions, utils
from valutatrade_hub.infra.database import load_metadata, save_metadata
from valutatrade_hub.parser_service.config import ParserConfig


class RatesStorage:
    def __init__(self, config=None):
        self.config = config if config is not None else ParserConfig()

    def _create_record(self, pair, data):
        '''Проверить измерение и подготовить запись истории в UTC.'''
        try:
            original, target = pair.split('_')
            currencies.get_currency(original)
            currencies.get_currency(target)
            rate = data['rate']
            if not utils.is_positive(rate):
                raise ValueError('Курс должен быть положительным')
            date = datetime.fromisoformat(data['updated_at'])
            if date.utcoffset() is None:
                raise ValueError('У времени должен быть указан часовой пояс')
            timestamp = date.astimezone(timezone.utc).isoformat()
            source = data['source']
            if not isinstance(source, str) or not source.strip():
                raise ValueError('Источник не указан')
        except (KeyError, TypeError, ValueError, exceptions.CurrencyNotFoundError) as e:
            raise exceptions.ValutaTradeExceptions(
                f'Некорректное измерение {pair}: {e}'
            ) from e
        return {
            'id': f'{pair}_{timestamp}',
            'from_currency': original,
            'to_currency': target,
            'rate': float(rate),
            'timestamp': timestamp,
            'source': source,
        }

    def _is_newer(self, timestamp, previous_timestamp):
        try:
            current = datetime.fromisoformat(timestamp)
            previous = datetime.fromisoformat(previous_timestamp)
            return current > previous
        except (TypeError, ValueError):
            return True

    def save_rates(self, pairs, last_refresh):
        # Подготовить новые записи до изменения файлов.
        try:
            refresh = datetime.fromisoformat(last_refresh)
            if refresh.utcoffset() is None:
                raise ValueError('Часовой пояс last_refresh не указан')
            last_refresh = refresh.astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError) as e:
            raise exceptions.ValutaTradeExceptions('Некорректный last_refresh') from e
        records = []
        for pair, data in pairs.items():
            records.append(self._create_record(pair, data))

        # Прочитать снимок и историю.
        cache = load_metadata(
            self.config.RATES_FILE_PATH, {'pairs': {}, 'last_refresh': None}
        )
        history = load_metadata(self.config.HISTORY_FILE_PATH, [])
        if not isinstance(cache, dict) or not isinstance(cache.get('pairs'), dict):
            raise exceptions.ValutaTradeExceptions('Некорректный формат rates.json')
        if not isinstance(history, list):
            raise exceptions.ValutaTradeExceptions('Некорректный формат истории курсов')
        try:
            known_ids = {record['id'] for record in history}
        except (KeyError, TypeError) as e:
            raise exceptions.ValutaTradeExceptions('Некорректная запись истории') from e

        # Добавить измерения в историю и заменить только более свежие пары.
        updated_count = 0
        for record in records:
            if record['id'] not in known_ids:
                history.append(record)
                known_ids.add(record['id'])
            pair = f'{record['from_currency']}_{record['to_currency']}'
            previous = cache['pairs'].get(pair)
            previous_timestamp = None
            if isinstance(previous, dict):
                previous_timestamp = previous.get('updated_at')
            if self._is_newer(record['timestamp'], previous_timestamp):
                cache['pairs'][pair] = {
                    'rate': record['rate'],
                    'updated_at': record['timestamp'],
                    'source': record['source'],
                }
                updated_count += 1

        if updated_count and self._is_newer(last_refresh, cache.get('last_refresh')):
            cache['last_refresh'] = last_refresh
        save_metadata(self.config.HISTORY_FILE_PATH, history)
        save_metadata(self.config.RATES_FILE_PATH, cache)
        return {
            'updated_count': updated_count,
            'last_refresh': cache.get('last_refresh'),
        }
