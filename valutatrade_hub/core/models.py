import hashlib
import random

from datetime import datetime


class User:
    def __init__(self, id:int, username:str, hashed_password:str, salt:str, registration_date: datetime):
        self._user_id = id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def id(self):
        return self._user_id

    @property
    def username(self):
        return self._username

    @property
    def registration_date(self):
        return self._registration_date

    @username.setter
    def username(self, value):
        if len(value) == 0:
            raise ValueError('Имя не может быть пустым')
        self._username = value

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
        if (len(new_password) < 4):
            raise ValueError('Пароль должен быть не короче 4 символов')
        self._salt = 'abc' # TODO: Генерировать
        self._hashed_password = hashlib.sha256((new_password + self._salt).encode(encoding='utf-8'))
    
    def verify_password(self, password: str):
        '''
        проверяет введённый пароль на совпадение
        '''
        pass

    # TODO: Для каждого атрибута реализовать геттер и, где необходимо, сеттер с проверками: Имя не может быть пусты и Пароль должен быть не короче 4 символов.


class Wallet:
    def __init__(self, currency_code: str, balance: float):
        self.currency_code = currency_code
        self._balance = balance

    @property
    def balance(self):
        return self._balance
    
    @balance.setter
    def balance(self, value):
        if not isinstance(value, [int, float]):
            raise ValueError('Некорректный тип данных')
        if value < 0:
            raise ValueError('Баланс не может быть отрицательным')
        self._balance = value

    def deposit(self, amount: float):
        '''
        пополнение баланс
        '''
        if amount < 0:
            raise ValueError('Размер пополнения не может быть отрицательным')
        new_balance = self.balance + amount
        self.balance = new_balance
    
    def withdraw(self, amount: float):
        '''
        снятие средств (если баланс позволяет)
        '''
        if amount < 0:
            raise ValueError('Размер списания не может быть отрицательным')
        if amount > self.balance:
            raise ValueError('Сумма снятия не может превышать размер баланса')
        new_balance = self._balance - amount
        self.balance = new_balance

    def get_balance_info(self):
        '''
        вывод информации о текущем балансе
        '''
        print(f'''
            Currency code: {self.currency_code}
            Balance: {self._balance}''')


class Portfolio:
    def __init__(self, user_id:int, wallets: dict[str, Wallet]):
        self._user_id = user_id
        self._wallets = wallets

    @property
    def user(self):
        # TODO: откуда его возвращать, пока по шагам мы никакого хранилища не сделали
        return User(self._user_id)

    @property
    def wallets(self):
        return self._wallets.copy()

    def add_currency(self, currency_code: str):
        if currency_code in self._wallets:
            return
        self._wallets[currency_code] = Wallet(currency_code, 0)

    def get_total_value(self, base_currency='USD'):
        # TODO: пока мы не дошли по шагам до того, чтобы откуда то брать курсы валют
        pass

    def get_wallet(self, currency_code):
        pass
