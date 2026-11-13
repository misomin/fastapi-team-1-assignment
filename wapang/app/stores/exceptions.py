from wapang.common.exceptions import WapangException


class StoreAlreadyExistsException(WapangException):
    def __init__(self) -> None:
        super().__init__(409, "ERR_008", "STORE ALREADY EXISTS")


class StoreInfoConflictException(WapangException):
    def __init__(self) -> None:
        super().__init__(409, "ERR_009", "STORE INFO CONFLICT")


class StoreNotFoundException(WapangException):
    def __init__(self) -> None:
        super().__init__(404, "ERR_010", "STORE NOT FOUND")


class NoStoreOwnedException(WapangException):
    def __init__(self) -> None:
        super().__init__(403, "ERR_011", "NO STORE OWNED")


class NotYourStoreException(WapangException):
    def __init__(self) -> None:
        super().__init__(403, "ERR_012", "NOT YOUR STORE")