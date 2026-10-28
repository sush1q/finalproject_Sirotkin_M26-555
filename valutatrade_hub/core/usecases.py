from datetime import datetime, timezone
from . import models, utils, exceptions


RATES_TTL_SECONDS = 300

def _load_portfolio(user:models.User):
    for data in utils.read_data('portfolios'):
        if data['user_id'] == user.id:
            return models.Portfolio.from_dict(data, user)
    raise ValueError(f'Портфель пользователя \'{user.username}\' не найден')

def _save_portfolio(portfolio:models.Portfolio):
    portfolios = utils.read_data('portfolios')
    for index, data in enumerate(portfolios):
        if data['user_id'] == portfolio.user_id:
            portfolios[index] = portfolio.to_dict()
            utils.save_data('portfolios', portfolios)
            return
    raise ValueError(f'Портфель пользователя с id={portfolio.user_id} не найден')

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

def show_portfolio(user:models.User, base:str = 'USD'):
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
    pairs = utils.DEFAULT_RATES.keys() | cache['pairs'].keys()
    if base != 'USD' and not any(base in pair.split('_') for pair in pairs):
        raise ValueError(f'Неизвестная базовая валюта \'{base}\'')
    portfolio = _load_portfolio(user)
    rates = {}
    rows = []
    for code, wallet in portfolio.wallets.items():
        rate, _ = get_rate(code, base)
        rates[f'{code}_{base}'] = rate
        rows.append({
            'currency_code': code,
            'balance': wallet.balance,
            'value': wallet.balance * rate,
        })
    return {
        'username': user.username,
        'base': base,
        'wallets': rows,
        'total': portfolio.get_total_value(base, rates),
    }

def buy(user:models.User, currency_code:str, amount:float):
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

    portfolio = _load_portfolio(user)
    rate, _ = get_rate(currency_code, 'USD')
    portfolio.add_currency(currency_code)
    wallet = portfolio.get_wallet(currency_code)
    before = wallet.balance
    wallet.deposit(amount)
    _save_portfolio(portfolio)
    return {
        'currency_code': currency_code,
        'amount': amount,
        'rate': rate,
        'before': before,
        'after': wallet.balance,
        'estimated_value': amount * rate,
    }

def sell(user:models.User, currency_code:str, amount:float):
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

    portfolio = _load_portfolio(user)
    wallet = portfolio.get_wallet(currency_code)
    before = wallet.balance
    wallet.withdraw(amount)
    rate, _ = get_rate(currency_code, 'USD')
    _save_portfolio(portfolio)
    return {
        'currency_code': currency_code,
        'amount': amount,
        'rate': rate,
        'before': before,
        'after': wallet.balance,
        'estimated_value': amount * rate,
    }

def get_rate(from_code:str, to_code:str):
    '''Возвращает курс и время: свежий кэш, затем фиксированная заглушка.'''
    if not utils.is_currency_fine(from_code) or not utils.is_currency_fine(to_code):
        raise ValueError(
            'Код валюты должен быть строкой без пробелов в верхнем регистре'
        )

    cache = utils.read_data('rates')
    currencies = {'USD'}
    for pair in utils.DEFAULT_RATES.keys() | cache['pairs'].keys():
        currencies.update(pair.split('_'))
    for code in (from_code, to_code):
        if code not in currencies:
            raise exceptions.CurrencyNotFoundError(code)

    now = datetime.now(timezone.utc)
    timestamp = now.isoformat().replace('+00:00', 'Z')
    if from_code == to_code:
        return 1.0, timestamp

    direct = f'{from_code}_{to_code}'
    reverse = f'{to_code}_{from_code}'
    for pair in (direct, reverse):
        data = cache['pairs'].get(pair)
        if not isinstance(data, dict) or not utils.is_positive(data.get('rate')):
            continue
        try:
            updated_at = datetime.fromisoformat(data['updated_at'])
            age = (now - updated_at).total_seconds()
        except (KeyError, TypeError, ValueError):
            continue
        if 0 <= age < RATES_TTL_SECONDS:
            rate = data['rate'] if pair == direct else 1 / data['rate']
            return rate, data['updated_at']

    # Кросс-курс состоит из двух обычных курсов к USD.
    if from_code != 'USD' and to_code != 'USD':
        from_usd, from_time = get_rate(from_code, 'USD')
        to_usd, to_time = get_rate(to_code, 'USD')
        return from_usd / to_usd, min(from_time, to_time, key=datetime.fromisoformat)

    try:
        rate = utils.convert_amount(from_code, to_code, 1.0, utils.DEFAULT_RATES)
    except ValueError as e:
        raise ValueError(
            f'Курс {from_code}→{to_code} недоступен. Повторите попытку позже.'
        ) from e
    cache['pairs'][direct] = {
        'rate': rate,
        'updated_at': timestamp,
        'source': 'Stub',
    }
    cache['last_refresh'] = timestamp
    utils.save_data('rates', cache)
    return rate, timestamp
