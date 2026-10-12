import prompt
import shlex


def execute_command(cmd: str):
    print(cmd)
    args = shlex.split(cmd)
    if not args:
        return
    
    match args[0]:
        case 'register':
            pass
        case 'login':
            pass
        case 'show-portfolio':
            pass
        case 'buy':
            pass
        case 'sell':
            pass
        case 'get-rate':
            pass
        case _:
            print(f'Функции {args[0]} нет')

def main():
    while True:
        try:
            user_input = prompt.string("> ")
            if execute_command(user_input):
                return 0
        except (EOFError, KeyboardInterrupt):
            return 0

