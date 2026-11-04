from datetime import datetime, timezone
from functools import wraps
from inspect import signature

from valutatrade_hub import logging_config


def log_action(verbose=True):
    '''
    Логирует параметры и результат операции на уровне INFO
    При verbose=True добавляет доступные балансы до и после операции
    '''
    def wrapper(func):
        parameters = signature(func)
        @wraps(func)
        def real_wrapper(*args, **kwargs):
            logger = logging_config.get_logger()
            timestamp = datetime.now(timezone.utc).isoformat()
            fields = {
                'timestamp': timestamp,
                'action': func.__name__.upper(),
            }
            try:
                arguments = parameters.bind_partial(*args, **kwargs).arguments
                user = arguments.get('user')
                if user is not None:
                    fields['user_id'] = user.id
                elif 'username' in arguments:
                    fields['username'] = arguments['username']
                for key in ('currency_code', 'amount'):
                    if key in arguments:
                        fields[key] = arguments[key]
                ret = func(*args, **kwargs)
            except Exception as e:
                fields.update(
                    result='ERROR', error_type=type(e).__name__, error_message=str(e)
                )
                logger.info(
                    ' '.join(f'{key}={value!r}' for key, value in fields.items())
                )
                raise
            if isinstance(ret, dict):
                keys = ('rate', 'base')
                if verbose:
                    keys += ('before', 'after')
                for key in keys:
                    if key in ret:
                        fields[key] = ret[key]
            fields['result'] = 'OK'
            logger.info(' '.join(f'{key}={value!r}' for key, value in fields.items()))
            return ret
        return real_wrapper
    return wrapper
