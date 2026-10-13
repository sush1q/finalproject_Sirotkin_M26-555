from datetime import datetime
from . import models


def register(username:str, password:str):
    '''
    Проверить уникальность username в users.json.
    Сгенерировать user_id (например, автоинкремент).
    Захешировать пароль (делайте односторонний псевдо-хеш (например, hashlib.sha256(password + salt)), соль храните рядом.).
    Сохранить пользователя в users.json.
    Создать пустой портфель (portfolios.json: user_id + пустой словарь кошельков).
    Вернуть сообщение об успехе.
    '''
    
    # TODO: пока не реализовали чтение
    if username in []:
        raise ValueError(f'Имя пользователя \'{username}\' уже занято')
    
    # TODO: пока не читаем users
    new_id = max([0],default=0) + 1
    new_user = models.User(new_id, username, '', '', datetime.now())
    new_user.change_password(password)
    
    # TODO: пока не работаем с файлами

    return new_user

def login(username:str, password:str):
    '''
    Найти пользователя по username.
    Сравнить хеш пароля.
    '''
    # TODO: пока не реализовали чтение
    if username not in []:
        raise ValueError(f'Пользователь \'{username}\' не найден')

    # TODO: загрузить инфу о пользователе
    target_user = models.User('', '', '', '', '')
    target_user.verify_password(password)
    return target_user
    

def show_portfolio(base:str = 'USD'):
    raise NotImplementedError

def buy(currency:str, amount:float):
    raise NotImplementedError

def sell(currency:str, amount:float):
    raise NotImplementedError

def get_rate(original:str, targe:str):
    raise NotImplementedError
