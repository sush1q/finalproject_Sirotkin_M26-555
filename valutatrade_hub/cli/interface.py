import prompt
import shlex

from ..core import usecases

def register(args:list[str]):
    username_idx = args.index('--username')
    password_idx = args.index('--password')

    if len(args) > 4:
        raise ValueError('Переданы лишние аргументы')
    if username_idx not in [0,2] or password_idx not in [0,2]:
        raise ValueError('Ошибка расположения аргументов')
    
    new_user = usecases.register(args[username_idx+1], args[password_idx+1])
    print(f'Пользователь \'{new_user.username}\' зарегистрирован (id={new_user.id}). Войдите: login --username {new_user.username} --password **** ')
    

def login(args:list[str]):
    username_idx = args.index('--username')
    password_idx = args.index('--password')

    if len(args) > 4:
        raise ValueError('Переданы лишние аргументы')
    if username_idx not in [0,2] or password_idx not in [0,2]:
        raise ValueError('Ошибка расположения аргументов')

    user = usecases.login(args[username_idx+1], args[password_idx+1])
    print(f'Вы вошли как \'{user.username}\'')

def show_portfolio(args:list[str]):
    len_args = len(args)
    base_arg = '--base'
    portfolio = None

    if len_args == 0:
        portfolio = usecases.show_portfolio()
    elif len_args == 2 and args[0] == base_arg:
        portfolio = usecases.show_portfolio(args[1])
    else:
        raise ValueError('Ошибка указания аргументов')

    # Портфель пользователя 'alice' (база: USD):
    # - USD: 150.00  → 150.00 USD
    # - BTC: 0.0500  → 2965.00 USD
    # - EUR: 200.00  → 214.00 USD
    # ---------------------------------
    # ИТОГО: 3,329.00 USD 
    raise NotImplementedError

def buy(args:list[str]):
    currency_idx = args.index('--currency')
    amount_idx = args.index('--amount')

    if len(args) > 4:
        raise ValueError('Переданы лишние аргументы')
    if currency_idx not in [0,2] or amount_idx not in [0,2]:
        raise ValueError('Ошибка расположения аргументов')
    
    amount_val = None
    try:
        amount_val = float(args[amount_idx]+1)
    except:
        raise ValueError('Переданое значение не относится к требуемому типу')
    
    buy = usecases.buy(args[currency_idx+1], amount_val)
    
    raise NotImplementedError

def sell(args:list[str]):
    raise NotImplementedError

def get_rate(args:list[str]):
    raise NotImplementedError

def execute_command(cmd: str):
    print(cmd)
    args = shlex.split(cmd)
    if not args:
        return
    
    match args[0]:
        case 'register':
            register(args[1:])
        case 'login':
            login(args[1:])
        case 'show-portfolio':
            show_portfolio(args[1:])
        case 'buy':
            buy(args[1:])
        case 'sell':
            sell(args[1:])
        case 'get-rate':
            get_rate(args[1:])
        case _:
            print(f'Функции {args[0]} нет')

def main():
    while True:
        try:
            user_input = prompt.string('> ')
            if execute_command(user_input):
                return 0
        except (EOFError, KeyboardInterrupt):
            return 0

