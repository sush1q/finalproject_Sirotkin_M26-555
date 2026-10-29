from functools import wraps


def log_action(verbose=True):
    def wrapper(func):
        @wraps(func)
        def real_wrapper(*args, **kwargs):
            try:
                ret = func(args, kwargs)
                raise NotImplementedError
                return ret   
            except Exception as e:
                print(f'Получили исключение {e}')
                raise e from e
        return real_wrapper
    return wrapper
