import json
import pathlib
from datetime import datetime
from . import models


DATA_DIR = 'data'

def load_metadata(filepath):
    """Загружает JSON-файл или возвращает пустой словарь, если файла нет."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.loads(file.read())
    except FileNotFoundError:
        return {}

def save_metadata(filepath, data):
    """Сохраняет переданные данные в JSON-файл."""
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(json.dumps(data))

def read_data(type:str):
    return load_metadata(pathlib.Path(DATA_DIR+f'{type}.json'))

def save_data(type:str, data:dict):
    save_metadata(pathlib.Path(DATA_DIR+f'{type}.json'), data)

def register(username:str, password:str):
    '''
    Проверить уникальность username в users.json.
    Сгенерировать user_id (например, автоинкремент).
    Захешировать пароль (делайте односторонний псевдо-хеш (например, hashlib.sha256(password + salt)), соль храните рядом.).
    Сохранить пользователя в users.json.
    Создать пустой портфель (portfolios.json: user_id + пустой словарь кошельков).
    Вернуть сообщение об успехе.
    '''
    users = utils.read_data('users')
    # TODO: пока не реализовали чтение
    if any(record.get('username') == username for record in users):
        raise ValueError(f'Имя пользователя \'{username}\' уже занято')
    
    loaded_users = [models.User.from_dict(record) for record in users]
    portfolios = utils.read_data('portfolios')
    new_id = max((user.id for user in loaded_users), default=0) + 1
    user = models.User(new_id, username, '', '', datetime.now(timezone.utc))
    user.change_password(password)


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
    '''
    Убедиться, что пользователь залогинен.
    Загрузить портфель пользователя.
    Если кошельков нет — сообщить об этом.
    Для каждого кошелька: показать currency_code, баланс и посчитать стоимость в base по текущим курсам;
    Показать сумму по всем кошелькам в base.
    '''
    # TODO: не реализовано хранение залогиненых пользователей
    # if 
    #     raise ValueError('Сначала выполните login')
    
    # TODO: не реализовано хранилище кошельков
    # if not in :
    #     return models.Portfolio()
    
    # TODO: не реализовано хранилище и получение курсов
    
    raise NotImplementedError

def buy(currency:str, amount:float):
    '''
    Проверить логин.
    Валидировать currency (формат) и amount > 0.
    Если в портфеле нет такого кошелька — автоматически создать (как делает add_currency).
    Увеличить баланс кошелька на amount.
    Опционально (по желанию) вести «расчётную стоимость» покупки для отчёта:
    Получить текущий курс currency → base.
    Посчитать стоимость amount * rate и вывести в итог.
    '''
    
    
    raise NotImplementedError

def sell(currency:str, amount:float):
    raise NotImplementedError

def get_rate(original:str, targe:str):
    raise NotImplementedError
