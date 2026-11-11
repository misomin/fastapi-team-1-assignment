from wapang.common.exceptions import WapangException

class InvalidAccountException(WapangException):
    def __init__(self) -> None:
        super().__init__(
            status_code=401,
            error_code="ERR_001",
            error_msg="Invalid account credentials"
        )

class UnauthenticatedException(WapangException):
    def __init__(self):
        super().__init__(
            status_code=401,
            error_code="ERR_005",
            error_msg="UNAUTHENTICATED"
        )

class BadAuthorizationHeaderException(WapangException):
    def __init__(self):
        super().__init__(
            status_code=400,
            error_code="ERR_006",
            error_msg="BAD AUTHORIZATION HEADER"
        )

class InvalidTokenException(WapangException):
    def __init__(self):
        super().__init__(
            status_code=401,
            error_code="ERR_007",
            error_msg="INVALID TOKEN"
        )