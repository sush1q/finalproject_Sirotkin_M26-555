import math
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
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and (value >= 0 if allow_zero else value > 0)

def convert_amount(from_code: str, to_code: str, amount: float, rates: dict) -> float:
    if from_code == to_code:
        return amount
    direct = f'{from_code}_{to_code}'
    reverse = f'{to_code}_{from_code}'
    try:
        if direct in rates:
            rate = rates[direct]
        elif reverse in rates:
            rate = 1 / rates[reverse]
        else:
            from_usd = 1 if from_code == 'USD' else rates[f'{from_code}_USD']
            to_usd = 1 if to_code == 'USD' else rates[f'{to_code}_USD']
            rate = from_usd / to_usd
    except (KeyError, TypeError, ZeroDivisionError) as e:
        raise exceptions.ValutaTradeExceptions(f'Не удалось получить курс для {from_code}→{to_code}') from e
    if not is_positive(rate):
        raise exceptions.ValutaTradeExceptions('Курс должен быть положительным числом')
    return amount * rate
