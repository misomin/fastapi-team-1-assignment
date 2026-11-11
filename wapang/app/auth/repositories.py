from typing import Annotated
from datetime import datetime

from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from wapang.database.connection import get_db_session
from wapang.app.auth.models import BlockedToken
from wapang.app.auth.exceptions import InvalidTokenException

class AuthRepository:
    def __init__(self, session: Annotated[Session, Depends(get_db_session)]) -> None:
        self.session = session

    def block_refresh_token(self, token: str, exp: datetime) -> None:
        if self.session.get(BlockedToken, token) is not None:
            raise InvalidTokenException()

        blocked_token = BlockedToken(
            token=token,
            expired_at=exp
        )
        self.session.add(blocked_token)
        try:
            self.session.flush()
        except IntegrityError as exc:
            # 다른 요청이 먼저 같은 토큰을 폐기한 경우도 인증 오류로 처리합니다.
            raise InvalidTokenException() from exc
