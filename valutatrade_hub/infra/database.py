import json
from pathlib import Path
from valutatrade_hub.core import exceptions
from valutatrade_hub.infra import settings


AVAILABLE_DATA_TYPES = {'users', 'portfolios', 'rates'}

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

class DatabaseManager:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def read_data(self, kind:str):
        if kind not in AVAILABLE_DATA_TYPES:
            raise exceptions.ValutaTradeExceptions(f'Неизвестный тип данных \'{kind}\'')

        default = {'pairs': {}, 'last_refresh': None} if kind == 'rates' else []
        result = load_metadata(Path(settings.SettingsLoader.get('data_path', 'data')) / f'{kind}.json', default)
        if kind == 'rates':
            if not isinstance(result, dict) or not isinstance(result.get('pairs'), dict):
                raise exceptions.ValutaTradeExceptions('Некорректный формат rates.json: ожидается объект pairs')
        elif not isinstance(result, list) or any(not isinstance(record, dict) for record in result):
            raise exceptions.ValutaTradeExceptions(f'Некорректный формат {kind}.json: ожидается список записей')
        return result

    def save_data(self, kind:str, data):
        if kind not in AVAILABLE_DATA_TYPES:
            raise exceptions.ValutaTradeExceptions(f'Неизвестный тип данных \'{kind}\'')
        save_metadata(Path(settings.SettingsLoader.get('data_path', 'data')) / f'{kind}.json', data)
