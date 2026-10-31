import tomllib
from pathlib import Path

from valutatrade_hub.core import exceptions


class SettingsLoader:
    __instance = None
    __data = None
    
    def __new__(cls):
        # __new__ выбран как простой способ возвращать один экземпляр
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @classmethod
    def get(cls, key: str, default = ""):
        if cls.__data is None:
            cls.reload()
        return cls.__data.get(key, default)

    @classmethod
    def reload(cls):
        path = Path('pyproject.toml')
        try:
            with path.open('rb') as f:
                data = tomllib.load(f)
        except FileNotFoundError:
            cls.__data = {}
            return
        except (OSError, ValueError) as e:
            raise exceptions.ValutaTradeExceptions(
                f'Не удалось загрузить настройки: {e}'
            ) from e
        cls.__data = data.get('tool', {}).get('valutatrade', {})
