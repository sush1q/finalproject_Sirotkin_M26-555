import abc


class Currency(abc.ABC):
    def __init__(self, name, code):
        self.name = name
        self.code = code
        
    @property
    def name(self):
        return self.name

    @name.setter
    def name(self, value):
        if not value:
            raise ValueError('Имя не может быть пустым')
        self.name = value

    @property
    def code(self):
        return self.code
    
    @code.setter
    def code(self, value:str):
        if not value.isupper() :
            raise ValueError('Код валюты должен быть в верхнем регистре')
        if len(value) not in range(2,6):
            raise ValueError('Код валюты должен быть длиной от 2 до 5 символов')
        if any(c.isspace() for c in value):
            raise ValueError('Код валюты не должен содержать пробелов')
        self.code = value

    def get_display_info(self) -> str:
        return f'{self.code} - {self.name}'

