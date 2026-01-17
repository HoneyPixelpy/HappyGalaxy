from uuid import UUID


class BaseServiceException(Exception):
    """Базовое исключение для сервисов."""
    def __init__(self, detail: str, error_code: str = "service_error"):
        self.detail = detail
        self.error_code = error_code
        super().__init__(detail)


class WalletNotFoundException(BaseServiceException):
    """Кошелка не найдена."""
    def __init__(self, wallet_id: UUID):
        detail = f"Wallet with id {wallet_id} not found"
        super().__init__(detail, "wallet_not_found")


class TransactionsNotFoundException(BaseServiceException):
    """Транзакция не найдена."""
    def __init__(self, transaction_id: int):
        detail = f"Transaction with id {transaction_id} not found"
        super().__init__(detail, "transaction_not_found")


class NotIndepotentKeyException(BaseServiceException):
    """Недостаточно индипутентный ключ."""
    def __init__(self, detail: str = "Not indipotent key"):
        super().__init__(detail, "not_indepotent_key")


class ValidationException(BaseServiceException):
    """Ошибка валидации."""
    def __init__(self, detail: str):
        super().__init__(detail, "validation_error")


class DuplicateOperationException(BaseServiceException):
    """Дублирующая операция (idempotency error)."""
    def __init__(self, detail: str = "Duplicate operation detected"):
        super().__init__(detail, "duplicate_operation")
