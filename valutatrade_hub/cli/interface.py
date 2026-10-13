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
    raise NotImplementedError

def buy(args:list[str]):
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

