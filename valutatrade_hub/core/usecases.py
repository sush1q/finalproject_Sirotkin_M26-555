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
        raise ValueError(f"Имя пользователя '{username}' уже занято")
    
    # TODO: пока не читаем users
    new_id = max(0) + 1
    new_user = models.User(new_id, username, '', '', datetime.now())
    new_user.change_password(password)
    
    # TODO: пока не работаем с файлами

    return (True, f"Пользователь '{username}' зарегистрирован (id={new_id}).")

def login(username:str, password:str):
    raise NotImplementedError

def show_portfolio(base:str = 'USD'):
    raise NotImplementedError

def buy(currency:str, amount:float):
    raise NotImplementedError

def sell(currency:str, amount:float):
    raise NotImplementedError

def get_rate(original:str, targe:str):
    raise NotImplementedError
