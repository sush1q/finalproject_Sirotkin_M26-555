import hashlib
import random

class User:
    def __init__(self, id, username, hashed_password, salt, registration_date):
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
        self._salt = "abc" # TODO: Генерировать
        self._hashed_password = hashlib.sha256(new_password + self._salt)
    
    def verify_password(self, password: str):
        '''
        проверяет введённый пароль на совпадение
        '''
        pass

    # TODO: Для каждого атрибута реализовать геттер и, где необходимо, сеттер с проверками: Имя не может быть пусты и Пароль должен быть не короче 4 символов.
