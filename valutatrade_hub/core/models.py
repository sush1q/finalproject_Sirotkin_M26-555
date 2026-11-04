import hashlib
import secrets
from datetime import datetime, timezone

from valutatrade_hub.core import currencies, exceptions, utils


class User:
    '''Пользователь с именем, солью, хешем пароля и датой регистрации в UTC'''
    def __init__(
        self, id:int, username:str, hashed_password:str, salt:str,
        registration_date: datetime,
    ):
        if isinstance(id, bool) or not isinstance(id, int) or id <= 0:
            raise exceptions.ValutaTradeExceptions(
                'ID пользователя должен быть положительным целым числом'
            )
        if not isinstance(hashed_password, str) or not isinstance(salt, str):
            raise exceptions.ValutaTradeExceptions('Хэш и соль должны быть строками')
        
        self._user_id = id
        self.username = username
        self._hashed_password = hashed_password
        self._salt = salt
        if not isinstance(registration_date, datetime):
            raise exceptions.ValutaTradeExceptions(
                'Дата регистрации должна быть datetime'
            )

        if registration_date.utcoffset() is None:
            raise exceptions.ValutaTradeExceptions(
                'У даты регистрации должен быть указан часовой пояс'
            )
        self._registration_date = registration_date.astimezone(timezone.utc)

    @property
    def id(self):
        '''Возвращает неизменяемый идентификатор пользователя'''
        return self._user_id

    @property
    def username(self):
        '''Возвращает имя пользователя'''
        return self._username

    @username.setter
    def username(self, value):
        '''Проверяет и задаёт непустое имя пользователя'''
        if not isinstance(value, str) or not value.strip():
            raise exceptions.ValutaTradeExceptions('Имя не может быть пустым')
        self._username = value

    @property
    def hashed_password(self) -> str:
        '''Возвращает сохранённый SHA-256 хеш пароля с солью'''
        return self._hashed_password

    @property
    def salt(self) -> str:
        '''Возвращает индивидуальную соль для проверки пароля'''
        return self._salt

    @property
    def registration_date(self):
        '''Возвращает дату регистрации с часовым поясом UTC'''
        return self._registration_date

    def get_user_info(self):
        '''Печатает сведения о пользователе без пароля и его хеша'''
        print(f'''
            UserID: {self._user_id};
            Username: {self._username}
            Registration date: {self._registration_date}
            Salt: {self._salt}''')

    def change_password(self, new_password: str):
        '''Проверяет длину пароля и сохраняет его хеш с новой случайной солью'''
        if not isinstance(new_password, str) or len(new_password) < 4:
            raise exceptions.ValutaTradeExceptions(
                'Пароль должен быть не короче 4 символов'
            )
        self._salt = secrets.token_hex(16)
        password_with_salt = (new_password + self._salt).encode('utf-8')
        self._hashed_password = hashlib.sha256(password_with_salt).hexdigest()

    def verify_password(self, password: str):
        '''Возвращает True, если пароль соответствует сохранённому хешу'''
        if not isinstance(password, str):
            return False
        password_with_salt = (password + self.salt).encode('utf-8')
        hashed_input = hashlib.sha256(password_with_salt).hexdigest()
        return hashed_input == self.hashed_password

    def to_dict(self):
        '''Возвращает JSON-совместимые данные пользователя с ISO-датой'''
        return {
            'user_id': self.id,
            'username': self.username,
            'hashed_password': self.hashed_password,
            'salt': self.salt,
            'registration_date': self.registration_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data:dict):
        '''
        Восстанавливает пользователя из JSON-записи;
        неверные данные вызывают ошибку
        '''
        try:
            return cls(
                data['user_id'],
                data['username'],
                data['hashed_password'],
                data['salt'],
                datetime.fromisoformat(data['registration_date']),
            )
        except (KeyError, TypeError, ValueError, exceptions.ValutaTradeExceptions) as e:
            raise exceptions.ValutaTradeExceptions(
                'Некорректная запись пользователя в users.json'
            ) from e


class Wallet:
    '''Кошелёк известной валюты с конечным неотрицательным балансом'''
    def __init__(self, currency_code: str, balance: float=0.0):
        currencies.get_currency(currency_code)
        self.currency_code = currency_code
        self.balance = balance

    @property
    def balance(self):
        '''Возвращает баланс кошелька'''
        return self._balance

    @balance.setter
    def balance(self, value):
        '''Проверяет конечное неотрицательное число и сохраняет баланс'''
        if not utils.is_positive(value, allow_zero=True):
            raise exceptions.ValutaTradeExceptions(
                'Баланс должен быть конечным неотрицательным числом'
            )
        self._balance = float(value)

    def deposit(self, amount: float):
        '''Увеличивает баланс на положительную конечную сумму'''
        if not utils.is_positive(amount):
            raise exceptions.ValutaTradeExceptions(
                'Размер пополнения должен быть положительным конечным числом'
            )
        new_balance = self.balance + amount
        self.balance = new_balance

    def withdraw(self, amount: float):
        '''
        Списывает положительную сумму; при нехватке средств даёт
        InsufficientFundsError
        '''
        if not utils.is_positive(amount):
            raise exceptions.ValutaTradeExceptions(
                'Размер списания должен быть положительным конечным числом'
            )
        if amount > self.balance:
            raise exceptions.InsufficientFundsError(
                self.balance, self.currency_code, amount
            )

        new_balance = self._balance - amount
        self.balance = new_balance

    def get_balance_info(self):
        '''Печатает код валюты и текущий баланс кошелька'''
        print(f'Currency code: {self.currency_code}')
        print(f'Balance: {self.balance}')

    def to_dict(self):
        '''Возвращает JSON-совместимую запись баланса'''
        return {'balance': self.balance}

    @classmethod
    def from_dict(cls, currency_code:str, data:dict):
        '''Восстанавливает кошелёк по коду валюты и JSON-записи баланса'''
        try:
            return cls(currency_code, data['balance'])
        except (KeyError, TypeError, exceptions.ValutaTradeExceptions) as e:
            raise exceptions.ValutaTradeExceptions(
                'Некорректная запись кошелька в portfolios.json'
            ) from e


class Portfolio:
    '''Набор уникальных кошельков пользователя без доступа к файлам хранилища'''
    def __init__(self, user_id:int, wallets: dict[str, Wallet], user:User=None):
        self._user_id = user_id
        self._wallets = wallets.copy()
        self._user = user

    @property
    def user_id(self) -> int:
        '''Возвращает идентификатор владельца портфеля'''
        return self._user_id

    @property
    def user(self):
        '''Возвращает переданный объект User без возможности замены свойства'''
        return self._user

    @property
    def wallets(self):
        '''Возвращает копию словаря, сохраняя ссылки на объекты Wallet'''
        return self._wallets.copy()

    def add_currency(self, currency_code: str):
        '''Создаёт отсутствующий кошелёк; существующий баланс не изменяет'''
        currencies.get_currency(currency_code)

        if currency_code in self._wallets:
            return
        self._wallets[currency_code] = Wallet(currency_code, 0)

    def get_total_value(self, base_currency='USD', rates=None):
        '''
        Возвращает стоимость портфеля в base_currency

        Использует переданный словарь числовых курсов или DEFAULT_RATES; отсутствие
        курса вызывает ошибку
        '''
        currencies.get_currency(base_currency)
        if rates is None:
            rates = utils.DEFAULT_RATES
        return sum(
            utils.convert_amount(code, base_currency, wallet.balance, rates)
            for code, wallet in self._wallets.items()
        )

    def get_wallet(self, currency_code):
        '''Возвращает кошелёк валюты или сообщает о его отсутствии'''
        currencies.get_currency(currency_code)

        if currency_code not in self._wallets:
            raise exceptions.ValutaTradeExceptions(
                f'У вас нет кошелька \'{currency_code}\'. Добавьте валюту: '
                'она создаётся автоматически при первой покупке.'
            )
        return self._wallets[currency_code]

    def to_dict(self):
        '''Возвращает JSON-совместимые данные портфеля и его кошельков'''
        return {
            'user_id': self.user_id,
            'wallets': {
                code: wallet.to_dict()
                for code, wallet in self._wallets.items()
            },
        }

    @classmethod
    def from_dict(cls, data:dict, user:User=None):
        '''Восстанавливает портфель из JSON-записи и переданного User'''
        try:
            wallets = {
                code: Wallet.from_dict(code, wallet_data)
                for code, wallet_data in data['wallets'].items()
            }
            return cls(data['user_id'], wallets, user)
        except (
            KeyError, TypeError, AttributeError, exceptions.ValutaTradeExceptions,
        ) as e:
            raise exceptions.ValutaTradeExceptions(
                'Некорректная запись портфеля'
            ) from e
