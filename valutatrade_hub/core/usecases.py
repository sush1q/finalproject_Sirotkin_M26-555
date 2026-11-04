from datetime import datetime, timezone

from valutatrade_hub import decorators
from valutatrade_hub.core import currencies, exceptions, models, utils
from valutatrade_hub.infra import database, settings
from valutatrade_hub.parser_service import updater


def _load_portfolio(user:models.User):
    for data in database.DatabaseManager().read_data('portfolios'):
        if data['user_id'] == user.id:
            return models.Portfolio.from_dict(data, user)
    raise exceptions.PortfolioNotFoundError(user.id)

def _save_portfolio(portfolio:models.Portfolio):
    portfolios = database.DatabaseManager().read_data('portfolios')
    for index, data in enumerate(portfolios):
        if data['user_id'] == portfolio.user_id:
            portfolios[index] = portfolio.to_dict()
            database.DatabaseManager().save_data('portfolios', portfolios)
            return
    raise exceptions.PortfolioNotFoundError(portfolio.user_id)

@decorators.log_action()
def register(username:str, password:str):
    '''
    Создаёт User с уникальным именем и пустой портфель, сохраняет их в JSON
    Возвращает User. Занятое имя или некорректные данные вызывают ошибку приложения
    '''
    db = database.DatabaseManager()
    users = db.read_data('users')
    user_id = 1
    for data in users:
        if data['username'] == username:
            raise exceptions.ValutaTradeExceptions(
                f'Имя пользователя \'{username}\' уже занято'
            )
        user_id = max(user_id, data['user_id'] + 1)

    user = models.User(user_id, username, '', '', datetime.now(timezone.utc))
    user.change_password(password)
    portfolio = models.Portfolio(user_id, {}, user)
    portfolios = db.read_data('portfolios')
    users.append(user.to_dict())
    portfolios.append(portfolio.to_dict())
    db.save_data('users', users)
    db.save_data('portfolios', portfolios)
    return user

@decorators.log_action()
def login(username:str, password:str):
    '''Возвращает User после проверки имени и пароля; состояние сессии не хранит'''
    for data in database.DatabaseManager().read_data('users'):
        if data['username'] == username:
            user = models.User.from_dict(data)
            if not user.verify_password(password):
                raise exceptions.InvalidPasswordError(username)
            return user
    raise exceptions.UserNotFoundError(username)

def show_portfolio(user:models.User, base:str=None):
    '''
    Возвращает строки кошельков и итог в выбранной базе по актуальным курсам

    Для пустого портфеля возвращает пустой список и нулевой итог
    '''
    if user is None:
        raise exceptions.ValutaTradeExceptions('Пользователь не залогинен')
    
    if base is None:
        base = settings.SettingsLoader.get('base_currency', 'USD')
    currencies.get_currency(base)
    portfolio = _load_portfolio(user)
    rows = []
    for code, wallet in portfolio.wallets.items():
        rate, _ = get_rate(code, base)
        rows.append({
            'currency_code': code,
            'balance': wallet.balance,
            'value': wallet.balance * rate,
        })
    return {
        'username': user.username,
        'base': base,
        'wallets': rows,
        'total': sum(row['value'] for row in rows),
    }

@decorators.log_action()
def buy(user:models.User, currency_code:str, amount:float):
    '''
    Увеличивает баланс покупаемой валюты и сохраняет портфель

    Возвращает сумму, баланс до и после, курс и оценочную стоимость в USD. Средства
    из USD-кошелька не списываются
    '''
    currencies.get_currency(currency_code)

    if not utils.is_positive(amount):
        raise exceptions.ValutaTradeExceptions(
            '\'amount\' должен быть положительным числом'
        )

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
        'base': 'USD',
        'before': before,
        'after': wallet.balance,
        'estimated_value': amount * rate,
    }

@decorators.log_action()
def sell(user:models.User, currency_code:str, amount:float):
    '''
    Уменьшает баланс продаваемой валюты и сохраняет портфель

    Возвращает баланс до и после, курс и оценочную выручку в USD. При нехватке
    средств возникает InsufficientFundsError
    '''
    currencies.get_currency(currency_code)

    if not utils.is_positive(amount):
        raise exceptions.ValutaTradeExceptions(
            '\'amount\' должен быть положительным числом'
        )

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
        'base': 'USD',
        'before': before,
        'after': wallet.balance,
        'estimated_value': amount * rate,
    }

def get_rate(from_code:str, to_code:str):
    '''
    Возвращает курс и ISO-время из свежего кеша либо обновляет его через Parser

    Проверяет коды валют и TTL. Если свежий курс получить не удалось, выбрасывает
    ApiRequestError
    '''
    currencies.get_currency(from_code)
    currencies.get_currency(to_code)
    if from_code == to_code:
        timestamp = datetime.now(timezone.utc).isoformat()
        return 1.0, timestamp
    db = database.DatabaseManager()
    ttl = settings.SettingsLoader.get('rates_ttl_seconds', 300)
    cache = db.read_data('rates')
    cached = utils.parse_rate(cache['pairs'], from_code, to_code, ttl)
    if cached is not None:
        return cached

    result = updater.create_updater().run_update()
    cache = db.read_data('rates')
    cached = utils.parse_rate(cache['pairs'], from_code, to_code, ttl)
    if cached is None:
        reasons = '; '.join(error['message'] for error in result['errors'])
        raise exceptions.ApiRequestError(
            f'Курс {from_code}→{to_code} не получен. {reasons}'
        )
    return cached


def show_rates(currency_code=None, top=None, base=None):
    '''
    Возвращает строки локального кеша с фильтрами currency_code, top и base

    Top выбирает криптовалюты по стоимости в USD; сетевые запросы не выполняются
    '''
    if not base:
        base = settings.SettingsLoader.get('base_currency', 'USD')
    currencies.get_currency(base)
    if top is not None:
        if isinstance(top, bool) or not isinstance(top, int) or top <= 0:
            raise exceptions.ValutaTradeExceptions(
                'top должен быть положительным целым числом'
            )

    cache = database.DatabaseManager().read_data('rates')
    pairs = cache['pairs']
    if not pairs:
        raise exceptions.ValutaTradeExceptions(
            'Локальный кеш курсов пуст. '
            'Выполните \'update-rates\', чтобы загрузить данные.'
        )

    # Выбрать валюты для показа
    available_codes = set()
    for pair in pairs:
        try:
            original, target = pair.split('_')
        except ValueError as e:
            raise exceptions.ValutaTradeExceptions(
                f'Некорректная валютная пара {pair}'
            ) from e
        available_codes.update((original, target))
    if currency_code:
        if currency_code not in available_codes:
            raise exceptions.ValutaTradeExceptions(
                f'Курс для \'{currency_code}\' не найден в кеше.'
            )
        currencies.get_currency(currency_code)
        selected_codes = [currency_code]
    else:
        selected_codes = sorted(available_codes - {base})

    # Для top отобрать криптовалюты и упорядочить по стоимости в USD
    # "--top это N самых дорогих криптовалют по курсу к USD,
    # фиатные валюты в выборку не входят"
    usd_rates = {}
    if top is not None:
        for code in selected_codes:
            currency = currencies.get_currency(code)
            if not isinstance(currency, currencies.CryptoCurrency):
                continue
            parsed = utils.parse_rate(pairs, code, 'USD')
            if parsed is None:
                raise exceptions.ValutaTradeExceptions(
                    f'Для top необходим курс {code}→USD в кеше.'
                )
            usd_rates[code] = parsed
        selected_codes = sorted(
            usd_rates, key=lambda code: usd_rates[code][0], reverse=True
        )[:top]

    # Пересчитать выбранные валюты в базу отображения
    rows = []
    for code in selected_codes:
        currencies.get_currency(code)
        if base == 'USD' and code in usd_rates:
            parsed = usd_rates[code]
        else:
            parsed = utils.parse_rate(pairs, code, base)
        if parsed is None:
            raise exceptions.ValutaTradeExceptions(
                f'Курс {code}→{base} отсутствует в кеше. Выполните update-rates.'
            )
        rate, updated_at = parsed
        rows.append({
            'pair': f'{code}_{base}',
            'rate': rate,
            'updated_at': updated_at,
        })
    return {'rows': rows, 'base': base, 'last_refresh': cache.get('last_refresh')}
