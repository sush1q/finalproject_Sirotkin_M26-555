class ValutaTradeExceptions(Exception):
    '''Базовая ошибка приложения, которую CLI может показать пользователю'''
    pass

class InsufficientFundsError(ValutaTradeExceptions):
    '''Ошибка снятия суммы, превышающей доступный баланс кошелька'''
    def __init__(self, available, code, required):
        super().__init__(
            f'Недостаточно средств: доступно {available} {code}, '
            f'требуется {required} {code}'
        )

class CurrencyNotFoundError(ValutaTradeExceptions):
    '''Ошибка неизвестного кода валюты'''
    def __init__(self, code):
        super().__init__(f"Неизвестная валюта '{code}'")

class ApiRequestError(ValutaTradeExceptions):
    '''Ошибка получения курсов от внешнего источника'''
    def __init__(self, reason):
        super().__init__(f'Ошибка при обращении к внешнему API: {reason}')

class UserNotFoundError(ValutaTradeExceptions):
    '''Ошибка входа с несуществующим именем пользователя'''
    def __init__(self, username):
        super().__init__(f'Пользователь "{username}" не найден')

class InvalidPasswordError(ValutaTradeExceptions):
    '''Ошибка входа с неверным паролем'''
    def __init__(self, username):
        super().__init__(f'Введен некорректный пароль для пользователя "{username}"')

class PortfolioNotFoundError(ValutaTradeExceptions):
    '''Ошибка отсутствующего портфеля пользователя'''
    def __init__(self, user_id):
        super().__init__(f'Портфель пользователя с id={user_id} не найден')
