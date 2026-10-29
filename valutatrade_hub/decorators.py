from functools import wraps


def log_action(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            ret = func(args, kwargs)
            raise NotImplementedError
            return ret   
        except Exception as e:
            print(f'Получили исключение {e}')
            raise e from e
    return wrapper
