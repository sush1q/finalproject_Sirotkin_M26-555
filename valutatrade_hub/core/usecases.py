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
    user_id = 1
    for data in users:
        if data['username'] == username:
            raise ValueError(f'Имя пользователя \'{username}\' уже занято')
        user_id = max(user_id, data['user_id'] + 1)

    user = models.User(user_id, username, '', '', datetime.now(timezone.utc))
    user.change_password(password)
    portfolio = models.Portfolio(user_id, {}, user)
    portfolios = utils.read_data('portfolios')
    users.append(user.to_dict())
    portfolios.append(portfolio.to_dict())
    utils.save_data('users', users)
    utils.save_data('portfolios', portfolios)
    return user


def login(username:str, password:str):
    '''
    Найти пользователя по username.
    Сравнить хеш пароля.
    '''
    for data in utils.read_data('users'):
        if data['username'] == username:
            user = models.User.from_dict(data)
            if not user.verify_password(password):
                raise ValueError('Неверный пароль')
            return user
    raise ValueError(f'Пользователь \'{username}\' не найден')

def show_portfolio(user_id:int, base:str = 'USD'):
    '''
    Убедиться, что пользователь залогинен.
    Загрузить портфель пользователя.
    Если кошельков нет — сообщить об этом.
    Для каждого кошелька: показать currency_code, баланс и посчитать стоимость в base по текущим курсам;
    Показать сумму по всем кошелькам в base.
    '''
    if not utils.is_currency_fine(base):
        raise ValueError('Некорректный код валюты')
    cache = utils.read_data('rates')
def buy(user_id:int, currency_code:str, amount:float):
    '''
    Проверить логин.
    Валидировать currency (формат) и amount > 0.
    Если в портфеле нет такого кошелька — автоматически создать (как делает add_currency).
    Увеличить баланс кошелька на amount.
    Опционально (по желанию) вести «расчётную стоимость» покупки для отчёта:
    Получить текущий курс currency → base.
    Посчитать стоимость amount * rate и вывести в итог.
    '''
    if not utils.is_currency_fine(currency_code):
        raise ValueError('Некорректный код валюты')
    if not utils.is_positive(amount):
        raise ValueError('\'amount\' должен быть положительным числом')
def sell(user_id:int, currency_code:str, amount:float):
    '''
    Проверить логин.
    Валидировать входные данные.
    Проверить, что кошелёк существует и на нём достаточно средств.
    Уменьшить баланс.
    Опционально: начислить эквивалент в USD (если ведёте кошелёк USD).
    '''
    if not utils.is_currency_fine(currency_code):
        raise ValueError('Некорректный код валюты')
    if not utils.is_positive(amount):
        raise ValueError('\'amount\' должен быть положительным числом')
