import shlex

import prompt
from prettytable import PrettyTable

from valutatrade_hub import logging_config
from valutatrade_hub.core import currencies, exceptions, models, usecases
from valutatrade_hub.infra import settings
from valutatrade_hub.parser_service import updater


def _parse_options(args:list, options:dict):
    if len(args) % 2:
        raise exceptions.ValutaTradeExceptions(
            'Для каждого аргумента нужно указать значение'
        )
    result = {}
    for index in range(0, len(args), 2):
        flag, value = args[index : index + 2]
        if flag not in options:
            raise exceptions.ValutaTradeExceptions(f'Неизвестный аргумент \'{flag}\'')
        if flag in result:
            raise exceptions.ValutaTradeExceptions(
                f'Аргумент \'{flag}\' указан повторно'
            )
        result[flag] = value
    missing = [
        flag for flag, value in options.items()
        if value is None and flag not in result
    ]
    if missing:
        raise exceptions.ValutaTradeExceptions(
            'Не указаны обязательные аргументы: ' + ', '.join(missing)
        )
    return options | result

def register(args:list):
    '''Разбирает опции регистрации и печатает результат создания пользователя.'''
    username = '--username'
    password = '--password'
    options = {username: None, password: None}
    
    options = _parse_options(args, options)
    user = usecases.register(options[username], options[password])
    print(
        f'Пользователь \'{user.username}\' зарегистрирован (id={user.id}). '
        f'Войдите: login --username {user.username} --password ****'
    )

def login(args:list):
    '''Проверяет опции входа, печатает результат и возвращает User для сессии CLI.'''
    username = '--username'
    password = '--password'
    options = _parse_options(args, {username: None, password: None})
    user = usecases.login(options[username], options[password])
    print(f'Вы вошли как \'{user.username}\'')
    return user

def show_portfolio(args:list, user:models.User):
    '''Печатает таблицу кошельков и общий итог в выбранной базовой валюте.'''
    base_opt = '--base'
    options = _parse_options(
        args, {base_opt: settings.SettingsLoader.get('base_currency', 'USD')}
    )
    result = usecases.show_portfolio(user, options[base_opt])
    
    base = result['base']
    print(f'Портфель пользователя \'{result['username']}\' (база: {base}):')
    if not result['wallets']:
        print('Портфель пуст. Кошельки создаются при первой покупке валюты.')
        return
    table = PrettyTable(['Валюта', 'Баланс', f'Стоимость в {base}'])
    for wallet in result['wallets']:
        table.add_row(
            [
                wallet['currency_code'],
                f'{wallet['balance']:.8g}',
                f'{wallet['value']:,.2f}',
            ]
        )
    print(table)
    print(f'ИТОГО: {result['total']:,.2f} {base}')

def _parse_trade_options(args: list):
    currency_opt = '--currency'
    amount_opt = '--amount'
    
    options = _parse_options(args, {currency_opt: None, amount_opt: None})
    try:
        amount = float(options[amount_opt])
    except (TypeError, ValueError) as e:
        raise exceptions.ValutaTradeExceptions(
            '\'amount\' должен быть положительным числом'
        ) from e
    return (options[currency_opt], amount)

def buy(args:list, user:models.User):
    '''Вызывает покупку и печатает изменение баланса и оценочную стоимость в USD.'''
    currency, amount = _parse_trade_options(args)
    result = usecases.buy(user, currency, amount)
    code = result['currency_code']
    print(
        f'Покупка выполнена: {result['amount']:.8g} {code} '
        f'по курсу {result['rate']:,.8g} USD/{code}'
    )
    print('Изменения в портфеле:')
    print(f'- {code}: было {result['before']:.8g} → стало {result['after']:.8g}')
    print(f'Оценочная стоимость покупки: {result['estimated_value']:,.2f} USD')

def sell(args:list, user:models.User):
    '''Вызывает продажу и печатает изменение баланса и оценочную выручку в USD.'''
    currency, amount = _parse_trade_options(args)
    result = usecases.sell(user, currency, amount)
    code = result['currency_code']
    print(
        f'Продажа выполнена: {result['amount']:.8g} {code} '
        f'по курсу {result['rate']:,.8g} USD/{code}'
    )
    print('Изменения в портфеле:')
    print(f'- {code}: было {result['before']:.8g} → стало {result['after']:.8g}')
    print(f'Оценочная выручка: {result['estimated_value']:,.2f} USD')

def get_rate(args:list):
    '''Печатает прямой и обратный курсы с временем обновления.'''
    from_opt = '--from'
    to_opt = '--to'

    options = _parse_options(args, {from_opt: None, to_opt: None})
    original, target = options[from_opt], options[to_opt]
    rate, timestamp = usecases.get_rate(original, target)
    print(f'Курс {original}→{target}: {rate:.8g} (обновлено: {timestamp})')
    print(f'Обратный курс {target}→{original}: {1 / rate:.8g}')

def update_rates(args:list):
    '''Обновляет выбранные источники и печатает итог с консольными логами Parser.'''
    source_opt = '--source'
    
    options = _parse_options(args, {source_opt: ''})
    service = updater.create_updater(options[source_opt])
    with logging_config.parser_console():
        result = service.run_update()
    if result['errors']:
        print(
            'Update completed with errors. Check '
            f'{settings.SettingsLoader.get('log_path', 'logs')}/parser.log for details.'
        )
        print(
            f'Total rates updated: {result['updated_count']}. '
            f'Last refresh: {result['last_refresh']}'
        )
    else:
        print(
            f'Update successful. Total rates updated: {result['updated_count']}. '
            f'Last refresh: {result['last_refresh']}'
        )

def show_rates(args:list):
    '''Печатает таблицу кеша с фильтрами валюты, количества криптовалют и базы.'''
    currency_opt = '--currency'
    top_opt = '--top'
    base_opt = '--base'
    
    options = _parse_options(args, {currency_opt: '', top_opt: '', base_opt: ''})
    top = None
    if options[top_opt]:
        try:
            top = int(options[top_opt])
        except ValueError as e:
            raise exceptions.ValutaTradeExceptions(
                'top должен быть положительным целым числом'
            ) from e
    result = usecases.show_rates(
        currency_code=options[currency_opt] or None,
        top=top,
        base=options[base_opt] or None,
    )
    print(f'Rates from cache (updated at {result['last_refresh']}):')
    table = PrettyTable(['Пара', 'Курс', 'Обновлён'])
    for row in result['rows']:
        table.add_row([row['pair'], f'{row['rate']:.10g}', row['updated_at']])
    print(table)

def execute_command(cmd: str, current_user:models.User=None):
    '''
    Разбирает одну команду и возвращает текущего пользователя.

    Доменные ошибки передаются основному циклу;
    Для операций портфеля требуется вход
    '''
    try:
        args = shlex.split(cmd)
    except ValueError as e:
        raise exceptions.ValutaTradeExceptions(f'Некорректная команда: {e}') from e
    if not args:
        return current_user
    command, options = args[0], args[1:]
    if command in {'show-portfolio', 'buy', 'sell'} and current_user is None:
        raise exceptions.ValutaTradeExceptions('Сначала выполните login')
    match command:
        case 'register':
            register(options)
        case 'login':
            return login(options)
        case 'show-portfolio':
            show_portfolio(options, current_user)
        case 'buy':
            buy(options, current_user)
        case 'sell':
            sell(options, current_user)
        case 'get-rate':
            get_rate(options)
        case 'update-rates':
            update_rates(options)
        case 'show-rates':
            show_rates(options)
        case _:
            print(f'Команда \'{command}\' не найдена')
    return current_user

def main():
    '''Основной цикл программы'''
    try:
        logging_config.setup_logging()
    except exceptions.ValutaTradeExceptions as e:
        print(f'Ошибка: {e}')
        return 1
    current_user = None
    while True:
        try:
            user_input = prompt.string('> ')
            current_user = execute_command(user_input, current_user)
        except exceptions.CurrencyNotFoundError as e:
            print(e)
            print('Доступные валюты: ' + ', '.join(currencies.currency_registry))
        except exceptions.ApiRequestError as e:
            print(e)
            print('Повторите попытку позже или проверьте подключение к сети.')
        except exceptions.InsufficientFundsError as e:
            print(e)
        except exceptions.ValutaTradeExceptions as e:
            print(f'Ошибка: {e}')
        except (EOFError, KeyboardInterrupt):
            return 0
