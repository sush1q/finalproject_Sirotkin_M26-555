import abc

from valutatrade_hub.core import exceptions


class Currency(abc.ABC):
    '''Абстрактная валюта с проверяемыми именем и кодом'''
    def __init__(self, name:str, code:str):
        self.name = name
        self.code = code
        
    @property
    def name(self):
        '''Возвращает непустое человекочитаемое имя валюты'''
        return self._name

    @name.setter
    def name(self, value:str):
        '''Задаёт имя валюты после проверки непустой строки'''
        if not isinstance(value, str) or not value.strip():
            raise exceptions.ValutaTradeExceptions('Имя не может быть пустым')
        self._name = value

    @property
    def code(self):
        '''Возвращает код валюты в верхнем регистре'''
        return self._code
    
    @code.setter
    def code(self, value:str):
        '''Проверяет и задаёт код длиной 2–5 символов без пробелов'''
        if not isinstance(value, str):
            raise exceptions.ValutaTradeExceptions('Код валюты должен быть строкой')
        if not value.isupper() :
            raise exceptions.ValutaTradeExceptions(
                'Код валюты должен быть в верхнем регистре'
            )
        if len(value) not in range(2,6):
            raise exceptions.ValutaTradeExceptions(
                'Код валюты должен быть длиной от 2 до 5 символов'
            )
        if any(c.isspace() for c in value):
            raise exceptions.ValutaTradeExceptions(
                'Код валюты не должен содержать пробелов'
            )
        self._code = value

    @abc.abstractmethod
    def get_display_info(self) -> str:
        '''Возвращает общую часть описания валюты для интерфейса'''
        return f'{self.code} - {self.name}'


class FiatCurrency(Currency):
    '''Фиатная валюта с указанием страны или зоны эмиссии'''
    def __init__(self, name:str, code:str, issuing_country: str):
        super().__init__(name, code)
        self.issuing_country = issuing_country
        
    def get_display_info(self) -> str:
        '''Возвращает описание фиатной валюты со страной эмиссии'''
        parent_info = super().get_display_info()
        return f'[FIAT] {parent_info} (Issuing: {self.issuing_country})'


class CryptoCurrency(Currency):
    '''Криптовалюта с алгоритмом и известной капитализацией'''
    def __init__(self, name:str, code:str, algorithm:str, market_cap:float):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap
        
    def get_display_info(self):
        '''Возвращает описание криптовалюты с алгоритмом и капитализацией'''
        parent_info = super().get_display_info()
        return (
            f'[CRYPTO] {parent_info} '
            f'(Algo: {self.algorithm}, MCAP: {self.market_cap:.3g})'
        )


currency_registry = {
    'USD': FiatCurrency('US Dollar', 'USD', 'United States'),
    'EUR': FiatCurrency('Euro', 'EUR', 'Eurozone'),
    'RUB': FiatCurrency('Russian Ruble', 'RUB', 'Russia'),
    'GBP': FiatCurrency('Pound Sterling', 'GBP', 'United Kingdom'),

    'BTC': CryptoCurrency('Bitcoin', 'BTC', 'SHA-256', 1.12e12),
    'ETH': CryptoCurrency('Ether', 'ETH', 'Ethash', 0.0),
    'SOL': CryptoCurrency('Solana', 'SOL', 'Proof of History', 0.0),
}

def get_currency(code: str) -> Currency:    
    '''Возвращает валюту из реестра; неизвестный код вызывает CurrencyNotFoundError'''
    if code not in currency_registry:
        raise exceptions.CurrencyNotFoundError(code)
    return currency_registry[code]
