from datetime import datetime

import pytest

from wapang.app.auth import utils
from wapang.app.auth.exceptions import InvalidTokenException
from wapang.app.auth.repositories import AuthRepository


def test_tokens_are_unique_in_same_second(monkeypatch):
    class FixedDatetime(datetime):
        @classmethod
        def now(cls):
            return cls(2026, 1, 1)

    monkeypatch.setattr(utils, "datetime", FixedDatetime)
    assert utils.issue_token("user-id", 15, "test-secret") != utils.issue_token("user-id", 15, "test-secret")


def test_refresh_rotates_tokens_and_rejects_reuse(client, token):
    headers = {"Authorization": f"Bearer {token['refresh_token']}"}
    response = client.get("/api/auth/tokens/refresh", headers=headers)
    assert response.status_code == 200
    rotated = response.json()
    assert rotated["refresh_token"] != token["refresh_token"]
    assert rotated["access_token"] != token["access_token"]
    rejected = client.get("/api/auth/tokens/refresh", headers=headers)
    assert rejected.status_code == 401
    assert rejected.json() == {"error_code": "ERR_007", "error_msg": "INVALID TOKEN"}
    response = client.get("/api/auth/tokens/refresh", headers={"Authorization": f"Bearer {rotated['refresh_token']}"})
    assert response.status_code == 200


@pytest.mark.parametrize("operation", ["refresh", "delete"])
def test_logged_out_refresh_token_is_rejected(client, token, operation):
    headers = {"Authorization": f"Bearer {token['refresh_token']}"}
    response = client.delete("/api/auth/tokens", headers=headers)
    assert response.status_code == 204
    assert response.content == b""
    if operation == "refresh":
        response = client.get("/api/auth/tokens/refresh", headers=headers)
    else:
        response = client.delete("/api/auth/tokens", headers=headers)
    assert response.status_code == 401
    assert response.json() == {"error_code": "ERR_007", "error_msg": "INVALID TOKEN"}


def test_blocked_token_insert_race_is_auth_error(db_session, monkeypatch):
    repository = AuthRepository(db_session)
    expires = datetime(2030, 1, 1)
    repository.block_refresh_token("same-token", expires)
    db_session.commit()
    # 다른 요청이 사전 조회 직후 토큰을 폐기한 상황을 재현합니다.
    monkeypatch.setattr(db_session, "get", lambda *args: None)
    with pytest.raises(InvalidTokenException):
        repository.block_refresh_token("same-token", expires)
    db_session.rollback()
