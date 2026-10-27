import prompt
import shlex
from prettytable import PrettyTable

from ..core import usecases, models, utils


def _parse_options(args:list, options:dict):
    if len(args) % 2:
        raise ValueError('Для каждого аргумента нужно указать значение')
    result = {}
    for index in range(0, len(args), 2):
        flag, value = args[index : index + 2]
        if flag not in options:
            raise ValueError(f'Неизвестный аргумент \'{flag}\'')
        if flag in result:
            raise ValueError(f'Аргумент \'{flag}\' указан повторно')
        result[flag] = value
    missing = [flag for flag, value in options.items() if value is None and flag not in result]
    if missing:
        raise ValueError('Не указаны обязательные аргументы: ' + ', '.join(missing))
    return options | result

def register(args:list):
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
    username = '--username'
    password = '--password'
    options = _parse_options(args, {username: None, password: None})
    user = usecases.login(options[username], options[password])
    print(f'Вы вошли как \'{user.username}\'')
    return user

def show_portfolio(args:list, user:models.User):
    base_opt = '--base'
    options = _parse_options(args, {base_opt: 'USD'})
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
        if not utils.is_positive(amount):
            raise ValueError
    except ValueError as e:
        raise ValueError('\'amount\' должен быть положительным числом') from e
    return (options[currency_opt], amount)

def _print_trade(result: dict, selling: bool):
    action = 'Продажа' if selling else 'Покупка'
    estimate = 'Оценочная выручка' if selling else 'Оценочная стоимость покупки'
    code = result['currency_code']
    print(
        f'{action} выполнена: {result['amount']:.8g} {code} '
        f'по курсу {result['rate']:,.2f} USD/{code}'
    )
    print('Изменения в портфеле:')
    print(f'- {code}: было {result['before']:.8g} → стало {result['after']:.8g}')
    print(f'{estimate}: {result['estimated_value']:,.2f} USD')

def buy(args:list, user:models.User):
    currency, amount = _parse_trade_options(args)
    _print_trade(usecases.buy(user, currency, amount), False)

def sell(args:list, user:models.User):
    currency, amount = _parse_trade_options(args)
    _print_trade(usecases.sell(user, currency, amount), True)

def get_rate(args:list):
    from_opt = '--from'
    to_opt = '--to'

    options = _parse_options(args, {from_opt: None, to_opt: None})
    original, target = options[from_opt], options[to_opt]
    rate, timestamp = usecases.get_rate(original, target)
    print(f'Курс {original}→{target}: {rate:.8g} (обновлено: {timestamp})')
    print(f'Обратный курс {target}→{original}: {1 / rate:.8g}')

def execute_command(cmd: str, current_user:models.User=None):
    args = shlex.split(cmd)
    if not args:
        return current_user
    command, options = args[0], args[1:]
    if command in {'show-portfolio', 'buy', 'sell'} and current_user is None:
        raise ValueError('Сначала выполните login')
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
        case _:
            print(f'Команда \'{command}\' не найдена')
    return current_user

def main():
    current_user = None
    while True:
        try:
            user_input = prompt.string('> ')
            current_user = execute_command(user_input, current_user)
        except (EOFError, KeyboardInterrupt):
            return 0
        except ValueError as e:
            print(f'Ошибка: {e}')
