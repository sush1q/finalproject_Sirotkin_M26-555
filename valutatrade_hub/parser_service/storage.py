from datetime import datetime, timezone

from valutatrade_hub.core import currencies, exceptions, utils
from valutatrade_hub.infra.database import load_metadata, save_metadata
from valutatrade_hub.parser_service.config import ParserConfig


class RatesStorage:
    def __init__(self, config=None):
        self.config = config if config is not None else ParserConfig()

    def save_rates(self, pairs, last_refresh):
        try:
            refresh = datetime.fromisoformat(last_refresh)
            if refresh.utcoffset() is None:
                raise exceptions.ValutaTradeExceptions('Часовой пояс last_refresh не указан')
            last_refresh = refresh.astimezone(timezone.utc).isoformat()
            last_refresh = last_refresh.replace('+00:00', 'Z')
        except (TypeError, ValueError) as e:
            raise exceptions.ValutaTradeExceptions('Некорректный last_refresh') from e
        records = []
        for pair, data in pairs.items():
            try:
                original, target = pair.split('_')
                currencies.get_currency(original)
                currencies.get_currency(target)
                if not utils.is_positive(data['rate']):
                    raise exceptions.ValutaTradeExceptions('Курс должен быть положительным')
                date = datetime.fromisoformat(data['updated_at'])
                if date.utcoffset() is None:
                    raise exceptions.ValutaTradeExceptions('У времени должен быть указан часовой пояс')
                timestamp = date.astimezone(timezone.utc).isoformat()
                timestamp = timestamp.replace('+00:00', 'Z')
                source = data['source']
                if not isinstance(source, str) or not source.strip():
                    raise exceptions.ValutaTradeExceptions('Источник не указан')
                records.append({
                    'id': f'{pair}_{timestamp}',
                    'from_currency': original,
                    'to_currency': target,
                    'rate': float(data['rate']),
                    'timestamp': timestamp,
                    'source': source,
                })
            except (
                KeyError, TypeError, ValueError, exceptions.CurrencyNotFoundError
            ) as e:
                raise exceptions.ValutaTradeExceptions(
                    f'Некорректное измерение {pair}: {e}'
                ) from e
        cache = load_metadata(
            self.config.RATES_FILE_PATH, {'pairs': {}, 'last_refresh': None}
        )
        history = load_metadata(self.config.HISTORY_FILE_PATH, [])
        if not isinstance(cache, dict) or not isinstance(cache.get('pairs'), dict):
            raise exceptions.ValutaTradeExceptions('Некорректный формат rates.json')
        if not isinstance(history, list) or any(
            not isinstance(row, dict) for row in history
        ):
            raise exceptions.ValutaTradeExceptions('Некорректный формат истории курсов')
        ids = {record.get('id') for record in history}
        updated_count = 0
        for record in records:
            if record['id'] not in ids:
                history.append(record)
                ids.add(record['id'])
            pair = f'{record['from_currency']}_{record['to_currency']}'
            previous = cache['pairs'].get(pair)
            try:
                previous_time = datetime.fromisoformat(previous['updated_at'])
                newer = datetime.fromisoformat(record['timestamp']) > previous_time
            except (KeyError, TypeError, ValueError):
                newer = True
            if newer:
                cache['pairs'][pair] = {
                    'rate': record['rate'], 'updated_at': record['timestamp'],
                    'source': record['source'],
                }
                updated_count += 1
        if updated_count:
            previous_refresh = cache.get('last_refresh')
            try:
                newer_refresh = refresh > datetime.fromisoformat(previous_refresh)
            except (TypeError, ValueError):
                newer_refresh = True
            if newer_refresh:
                cache['last_refresh'] = last_refresh
        save_metadata(self.config.HISTORY_FILE_PATH, history)
        save_metadata(self.config.RATES_FILE_PATH, cache)
        return {
            'updated_count': updated_count,
            'last_refresh': cache.get('last_refresh'),
        }
