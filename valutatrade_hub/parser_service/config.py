import os
from pathlib import Path

from valutatrade_hub.core import currencies, exceptions
from valutatrade_hub.infra import settings


class ParserConfig:
    '''Собирает ключи API, URL, валюты, общую базу, таймаут и пути хранилищ'''
    COINGECKO_URL = 'https://api.coingecko.com/api/v3/simple/price'
    EXCHANGERATE_API_URL = 'https://v6.exchangerate-api.com/v6'
    BASE_CURRENCY = 'USD'
    CRYPTO_ID_MAP = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'SOL': 'solana',
    }

    def __init__(self):
        self.BASE_CURRENCY = settings.SettingsLoader.get(
            'base_currency', self.BASE_CURRENCY
        )
        if not isinstance(
            currencies.get_currency(self.BASE_CURRENCY), currencies.FiatCurrency
        ):
            raise exceptions.ValutaTradeExceptions(
                'Базовая валюта Parser должна быть фиатной'
            )
        self.EXCHANGERATE_API_KEY = os.getenv('EXCHANGERATE_API_KEY', '')
        self.COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY', '')
        self.FIAT_CURRENCIES = tuple(
            code for code, currency in currencies.currency_registry.items()
            if isinstance(currency, currencies.FiatCurrency)
            and code != self.BASE_CURRENCY
        )
        self.CRYPTO_CURRENCIES = tuple(
            code for code, currency in currencies.currency_registry.items()
            if isinstance(currency, currencies.CryptoCurrency)
        )
        data_path = Path(settings.SettingsLoader.get('data_path', 'data'))
        self.RATES_FILE_PATH = data_path / 'rates.json'
        self.HISTORY_FILE_PATH = data_path / 'exchange_rates.json'
        self.REQUEST_TIMEOUT = settings.SettingsLoader.get('request_timeout', 10)
        self.UPDATE_INTERVAL = settings.SettingsLoader.get(
            'parser_update_interval', 3600
        )
