import abc
import time

import requests

from valutatrade_hub import logging_config
from valutatrade_hub.core import exceptions, utils
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(abc.ABC):
    source = ''

    def __init__(self, config=None):
        self.config = config if config is not None else ParserConfig()

    @abc.abstractmethod
    def fetch_rates(self) -> dict:
        pass

    def _hide_api_keys(self, text):
        for key in (
            self.config.EXCHANGERATE_API_KEY, self.config.COINGECKO_API_KEY
        ):
            if key:
                text = text.replace(key, '***')
        return text

    def _request(self, url, params=None, headers=None):
        logger = logging_config.get_parser_logger()
        safe_url = self._hide_api_keys(url)
        logger.debug(f'GET {safe_url} params={params}')
        started = time.perf_counter()
        try:
            response = requests.get(
                url, params=params, headers=headers,
                timeout=self.config.REQUEST_TIMEOUT,
            )
        except requests.exceptions.RequestException as e:
            reason = self._hide_api_keys(str(e))
            raise exceptions.ApiRequestError(
                f'{self.source}: ошибка сети {type(e).__name__}: {reason}'
            ) from None
        logger.debug(
            '%s status=%s request_ms=%.1f', safe_url, response.status_code,
            (time.perf_counter() - started) * 1000,
        )
        if response.status_code != 200:
            reasons = {
                401: 'неверный или отсутствующий API-ключ',
                403: 'доступ запрещён; проверьте API-ключ',
                429: 'превышен лимит запросов',
            }
            reason = reasons.get(response.status_code, 'источник недоступен')
            raise exceptions.ApiRequestError(
                f'{self.source}: HTTP {response.status_code}, {reason}'
            )
        try:
            data = response.json()
        except ValueError:
            raise exceptions.ApiRequestError(
                f'{self.source}: некорректный JSON в ответе'
            )
        if not isinstance(data, dict):
            raise exceptions.ApiRequestError(
                f'{self.source}: ожидался JSON-объект'
            )
        return data


class CoinGeckoClient(BaseApiClient):
    source = 'CoinGecko'

    def fetch_rates(self) -> dict:
        try:
            ids = [
                self.config.CRYPTO_ID_MAP[code]
                for code in self.config.CRYPTO_CURRENCIES
            ]
        except KeyError as e:
            raise exceptions.ApiRequestError(
                f'{self.source}: не задан ID монеты {e}'
            ) from e
        headers = {}
        if self.config.COINGECKO_API_KEY:
            headers['x-cg-demo-api-key'] = self.config.COINGECKO_API_KEY
        base = self.config.BASE_CURRENCY.lower()
        data = self._request(
            self.config.COINGECKO_URL,
            params={'ids': ','.join(ids), 'vs_currencies': base},
            headers=headers,
        )
        result = {}
        for code, coin_id in zip(self.config.CRYPTO_CURRENCIES, ids):
            item = data.get(coin_id)
            if not isinstance(item, dict):
                raise exceptions.ApiRequestError(
                    f'{self.source}: отсутствуют данные {code}'
                )
            rate = item.get(base)
            if not utils.is_positive(rate):
                raise exceptions.ApiRequestError(
                    f'{self.source}: некорректный или отсутствующий курс {code}'
                )
            result[f'{code}_{self.config.BASE_CURRENCY}'] = float(rate)
        return result


class ExchangeRateApiClient(BaseApiClient):
    source = 'ExchangeRate-API'

    def fetch_rates(self) -> dict:
        if not self.config.EXCHANGERATE_API_KEY:
            raise exceptions.ApiRequestError(
                f'{self.source}: задайте EXCHANGERATE_API_KEY в окружении'
            )
        base = self.config.BASE_CURRENCY
        url = (
            f'{self.config.EXCHANGERATE_API_URL}/'
            f'{self.config.EXCHANGERATE_API_KEY}/latest/{base}'
        )
        data = self._request(url)
        if data.get('result') != 'success':
            reasons = {
                'invalid-key': 'неверный API-ключ',
                'inactive-account': 'учётная запись не активирована',
                'quota-reached': 'превышен лимит запросов',
                'unsupported-code': 'неподдерживаемая базовая валюта',
            }
            reason = reasons.get(data.get('error-type'), 'неуспешный ответ API')
            raise exceptions.ApiRequestError(f'{self.source}: {reason}')
        rates = data.get('conversion_rates')
        if data.get('base_code') != base or not isinstance(rates, dict):
            raise exceptions.ApiRequestError(
                f'{self.source}: некорректная база или conversion_rates'
            )
        result = {}
        for code in self.config.FIAT_CURRENCIES:
            rate = rates.get(code)
            if not utils.is_positive(rate) or not utils.is_positive(1 / rate):
                raise exceptions.ApiRequestError(
                    f'{self.source}: некорректный или отсутствующий курс {code}'
                )
            result[f'{code}_{base}'] = 1 / rate
        return result
