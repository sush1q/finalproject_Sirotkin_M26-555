import abc


class CurrencyNotFoundError(Exception):
    pass


class Currency(abc.ABC):
    def __init__(self, name:str, code:str):
        self.name = name
        self.code = code
        
    @property
    def name(self):
        return self.name

    @name.setter
    def name(self, value:str):
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


class FiatCurrency(Currency):
    def __init__(self, name:str, code:str, issuing_country: str):
        super().__init__(name, code)
        self.issuing_country = issuing_country
        
    def get_display_info(self) -> str:
        parent_info = super().get_display_info()
        return f'[FIAT] {parent_info} (Issuing: {self.issuing_country})'


class CryptoCurrency(Currency):
    def __init__(self, name:str, code:str, algorithm:str, market_cap:float):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap
        
    def get_display_info(self):
        parent_info = super().get_display_info()
        return f'[CRYPTO] {parent_info} (Algo: {self.algorithm}, MCAP: {self.market_cap})'


currency_registry = {}

def get_currency(code: str) -> Currency:
    if code not in currency_registry:
        raise CurrencyNotFoundError
    return currency_registry[code]
