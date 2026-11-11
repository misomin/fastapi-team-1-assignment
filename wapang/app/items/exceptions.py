from wapang.common.exceptions import WapangException

class StoreNotFoundException(WapangException):
    def __init__(self):
        super().__init__(404, "ERR_010", "STORE NOT FOUND")

class NoStoreOwnedException(WapangException):
    def __init__(self):
        super().__init__(403, "ERR_011", "NO STORE OWNED")

class ItemNotFoundException(WapangException):
    def __init__(self):
        super().__init__(404, "ERR_013", "ITEM NOT FOUND")

class NotYourItemException(WapangException):
    def __init__(self):
        super().__init__(403, "ERR_014", "NOT YOUR ITEM")