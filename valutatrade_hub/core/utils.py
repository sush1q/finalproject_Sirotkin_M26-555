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

def parse_rate(pairs, from_code, to_code, ttl=None):
    '''Находит курс в словаре пар и возвращает его вместе с датой.'''
    now = datetime.now(timezone.utc)
    if from_code == to_code:
        return 1.0, now.isoformat()

    direct_pair = f'{from_code}_{to_code}'
    reverse_pair = f'{to_code}_{from_code}'
    for pair in (direct_pair, reverse_pair):
        record = pairs.get(pair)
        if not isinstance(record, dict):
            continue
        if not is_positive(record.get('rate')):
            continue
        try:
            updated_at = datetime.fromisoformat(record['updated_at'])
            age = (now - updated_at).total_seconds()
        except (KeyError, TypeError, ValueError):
            continue
        if ttl is not None:
            if age < 0 or age >= ttl:
                continue
        rate = record['rate']
        if pair == reverse_pair:
            rate = 1 / rate
        if is_positive(rate):
            return rate, record['updated_at']

    # Для кросс-курса нужны стоимости обеих валют в USD.
    if from_code == 'USD' or to_code == 'USD':
        return None
    from_usd = parse_rate(pairs, from_code, 'USD', ttl)
    to_usd = parse_rate(pairs, to_code, 'USD', ttl)
    if from_usd is None or to_usd is None:
        return None
    rate = from_usd[0] / to_usd[0]
    if not is_positive(rate):
        return None
    updated_at = min(from_usd[1], to_usd[1], key=datetime.fromisoformat)
    return rate, updated_at

def convert_amount(from_code: str, to_code: str, amount: float, rates: dict) -> float:
    if from_code == to_code:
        return amount
    direct_pair = f'{from_code}_{to_code}'
    reverse_pair = f'{to_code}_{from_code}'
    try:
        if direct_pair in rates:
            rate = rates[direct_pair]
        elif reverse_pair in rates:
            rate = 1 / rates[reverse_pair]
        else:
            from_usd = 1 if from_code == 'USD' else rates[f'{from_code}_USD']
            to_usd = 1 if to_code == 'USD' else rates[f'{to_code}_USD']
            rate = from_usd / to_usd
    except (KeyError, TypeError, ZeroDivisionError) as e:
        raise exceptions.ValutaTradeExceptions(
            f'Не удалось получить курс для {from_code}→{to_code}'
        ) from e
    if not is_positive(rate):
        raise exceptions.ValutaTradeExceptions('Курс должен быть положительным числом')
    return amount * rate
