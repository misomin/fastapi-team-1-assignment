from fastapi.testclient import TestClient
from types import SimpleNamespace
from wapang.app.users.models import User
from wapang.app.users.repositories import UserRepository
import pytest

# TEST POST /api/users
def test_signup(
    client: TestClient
):
    req = {
        "email": "test1234@snu.ac.kr",
        "password": "password123"
    }

    res = client.post("/api/users", json=req)
    res_json = res.json()
    
    assert res.status_code == 201
    assert res_json["id"] is not None
    assert res_json["email"] == "test1234@snu.ac.kr"
    
    # 로그인 테스트
    res = client.post("/api/auth/tokens", json=req)
    res_json = res.json()
    
    assert res.status_code == 200

def test_signup_missing_email(
    client: TestClient
):
    req = {
        "password": "password123"
    }

    res = client.post("/api/users", json=req)
    res_json = res.json()
    
    assert res.status_code == 400
    assert res_json["error_code"] == "ERR_002"
    assert res_json["error_msg"] == "MISSING REQUIRED FIELDS"

def test_signup_missing_password(
    client: TestClient
):
    req = {
        "email": "test1234@snu.ac.kr"
    }

    res = client.post("/api/users", json=req)
    res_json = res.json()
    
    assert res.status_code == 400
    assert res_json["error_code"] == "ERR_002"
    assert res_json["error_msg"] == "MISSING REQUIRED FIELDS"

def test_signup_invalid_email(
    client: TestClient
):
    req = {
        "email": "test.snu.ac.kr",
        "password": "password123"
    }

    res = client.post("/api/users", json=req)
    res_json = res.json()
    
    assert res.status_code == 400
    assert res_json["error_code"] == "ERR_003"
    assert res_json["error_msg"] == "INVALID FIELD FORMAT"

def test_signup_short_password(
    client: TestClient
):
    req = {
        "email": "test1234@snu.ac.kr",
        "password": "short"
    }

    res = client.post("/api/users", json=req)
    res_json = res.json()
    
    assert res.status_code == 400
    assert res_json["error_code"] == "ERR_003"
    assert res_json["error_msg"] == "INVALID FIELD FORMAT"

def test_signup_long_password(
    client: TestClient
):
    req = {
        "email": "test1234@snu.ac.kr",
        "password": "longpasswordlongpassword"
    }

    res = client.post("/api/users", json=req)
    res_json = res.json()
    
    assert res.status_code == 400
    assert res_json["error_code"] == "ERR_003"
    assert res_json["error_msg"] == "INVALID FIELD FORMAT"


def test_signup_email_conflict(
    client: TestClient,
    user: User
):
    req = {
        "email": "test1234@snu.ac.kr",
        "password": "password321"
    }

    res = client.post("/api/users", json=req)
    res_json = res.json()

    assert res.status_code == 409
    assert res_json["error_code"] == "ERR_004"
    assert res_json["error_msg"] == "EMAIL ALREADY EXISTS"
    
# TEST GET /api/users/me
def test_get_me(
    client: TestClient,
    access_token: str
):
    auth_header = {"Authorization": f"Bearer {access_token}"}
    
    res = client.get("/api/users/me", headers=auth_header)
    
    assert res.status_code == 200
    
def test_get_me_without_header(
    client: TestClient
):
    res = client.get("/api/users/me")
    res_json = res.json()
    
    assert res.status_code == 401
    assert res_json["error_code"] == "ERR_005"
    assert res_json["error_msg"] == "UNAUTHENTICATED"
    
def test_get_me_invalid_header(
    client: TestClient,
    access_token: str
):
    invalid_header = {"Authorization": f"{access_token}"}
    
    res = client.get("/api/users/me", headers=invalid_header)
    res_json = res.json()
    
    assert res.status_code == 400
    assert res_json["error_code"] == "ERR_006"
    assert res_json["error_msg"] == "BAD AUTHORIZATION HEADER"
    
def test_get_me_invalid_token(
    client: TestClient,
):
    auth_header = {"Authorization": f"Bearer invalidtoken"}
    
    res = client.get("/api/users/me", headers=auth_header)
    res_json = res.json()
    
    assert res.status_code == 401
    assert res_json["error_code"] == "ERR_007"
    assert res_json["error_msg"] == "INVALID TOKEN"

def test_update_me(client: TestClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.patch(
        "/api/users/me",
        headers=headers,
        json={"nickname": "waffle"},
    )

    assert response.status_code == 200
    assert response.json()["nickname"] == "waffle"

    profile = client.get("/api/users/me", headers=headers)
    assert profile.json()["nickname"] == "waffle"

def test_update_me_empty_request(client: TestClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.patch("/api/users/me", headers=headers, json={})

    assert response.status_code == 400
    assert response.json() == {
        "error_code": "ERR_002",
        "error_msg": "MISSING REQUIRED FIELDS",
    }

@pytest.mark.parametrize(
    "body",
    [
        {"nickname": "a" * 21},
        {"address": "a" * 101},
        {"phone_number": "123-4567-8901"},
        {"phone_number": None},
    ],
)
def test_update_me_invalid_fields(
    client: TestClient, access_token: str, body: dict
):
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.patch("/api/users/me", headers=headers, json=body)

    assert response.status_code == 400
    assert response.json()["error_code"] == "ERR_003"

def test_update_me_without_token(client: TestClient):
    response = client.patch("/api/users/me", json={"nickname": "waffle"})

    assert response.status_code == 401
    assert response.json()["error_code"] == "ERR_005"

def test_update_me_preserves_other_fields(
    client: TestClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}

    first = client.patch(
        "/api/users/me",
        headers=headers,
        json={"nickname": "waffle"},
    )
    second = client.patch(
        "/api/users/me",
        headers=headers,
        json={"address": "Seoul National University"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["nickname"] == "waffle"
    assert second.json()["address"] == "Seoul National University"

def test_update_me_bad_authorization_header(
    client: TestClient, access_token: str
):
    response = client.patch(
        "/api/users/me",
        headers={"Authorization": access_token},
        json={"nickname": "waffle"},
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "ERR_006"

def test_update_me_invalid_token(client: TestClient):
    response = client.patch(
        "/api/users/me",
        headers={"Authorization": "Bearer invalidtoken"},
        json={"nickname": "waffle"},
    )

    assert response.status_code == 401
    assert response.json()["error_code"] == "ERR_007"


def test_get_my_orders(client: TestClient, access_token: str, user: User, monkeypatch):
    def fake_orders(self, user_id: str):
        assert user_id == user.id
        return [
            SimpleNamespace(id="order-1", total_price=41000, status="ORDERED"),
            SimpleNamespace(id="order-2", total_price=25000, status="COMPLETE"),
        ]

    monkeypatch.setattr(UserRepository, "get_orders_by_user_id", fake_orders)
    response = client.get(
        "/api/users/me/orders",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json() == [
        {"order_id": "order-1", "total_price": 41000, "status": "ORDERED"},
        {"order_id": "order-2", "total_price": 25000, "status": "COMPLETE"},
    ]


def test_get_my_orders_without_token(client: TestClient):
    response = client.get("/api/users/me/orders")
    assert response.status_code == 401
    assert response.json()["error_code"] == "ERR_005"


def test_get_my_orders_empty(client: TestClient, access_token: str, monkeypatch):
    monkeypatch.setattr(UserRepository, "get_orders_by_user_id", lambda self, user_id: [])
    response = client.get(
        "/api/users/me/orders",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == []


def test_get_my_orders_bad_header(client: TestClient, access_token: str):
    response = client.get(
        "/api/users/me/orders", headers={"Authorization": access_token}
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "ERR_006"


def test_get_my_orders_invalid_token(client: TestClient):
    response = client.get(
        "/api/users/me/orders", headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "ERR_007"
