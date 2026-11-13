import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from wapang.app.items.models import Item
from wapang.app.stores.models import Store
from wapang.app.users.models import User


@pytest.fixture
def store(db_session: Session, user: User) -> Store:
    store = Store(
        user_id=user.id,
        name="Waffle Store",
        address="Seoul",
        email="store@example.com",
        phone_number="010-1234-5678",
        delivery_fee=3000,
    )
    db_session.add(store)
    db_session.commit()
    return store

@pytest.fixture
def item(db_session: Session, store: Store) -> Item:
    item = Item(store_id=store.id, name="Waffle", price=10000, stock=5)
    db_session.add(item)
    db_session.commit()
    return item

def test_create_item(
    client: TestClient,
    db_session: Session,
    store: Store,
    access_token: str,
):
    response = client.post(
        "/api/items",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"item_name": "Syrup", "price": 3000, "stock": 8},
    )

    assert response.status_code == 201
    assert response.json()["item_name"] == "Syrup"

    saved_item = db_session.get(Item, response.json()["id"])
    assert saved_item is not None
    assert saved_item.store_id == store.id

def test_list_items(client: TestClient, item: Item):
    response = client.get("/api/items", params={"in_stock": "true"})

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": item.id,
            "item_name": "Waffle",
            "price": 10000,
            "stock": 5,
            "store_id": item.store_id,
            "store_name": "Waffle Store",
        }
    ]

def test_update_item(
    client: TestClient, item: Item, access_token: str
):
    response = client.patch(
        f"/api/items/{item.id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"price": 12000},
    )

    assert response.status_code == 200
    assert response.json()["price"] == 12000
    assert response.json()["item_name"] == "Waffle"

def test_delete_item(
    client: TestClient,
    db_session: Session,
    item: Item,
    access_token: str,
):
    response = client.delete(
        f"/api/items/{item.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 204
    assert db_session.get(Item, item.id) is None

@pytest.mark.parametrize(
    ("body", "error_code"),
    [
        ({"price": 1000, "stock": 1}, "ERR_002"),
        ({"item_name": "A", "price": 1000, "stock": 1}, "ERR_003"),
        ({"item_name": "Valid", "price": -1, "stock": 1}, "ERR_003"),
        ({"item_name": "Valid", "price": 1000, "stock": -1}, "ERR_003"),
        ({"item_name": "Valid", "price": "1000", "stock": 1}, "ERR_003"),
    ],
)
def test_create_item_invalid_body(
    client: TestClient, store: Store, access_token: str,
    body: dict, error_code: str
):
    response = client.post(
        "/api/items",
        headers={"Authorization": f"Bearer {access_token}"},
        json=body,
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == error_code

def test_create_item_without_store(
    client: TestClient, access_token: str
):
    response = client.post(
        "/api/items",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"item_name": "Waffle", "price": 10000, "stock": 5},
    )
    assert response.status_code == 403
    assert response.json()["error_code"] == "ERR_011"

def test_update_item_empty(
    client: TestClient, item: Item, access_token: str
):
    response = client.patch(
        f"/api/items/{item.id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={},
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "ERR_002"

def test_update_item_not_found(
    client: TestClient, store: Store, access_token: str
):
    response = client.patch(
        "/api/items/missing-item",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"price": 12000},
    )
    assert response.status_code == 404
    assert response.json()["error_code"] == "ERR_013"

def test_delete_item_not_found(client: TestClient, access_token: str):
    response = client.delete(
        "/api/items/missing-item",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["error_code"] == "ERR_013"

def test_list_items_filters(
    client: TestClient, db_session: Session, item: Item
):
    db_session.add_all([
        Item(store_id=item.store_id, name="Cheap", price=2000, stock=0),
        Item(store_id=item.store_id, name="Expensive", price=20000, stock=3),
    ])
    db_session.commit()

    response = client.get(
        "/api/items",
        params={
            "store_id": item.store_id,
            "min_price": 9000,
            "max_price": 11000,
            "in_stock": "true",
        },
    )

    assert response.status_code == 200
    assert [entry["id"] for entry in response.json()] == [item.id]

def test_list_items_unknown_store(client: TestClient):
    response = client.get(
        "/api/items", params={"store_id": "missing-store"}
    )
    assert response.status_code == 404
    assert response.json()["error_code"] == "ERR_010"

@pytest.fixture
def other_item(db_session: Session) -> Item:
    other_user = User(
        email="other@example.com",
        hashed_password="unused-for-this-test",
    )
    db_session.add(other_user)
    db_session.flush()

    other_store = Store(
        user_id=other_user.id,
        name="Other Store",
        address="Busan",
        email="other-store@example.com",
        phone_number="010-9999-8888",
        delivery_fee=2000,
    )
    db_session.add(other_store)
    db_session.flush()

    product = Item(
        store_id=other_store.id,
        name="Other Product",
        price=5000,
        stock=4,
    )
    db_session.add(product)
    db_session.commit()
    return product

def test_update_other_stores_item(
    client: TestClient, store: Store, other_item: Item, access_token: str
):
    response = client.patch(
        f"/api/items/{other_item.id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"price": 6000},
    )
    assert response.status_code == 403
    assert response.json()["error_code"] == "ERR_014"

def test_delete_other_stores_item(
    client: TestClient, store: Store, other_item: Item, access_token: str
):
    response = client.delete(
        f"/api/items/{other_item.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 403
    assert response.json()["error_code"] == "ERR_014"

def test_update_item_without_store(
    client: TestClient, access_token: str
):
    response = client.patch(
        "/api/items/any-item",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"price": 6000},
    )
    assert response.status_code == 403
    assert response.json()["error_code"] == "ERR_011"

@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        (
            "POST",
            "/api/items",
            {"item_name": "Waffle", "price": 1000, "stock": 1},
        ),
        ("PATCH", "/api/items/any-item", {"price": 1000}),
        ("DELETE", "/api/items/any-item", None),
    ],
)

@pytest.mark.parametrize(
    ("authorization", "status_code", "error_code"),
    [
        (None, 401, "ERR_005"),
        ("bad-header", 400, "ERR_006"),
        ("Bearer invalidtoken", 401, "ERR_007"),
    ],
)

def test_item_write_requires_valid_token(
    client: TestClient,
    method: str,
    path: str,
    body: dict | None,
    authorization: str | None,
    status_code: int,
    error_code: str,
):
    headers = (
        {"Authorization": authorization}
        if authorization is not None
        else {}
    )
    response = client.request(
        method, path, headers=headers, json=body
    )

    assert response.status_code == status_code
    assert response.json()["error_code"] == error_code

@pytest.mark.parametrize(
    "body",
    [
        {"item_name": "A"},
        {"price": -1},
        {"stock": -1},
        {"price": "1000"},
        {"stock": None},
    ],
)
def test_update_item_invalid_fields(
    client: TestClient, item: Item, access_token: str, body: dict
):
    response = client.patch(
        f"/api/items/{item.id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=body,
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "ERR_003"


def test_update_item_name(
    client: TestClient, db_session: Session, item: Item, access_token: str
):
    response = client.patch(
        f"/api/items/{item.id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"item_name": "New Waffle"},
    )

    assert response.status_code == 200
    assert response.json()["item_name"] == "New Waffle"
    assert db_session.get(Item, item.id).name == "New Waffle"