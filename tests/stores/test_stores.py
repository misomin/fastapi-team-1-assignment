import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from wapang.app.items.models import Item


STORE_BODY = {
    "store_name": "와플상점",
    "address": "서울시 관악구",
    "email": "store@example.com",
    "phone_number": "010-1234-5678",
    "delivery_fee": 3000,
}


def auth(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def create_store(client: TestClient, access_token: str, **changes):
    return client.post(
        "/api/stores",
        headers=auth(access_token),
        json={**STORE_BODY, **changes},
    )


def another_user_token(client: TestClient) -> str:
    credentials = {
        "email": "other@example.com",
        "password": "password123",
    }
    assert client.post("/api/users", json=credentials).status_code == 201
    response = client.post("/api/auth/tokens", json=credentials)
    assert response.status_code == 200
    return response.json()["access_token"]


def assert_error(response, status_code: int, code: str, message: str):
    assert response.status_code == status_code
    assert response.json() == {
        "error_code": code,
        "error_msg": message,
    }


def test_create_and_get_store(client: TestClient, access_token: str):
    created = create_store(client, access_token)

    assert created.status_code == 201
    store_id = created.json()["id"]
    assert created.json() == {"id": store_id, **STORE_BODY}

    fetched = client.get(f"/api/stores/{store_id}")
    assert fetched.status_code == 200
    assert fetched.json() == created.json()


def test_create_store_requires_authentication(client: TestClient):
    assert_error(
        client.post("/api/stores", json=STORE_BODY),
        401, "ERR_005", "UNAUTHENTICATED",
    )
    assert_error(
        client.post(
            "/api/stores",
            headers={"Authorization": "invalid"},
            json=STORE_BODY,
        ),
        400, "ERR_006", "BAD AUTHORIZATION HEADER",
    )
    assert_error(
        client.post(
            "/api/stores",
            headers=auth("invalid"),
            json=STORE_BODY,
        ),
        401, "ERR_007", "INVALID TOKEN",
    )


def test_create_store_rejects_missing_field(
    client: TestClient, access_token: str
):
    body = {key: value for key, value in STORE_BODY.items() if key != "store_name"}
    assert_error(
        client.post("/api/stores", headers=auth(access_token), json=body),
        400, "ERR_002", "MISSING REQUIRED FIELDS",
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"store_name": "가나"},
        {"store_name": "가" * 21},
        {"address": "가" * 101},
        {"email": "invalid"},
        {"phone_number": "010-123-5678"},
        {"delivery_fee": -1},
        {"delivery_fee": True},
    ],
)
def test_create_store_rejects_invalid_fields(
    client: TestClient, access_token: str, changes: dict
):
    assert_error(
        create_store(client, access_token, **changes),
        400, "ERR_003", "INVALID FIELD FORMAT",
    )


def test_create_store_rejects_second_store(
    client: TestClient, access_token: str
):
    assert create_store(client, access_token).status_code == 201

    assert_error(
        create_store(
            client,
            access_token,
            store_name="다른상점",
            email="other-store@example.com",
            phone_number="010-9876-5432",
        ),
        409, "ERR_008", "STORE ALREADY EXISTS",
    )


@pytest.mark.parametrize("field", ["store_name", "email", "phone_number"])
def test_create_store_rejects_duplicate_info(
    client: TestClient, access_token: str, field: str
):
    assert create_store(client, access_token).status_code == 201
    other_token = another_user_token(client)

    other_values = {
        "store_name": "다른상점",
        "email": "other-store@example.com",
        "phone_number": "010-9876-5432",
        field: STORE_BODY[field],
    }
    assert_error(
        create_store(client, other_token, **other_values),
        409, "ERR_009", "STORE INFO CONFLICT",
    )


def test_update_store(client: TestClient, access_token: str):
    store_id = create_store(client, access_token).json()["id"]

    response = client.patch(
        f"/api/stores/{store_id}",
        headers=auth(access_token),
        json={"store_name": "새와플상점", "delivery_fee": 5000},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": store_id,
        **STORE_BODY,
        "store_name": "새와플상점",
        "delivery_fee": 5000,
    }
    assert client.get(f"/api/stores/{store_id}").json() == response.json()


def test_update_store_requires_a_field(
    client: TestClient, access_token: str
):
    store_id = create_store(client, access_token).json()["id"]

    assert_error(
        client.patch(
            f"/api/stores/{store_id}",
            headers=auth(access_token),
            json={},
        ),
        400, "ERR_002", "MISSING REQUIRED FIELDS",
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"store_name": None},
        {"store_name": "가나"},
        {"address": None},
        {"address": "가" * 101},
        {"email": None},
        {"email": "invalid"},
        {"phone_number": None},
        {"phone_number": "123"},
        {"delivery_fee": None},
        {"delivery_fee": -1},
        {"delivery_fee": True},
    ],
)
def test_update_store_rejects_invalid_fields(
    client: TestClient, access_token: str, changes: dict
):
    store_id = create_store(client, access_token).json()["id"]

    assert_error(
        client.patch(
            f"/api/stores/{store_id}",
            headers=auth(access_token),
            json=changes,
        ),
        400, "ERR_003", "INVALID FIELD FORMAT",
    )


@pytest.mark.parametrize("field", ["store_name", "email", "phone_number"])
def test_update_store_rejects_duplicate_info(
    client: TestClient, access_token: str, field: str
):
    assert create_store(client, access_token).status_code == 201
    other_token = another_user_token(client)

    other_store = create_store(
        client,
        other_token,
        store_name="다른상점",
        email="other-store@example.com",
        phone_number="010-9876-5432",
    )
    other_id = other_store.json()["id"]

    assert_error(
        client.patch(
            f"/api/stores/{other_id}",
            headers=auth(other_token),
            json={field: STORE_BODY[field]},
        ),
        409, "ERR_009", "STORE INFO CONFLICT",
    )


def test_update_store_checks_ownership(
    client: TestClient, access_token: str
):
    store_id = create_store(client, access_token).json()["id"]
    other_token = another_user_token(client)

    assert_error(
        client.patch(
            f"/api/stores/{store_id}",
            headers=auth(other_token),
            json={"delivery_fee": 1},
        ),
        403, "ERR_011", "NO STORE OWNED",
    )

    other_store = create_store(
        client,
        other_token,
        store_name="다른상점",
        email="other-store@example.com",
        phone_number="010-9876-5432",
    )
    other_id = other_store.json()["id"]

    assert_error(
        client.patch(
            f"/api/stores/{other_id}",
            headers=auth(access_token),
            json={"delivery_fee": 1},
        ),
        403, "ERR_012", "NOT YOUR STORE",
    )

    assert_error(
        client.patch(
            "/api/stores/missing",
            headers=auth(access_token),
            json={"delivery_fee": 1},
        ),
        404, "ERR_010", "STORE NOT FOUND",
    )


def test_get_store_and_items_not_found(client: TestClient):
    assert_error(
        client.get("/api/stores/missing"),
        404, "ERR_010", "STORE NOT FOUND",
    )
    assert_error(
        client.get("/api/stores/missing/items"),
        404, "ERR_010", "STORE NOT FOUND",
    )


def test_list_store_items(
    client: TestClient, db_session: Session, access_token: str
):
    store_id = create_store(client, access_token).json()["id"]
    assert client.get(f"/api/stores/{store_id}/items").json() == []

    first = Item(store_id=store_id, name="와플", price=10000, stock=15)
    second = Item(store_id=store_id, name="시럽", price=3000, stock=8)
    db_session.add_all([first, second])
    db_session.commit()

    response = client.get(f"/api/stores/{store_id}/items")
    assert response.status_code == 200
    assert response.json() == [
        {"id": first.id, "item_name": "와플", "price": 10000, "stock": 15},
        {"id": second.id, "item_name": "시럽", "price": 3000, "stock": 8},
    ]