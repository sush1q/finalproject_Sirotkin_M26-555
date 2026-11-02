class ValutaTradeExceptions(Exception):
    pass

class InsufficientFundsError(ValutaTradeExceptions):
    def __init__(self, available, code, required):
        super().__init__(f'Недостаточно средств: доступно {available} {code}, требуется {required} {code}')

class CurrencyNotFoundError(ValutaTradeExceptions):
    def __init__(self, code):
        super().__init__(f"Неизвестная валюта '{code}'")

class ApiRequestError(ValutaTradeExceptions):
    def __init__(self, reason):
        super().__init__(f'Ошибка при обращении к внешнему API: {reason}')

class UserNotFoundError(ValutaTradeExceptions):
    def __init__(self, username):
        super().__init__(f'Пользователь "{username}" не найден')

class InvalidPasswordError(ValutaTradeExceptions):
    def __init__(self, username):
        super().__init__(f'Введен некорректный пароль для пользователя "{username}"')

class PortfolionotFoundError(ValutaTradeExceptions):
    def __init__(self, user_id):
        super().__init__(f'Портфель пользователя с id={user_id} не найден')
