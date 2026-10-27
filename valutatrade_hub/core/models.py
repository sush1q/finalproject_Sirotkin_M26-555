import hashlib
import secrets

from datetime import datetime, timezone

from . import utils


class User:
    def __init__(self, id:int, username:str, hashed_password:str, salt:str, registration_date: datetime):
        if isinstance(id, bool) or not isinstance(id, int) or id <= 0:
            raise ValueError('ID пользователя должен быть положительным целым числом')
        if not isinstance(hashed_password, str) or not isinstance(salt, str):
            raise ValueError('Хэш и соль должны быть строками')
        
        self._user_id = id
        self.username = username
        self._hashed_password = hashed_password
        self._salt = salt
        if not isinstance(registration_date, datetime):
            raise ValueError('Дата регистрации должна быть datetime')

        if registration_date.tzinfo is None:
            registration_date = registration_date.replace(tzinfo=timezone.utc)
        self._registration_date = registration_date.astimezone(timezone.utc)

    @property
    def id(self):
        return self._user_id

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError('Имя не может быть пустым')
        self._username = value

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self):
        return self._registration_date

    def get_user_info(self):
        '''
        выводит информацию о пользователе (без пароля)
        '''
        print(f'''
            UserID: {self._user_id};
            Username: {self._username}
            Registration date: {self._registration_date}
            Salt: {self._salt}''')

    def change_password(self, new_password: str):
        '''
        изменяет пароль пользователя, с хешированием нового пароля
        '''
        if not isinstance(new_password, str) or len(new_password) < 4:
            raise ValueError('Пароль должен быть не короче 4 символов')
        self._salt = secrets.token_hex(16)
        self._hashed_password = hashlib.sha256((new_password + self._salt).encode(encoding='utf-8')).hexdigest()

    def verify_password(self, password: str):
        '''
        проверяет введённый пароль на совпадение
        '''
        if not isinstance(password, str):
            return False
        hashed_input = hashlib.sha256((password + self.salt).encode('utf-8')).hexdigest()
        return hashed_input == self.hashed_password

    def to_dict(self):
        return {
            'user_id': self.id,
            'username': self.username,
            'hashed_password': self.hashed_password,
            'salt': self.salt,
            'registration_date': self.registration_date.isoformat().replace('+00:00', 'Z'),
        }

    @classmethod
    def from_dict(cls, data:dict):
        try:
            return cls(
                data['user_id'],
                data['username'],
                data['hashed_password'],
                data['salt'],
                datetime.fromisoformat(data['registration_date']),
            )
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError('Некорректная запись пользователя в users.json') from e


class Wallet:
    def __init__(self, currency_code: str, balance: float=0.0):
        if not utils.is_currency_fine(currency_code):
            raise ValueError('Передан некорректный код валюты')
        self.currency_code = currency_code
        self.balance = balance

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        if not utils.is_positive(value):
            raise ValueError('Баланс не может быть отрицательным')
        self._balance = float(value)

    def deposit(self, amount: float):
        '''
        пополнение баланс
        '''
        if not utils.is_positive(amount):
            raise ValueError('Размер пополнения не может быть отрицательным')
        new_balance = self.balance + amount
        self.balance = new_balance

    def withdraw(self, amount: float):
        '''
        снятие средств (если баланс позволяет)
        '''
        if not utils.is_positive(amount):
            raise ValueError('Размер списания не может быть отрицательным')
        if amount > self.balance:
            raise ValueError(
                f'Недостаточно средств: доступно {self.balance:.8g} '
                f'{self.currency_code}, требуется {amount:.8g} {self.currency_code}'
            )
        new_balance = self._balance - amount
        self.balance = new_balance

    def get_balance_info(self):
        print(f'Currency code: {self.currency_code}\n'\
            f'Balance: {self._balance}')

    def to_dict(self):
        return {'balance': self.balance}

    @classmethod
    def from_dict(cls, currency_code:str, data:dict):
        try:
            return cls(currency_code, data['balance'])
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError('Некорректная запись кошелька в portfolios.json') from e


class Portfolio:
    def __init__(self, user_id:int, wallets: dict[str, Wallet], user:User=None):
        self._user_id = user_id
        self._wallets = wallets.copy()
        self._user = user

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def user(self):
        return self._user

    @property
    def wallets(self):
        return self._wallets.copy()

    def add_currency(self, currency_code: str):
        if not utils.is_currency_fine(currency_code):
            raise ValueError('Код валюты должен быть строкой без пробелов в верхнем регистре')
        
        if currency_code in self._wallets:
            return
        self._wallets[currency_code] = Wallet(currency_code, 0)

    def get_total_value(self, base_currency='USD', rates=utils.DEFAULT_RATES):
        if not utils.is_currency_fine(base_currency):
            raise ValueError('Код валюты должен быть строкой без пробелов в верхнем регистре')
        
        return sum(
            utils.convert_amount(code, base_currency, wallet.balance, rates)
            for code, wallet in self._wallets.items()
        )

    def get_wallet(self, currency_code):
        if not utils.is_currency_fine(currency_code):
            raise ValueError('Код валюты должен быть строкой без пробелов в верхнем регистре')

        if currency_code not in self._wallets:
            raise ValueError(
                f'У вас нет кошелька \'{currency_code}\'. Добавьте валюту: '
                'она создаётся автоматически при первой покупке.'
            )
        return self._wallets[currency_code]

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'wallets': {
                code: wallet.to_dict()
                for code, wallet in self._wallets.items()
            },
        }

    @classmethod
    def from_dict(cls, data:dict, user:User=None):
        try:
            wallets = {
                code: Wallet.from_dict(code, wallet_data)
                for code, wallet_data in data['wallets'].items()
            }
            return cls(data['user_id'], wallets, user)
        except (KeyError, TypeError, AttributeError, ValueError) as e:
            raise ValueError('Некорректная запись портфеля') from e
