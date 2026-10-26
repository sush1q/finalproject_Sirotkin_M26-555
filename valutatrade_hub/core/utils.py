import json
import math
from collections.abc import Mapping
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
    return isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0

def is_currency_fine(value: str) -> str:
    return (
        not isinstance(value, str)
        or not value
        or value != value.upper()
        or any(char.isspace() for char in value)
    )

def load_metadata(filepath, default=None):
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.loads(file.read())
    except FileNotFoundError:
        return {} if default is None else default

def save_metadata(filepath, data):
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(json.dumps(data))

def read_data(kind:str):
    '''Читает пользователей, портфели или кэш с правильным типом по умолчанию.'''
    # TODO: поясни что делает эта функция
    if kind not in AVAILABLE_DATA_TYPES:
        raise ValueError(f'Неизвестный тип данных \'{kind}\'')
    
    default = {'pairs': {}, 'last_refresh': None} if kind == 'rates' else [] # TODO: ОТКУДА это взялось?
    result = load_metadata(Path(DATA_DIR) / f'{kind}.json', default)
    if kind == 'rates':
        if not isinstance(result, dict) or not isinstance(result.get('pairs'), dict):
            raise ValueError('Некорректный формат rates.json: ожидается объект pairs')
    elif not isinstance(result, list) or any(
        not isinstance(record, dict) for record in result
    ):
        raise ValueError(f'Некорректный формат {kind}.json: ожидается список записей')
    return result

def save_data(kind:str, data):
    if kind not in AVAILABLE_DATA_TYPES:
        raise ValueError(f'Неизвестный тип данных \'{kind}\'')
    save_metadata(Path(DATA_DIR) / f'{kind}.json', data)
