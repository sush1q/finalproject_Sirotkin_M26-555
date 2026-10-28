import tomllib


class SettingsLoader:
    __instance = None
    __data = None
    
    def __new__(cls):
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
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
            if data.get('tool') is not None:
                cls.__data = data.get('tool').get('valutatrade')
