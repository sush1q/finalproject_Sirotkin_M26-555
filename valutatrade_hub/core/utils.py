import math
from datetime import datetime, timezone
from valutatrade_hub.core import exceptions


DEFAULT_RATES = {
    'EUR_USD': 1.0786,
    'BTC_USD': 59337.21,
    'RUB_USD': 0.01016,
    'ETH_USD': 3720.0,
    'GBP_USD': 1 / 0.809,
    'SOL_USD': 145.12,
}

def is_positive(value: float, allow_zero:bool=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if not math.isfinite(value):
        return False
    if allow_zero:
        return value >= 0
    return value > 0

def _find_rate(rates, from_code, to_code):
    '''Возвращает значение курса и пары, использованные для расчёта.'''
    if from_code == to_code:
        return 1.0, ()
    from_rates = {}
    to_rates = {}
    for pair, rate in rates.items():
        try:
            original, target = pair.split('_')
        except (AttributeError, ValueError) as e:
            raise exceptions.ValutaTradeExceptions(f'Некорректная валютная пара {pair}') from e
        if not is_positive(rate):
            raise exceptions.ValutaTradeExceptions(f'Некорректный курс {pair}')
        # Прямая запись имеет приоритет перед вычисленной обратной.
        for code, quotes in ((from_code, from_rates), (to_code, to_rates)):
            if original == code:
                quotes[target] = (rate, pair)
            elif target == code:
                quotes.setdefault(original, (1 / rate, pair))

    if to_code in from_rates:
        rate, pair = from_rates[to_code]
        used_pairs = (pair,)
    else:
        common_codes = sorted(from_rates.keys() & to_rates.keys())
        if not common_codes:
            return None
        common = common_codes[0]
        from_rate, from_pair = from_rates[common]
        to_rate, to_pair = to_rates[common]
        rate = from_rate / to_rate
        used_pairs = (from_pair, to_pair)
    if not is_positive(rate):
        raise exceptions.ValutaTradeExceptions('Курс должен быть положительным числом')
    return rate, used_pairs

def parse_rate(pairs, from_code, to_code, ttl=None):
    now = datetime.now(timezone.utc)
    if from_code == to_code:
        return 1.0, now.isoformat()

    rates = {}
    dates = {}
    for pair, record in pairs.items():
        try:
            rate = record['rate']
            if not is_positive(rate):
                raise ValueError('Курс должен быть положительным числом')
            updated_at = datetime.fromisoformat(record['updated_at'])
            if updated_at.utcoffset() is None:
                raise ValueError('У даты курса должен быть указан часовой пояс')
        except (KeyError, TypeError, ValueError) as e:
            raise exceptions.ValutaTradeExceptions(
                f'Некорректная запись курса {pair}: {e}'
            ) from e
        if ttl is not None:
            age = (now - updated_at).total_seconds()
            if age < 0 or age >= ttl:
                continue
        rates[pair] = rate
        dates[pair] = updated_at

    found = _find_rate(rates, from_code, to_code)
    if found is None:
        return None
    rate, used_pairs = found
    updated_at = min(dates[pair] for pair in used_pairs)
    return rate, updated_at.astimezone(timezone.utc).isoformat()

def convert_amount(from_code: str, to_code: str, amount: float, rates: dict) -> float:
    found = _find_rate(rates, from_code, to_code)
    if found is None:
        raise exceptions.ValutaTradeExceptions(
            f'Не удалось получить курс для {from_code}→{to_code}'
        )
    return amount * found[0]
