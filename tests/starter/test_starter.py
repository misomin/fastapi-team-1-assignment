from unittest.mock import Mock
from uuid import UUID

import pytest

from wapang.app.users.models import User
from wapang.database import connection


def test_user_ids_are_distinct_uuid7(db_session):
    users = [User(email=f"user{i}@example.com", hashed_password="test-hash") for i in range(2)]
    db_session.add_all(users)
    db_session.flush()
    assert users[0].id != users[1].id
    assert all(UUID(user.id).version == 7 for user in users)


@pytest.mark.parametrize("body", [
    {"email": "invalid", "password": "password123"},
    {"email": "user@example.com", "password": 123},
    {"email": None, "password": "password123"},
])
def test_invalid_input_uses_assignment_error(client, body):
    response = client.post("/api/users", json=body)
    assert response.status_code == 400
    assert response.json() == {"error_code": "ERR_003", "error_msg": "INVALID FIELD FORMAT"}


def test_invalid_json_uses_assignment_error(client):
    response = client.post("/api/users", content="{", headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert response.json() == {"error_code": "ERR_003", "error_msg": "INVALID FIELD FORMAT"}


def test_db_requests_reuse_factory_and_manage_transactions(monkeypatch):
    successful, failed = Mock(), Mock()
    factory = Mock(side_effect=[successful, failed])
    monkeypatch.setattr(connection.database_manager, "session_factory", factory)
    create_engine = Mock(side_effect=AssertionError("Request must reuse the existing engine"))
    monkeypatch.setattr(connection, "create_engine", create_engine)
    first = connection.get_db_session()
    assert next(first) is successful
    with pytest.raises(StopIteration):
        next(first)
    successful.commit.assert_called_once()
    successful.rollback.assert_not_called()
    successful.close.assert_called_once()
    second = connection.get_db_session()
    assert next(second) is failed
    with pytest.raises(ValueError):
        second.throw(ValueError("request failed"))
    failed.rollback.assert_called_once()
    failed.commit.assert_not_called()
    failed.close.assert_called_once()
    assert factory.call_count == 2
    create_engine.assert_not_called()
