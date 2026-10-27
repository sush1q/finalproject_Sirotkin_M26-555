import json
import math
from pathlib import Path

DATA_DIR = Path('data')
DEFAULT_RATES = {
    'EUR_USD': 1.0786,
    'BTC_USD': 59337.21,
    'RUB_USD': 0.01016,
    'ETH_USD': 3720.0,
    'GBP_USD': 1 / 0.809,
    'SOL_USD': 145.12,
}
AVAILABLE_DATA_TYPES = {'users', 'portfolios', 'rates'}

def is_positive(value: float):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0

def is_currency_fine(value: str) -> bool:
    return isinstance(value, str) and bool(value) and value == value.upper() and not any(char.isspace() for char in value)

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
        raise ValueError(f'Не удалось получить курс для {from_code}→{to_code}') from e
    if not is_positive(rate):
        raise ValueError('Курс должен быть положительным числом')
    return amount * rate

def load_metadata(filepath, default=None):
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.loads(file.read())
    except FileNotFoundError:
        return {} if default is None else default

def save_metadata(filepath, data):
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(json.dumps(data))

def read_data(kind:str):
    if kind not in AVAILABLE_DATA_TYPES:
        raise ValueError(f'Неизвестный тип данных \'{kind}\'')

    default = {'pairs': {}, 'last_refresh': None} if kind == 'rates' else []
    result = load_metadata(Path(DATA_DIR) / f'{kind}.json', default)
    if kind == 'rates':
        if not isinstance(result, dict) or not isinstance(result.get('pairs'), dict):
            raise ValueError('Некорректный формат rates.json: ожидается объект pairs')
    elif not isinstance(result, list) or any(not isinstance(record, dict) for record in result):
        raise ValueError(f'Некорректный формат {kind}.json: ожидается список записей')
    return result

def save_data(kind:str, data):
    if kind not in AVAILABLE_DATA_TYPES:
        raise ValueError(f'Неизвестный тип данных \'{kind}\'')
    save_metadata(Path(DATA_DIR) / f'{kind}.json', data)
