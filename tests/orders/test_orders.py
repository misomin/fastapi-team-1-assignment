"""주문 API 테스트. 팀 저장소의 tests/orders/test_orders.py에 넣으세요.

tests/conftest.py의 client/db_session/access_token fixture를 사용합니다.
로컬 MySQL 대신 테스트마다 새로운 메모리 SQLite DB를 사용합니다.
"""

import pytest
from sqlalchemy import delete, func, select

from wapang.app.orders.repositories import OrderRepository
from wapang.common.exceptions import WapangException
from wapang.database.models import Item, Order, OrderItem, OrderStore, Store, User


@pytest.fixture
def headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def catalog(db_session):
    """상점/상품 API 구현 여부와 무관하게 테스트 데이터를 준비합니다."""
    stores = [
        Store(
            user=User(email=f"seller{i}@example.com", hashed_password="test-hash"),
            name=f"store{i}",
            address="Seoul",
            email=f"store{i}@example.com",
            phone_number=f"010-0000-000{i}",
            delivery_fee=fee,
        )
        for i, fee in enumerate((3000, 2500), start=1)
    ]
    items = [
        Item(store=stores[0], name="waffle", price=10000, stock=10),
        Item(store=stores[1], name="chocolate", price=15000, stock=5),
        Item(store=stores[0], name="juice", price=5000, stock=7),
    ]
    db_session.add_all(items)
    db_session.commit()
    return {"items": [item.id for item in items], "stores": [s.id for s in stores]}


def order_body(catalog):
    return {"items": [
        {"item_id": catalog["items"][0], "quantity": 2},
        {"item_id": catalog["items"][1], "quantity": 1},
    ]}


def assert_error(response, status, code, message):
    assert response.status_code == status, response.text
    assert response.json() == {"error_code": code, "error_msg": message}


def table_count(session, model):
    return session.scalar(select(func.count()).select_from(model))


@pytest.fixture
def placed_order(client, headers, catalog):
    response = client.post("/api/orders", headers=headers, json=order_body(catalog))
    assert response.status_code == 201, response.text
    return response.json()


def test_create_order_multiple_stores(client, headers, catalog, db_session, user):
    response = client.post("/api/orders", headers=headers, json=order_body(catalog))
    assert response.status_code == 201, response.text
    data = response.json()
    assert isinstance(data["order_id"], str)
    assert data["status"] == "ORDERED"
    assert data["total_price"] == 40500
    details = {group["store_id"]: group for group in data["details"]}
    assert len(details) == 2
    first = details[catalog["stores"][0]]
    assert first["store_name"] == "store1"
    assert first["delivery_fee"] == 3000
    assert first["store_total_price"] == 23000
    assert first["items"] == [{
        "item_id": catalog["items"][0], "item_name": "waffle", "price": 10000,
        "quantity": 2, "subtotal": 20000,
    }]
    assert details[catalog["stores"][1]]["store_total_price"] == 17500
    db_session.expire_all()
    assert db_session.get(Item, catalog["items"][0]).stock == 8
    assert db_session.get(Item, catalog["items"][1]).stock == 4
    assert db_session.get(Order, data["order_id"]).user_id == user.id
    assert table_count(db_session, Order) == 1
    assert table_count(db_session, OrderStore) == 2
    assert table_count(db_session, OrderItem) == 2


def test_shipping_charged_once_per_store(client, headers, catalog):
    response = client.post("/api/orders", headers=headers, json={"items": [
        {"item_id": catalog["items"][0], "quantity": 2},
        {"item_id": catalog["items"][2], "quantity": 1},
    ]})
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["total_price"] == 28000
    assert len(data["details"]) == 1
    assert len(data["details"][0]["items"]) == 2


@pytest.mark.parametrize("price, fee, quantity, expected", [
    (0, 0, 1, 0),
    (10000, 3000, 10, 103000),
    (1500000000, 3000, 2, 3000003000),
])
def test_price_and_stock_boundaries(client, headers, catalog, db_session,
                                    price, fee, quantity, expected):
    item = db_session.get(Item, catalog["items"][0])
    item.price = price
    item.store.delivery_fee = fee
    db_session.commit()
    response = client.post("/api/orders", headers=headers, json={"items": [
        {"item_id": item.id, "quantity": quantity},
    ]})
    assert response.status_code == 201, response.text
    assert response.json()["total_price"] == expected
    db_session.refresh(item)
    assert item.stock == 10 - quantity


@pytest.mark.parametrize("payload, status, code, message", [
    ({}, 400, "ERR_002", "MISSING REQUIRED FIELDS"),
    ({"items": []}, 422, "ERR_018", "EMPTY ITEM LIST"),
    ({"items": None}, 400, "ERR_003", "INVALID FIELD FORMAT"),
    ({"items": {}}, 400, "ERR_003", "INVALID FIELD FORMAT"),
    ({"items": "bad"}, 400, "ERR_003", "INVALID FIELD FORMAT"),
    ({"items": [None]}, 400, "ERR_003", "INVALID FIELD FORMAT"),
    ({"items": [{}]}, 400, "ERR_002", "MISSING REQUIRED FIELDS"),
    ({"items": [{"item_id": "id"}]}, 400, "ERR_002", "MISSING REQUIRED FIELDS"),
    ({"items": [{"quantity": 1}]}, 400, "ERR_002", "MISSING REQUIRED FIELDS"),
])
def test_invalid_order_body(client, headers, db_session, payload, status, code, message):
    response = client.post("/api/orders", headers=headers, json=payload)
    assert_error(response, status, code, message)
    assert table_count(db_session, Order) == 0


def test_missing_order_body(client, headers):
    assert_error(client.post("/api/orders", headers=headers),
                 400, "ERR_002", "MISSING REQUIRED FIELDS")


@pytest.mark.parametrize("quantity", [0, -1, 1.5, "2", True, None])
def test_invalid_quantity(client, headers, catalog, quantity):
    response = client.post("/api/orders", headers=headers, json={"items": [
        {"item_id": catalog["items"][0], "quantity": quantity},
    ]})
    assert_error(response, 400, "ERR_003", "INVALID FIELD FORMAT")


@pytest.mark.parametrize("item_id", ["", "  ", None, 123])
def test_invalid_item_id(client, headers, item_id):
    response = client.post("/api/orders", headers=headers, json={"items": [
        {"item_id": item_id, "quantity": 1},
    ]})
    assert_error(response, 400, "ERR_003", "INVALID FIELD FORMAT")


def test_duplicate_items_are_rejected(client, headers, catalog, db_session):
    entry = {"item_id": catalog["items"][0], "quantity": 1}
    response = client.post("/api/orders", headers=headers, json={"items": [entry, entry]})
    assert_error(response, 400, "ERR_003", "INVALID FIELD FORMAT")
    assert table_count(db_session, Order) == 0
    assert db_session.get(Item, entry["item_id"]).stock == 10


@pytest.mark.parametrize("failure", ["missing", "stock"])
def test_invalid_item_does_not_partially_save(client, headers, catalog, db_session, failure):
    payload = order_body(catalog)
    if failure == "missing":
        payload["items"][1]["item_id"] = "00000000-0000-0000-0000-000000000000"
        expected = (404, "ERR_013", "ITEM NOT FOUND")
    else:
        payload["items"][1]["quantity"] = 6
        expected = (409, "ERR_017", "NOT ENOUGH STOCK")
    response = client.post("/api/orders", headers=headers, json=payload)
    assert_error(response, *expected)
    db_session.expire_all()
    assert db_session.get(Item, catalog["items"][0]).stock == 10
    assert db_session.get(Item, catalog["items"][1]).stock == 5
    assert all(table_count(db_session, model) == 0 for model in (Order, OrderStore, OrderItem))


def test_failure_after_flush_rolls_back_everything(client, headers, catalog,
                                                 db_session, monkeypatch):
    """DB 반영 직후 실패해도 주문과 재고가 함께 되돌아가는지 확인합니다."""
    original_save = OrderRepository.save_order

    def fail_after_flush(repository, order):
        original_save(repository, order)
        raise WapangException(409, "ERR_017", "NOT ENOUGH STOCK")

    monkeypatch.setattr(OrderRepository, "save_order", fail_after_flush)
    response = client.post("/api/orders", headers=headers, json=order_body(catalog))
    assert_error(response, 409, "ERR_017", "NOT ENOUGH STOCK")
    db_session.expire_all()
    assert all(table_count(db_session, model) == 0 for model in (Order, OrderStore, OrderItem))
    assert db_session.get(Item, catalog["items"][0]).stock == 10
    assert db_session.get(Item, catalog["items"][1]).stock == 5


@pytest.mark.parametrize("method,path,body", [
    ("POST", "/api/orders", {"items": [{"item_id": "test", "quantity": 1}]}),
    ("GET", "/api/orders/test", None),
    ("PATCH", "/api/orders/test", {"status": "COMPLETE"}),
])
@pytest.mark.parametrize("authorization,status,code,message", [
    (None, 401, "ERR_005", "UNAUTHENTICATED"),
    ("Bearer", 400, "ERR_006", "BAD AUTHORIZATION HEADER"),
    ("Bearer invalid-token", 401, "ERR_007", "INVALID TOKEN"),
])
def test_auth_errors(client, method, path, body, authorization, status, code, message):
    request_headers = {} if authorization is None else {"Authorization": authorization}
    response = client.request(method, path, headers=request_headers, json=body)
    assert_error(response, status, code, message)


def test_get_own_order(client, headers, placed_order):
    response = client.get(f"/api/orders/{placed_order['order_id']}", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == placed_order


@pytest.mark.parametrize("method", ["GET", "PATCH"])
def test_missing_order(client, headers, method):
    response = client.request(method, "/api/orders/00000000-0000-0000-0000-000000000000",
                              headers=headers, json={"status": "COMPLETE"} if method == "PATCH" else None)
    assert_error(response, 404, "ERR_019", "ORDER NOT FOUND")


@pytest.mark.parametrize("method", ["GET", "PATCH"])
def test_other_user_cannot_access_order(client, placed_order, method, db_session):
    account = {"email": "other@example.com", "password": "password123"}
    assert client.post("/api/users", json=account).status_code == 201
    login = client.post("/api/auth/tokens", json=account)
    assert login.status_code == 200, login.text
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    response = client.request(method, f"/api/orders/{placed_order['order_id']}",
                              headers=other_headers,
                              json={"status": "CANCELED"} if method == "PATCH" else None)
    assert_error(response, 403, "ERR_020", "NOT YOUR ORDER")
    db_session.expire_all()
    assert db_session.get(Order, placed_order["order_id"]).status.value == "ORDERED"


@pytest.mark.parametrize("new_status", ["CANCELED", "COMPLETE"])
def test_update_status(client, headers, placed_order, db_session, new_status):
    path = f"/api/orders/{placed_order['order_id']}"
    response = client.patch(path, headers=headers, json={"status": new_status})
    assert response.status_code == 204, response.text
    assert response.content == b""
    db_session.expire_all()
    assert db_session.get(Order, placed_order["order_id"]).status.value == new_status
    assert client.get(path, headers=headers).json()["status"] == new_status


@pytest.mark.parametrize("first", ["CANCELED", "COMPLETE"])
@pytest.mark.parametrize("second", ["CANCELED", "COMPLETE"])
def test_terminal_status_cannot_change(client, headers, placed_order, first, second):
    path = f"/api/orders/{placed_order['order_id']}"
    assert client.patch(path, headers=headers, json={"status": first}).status_code == 204
    response = client.patch(path, headers=headers, json={"status": second})
    assert_error(response, 409, "ERR_021", "INVALID ORDER STATUS")
    assert client.get(path, headers=headers).json()["status"] == first


@pytest.mark.parametrize("payload,code,message", [
    ({}, "ERR_002", "MISSING REQUIRED FIELDS"),
    ({"status": "ORDERED"}, "ERR_003", "INVALID FIELD FORMAT"),
    ({"status": "SHIPPED"}, "ERR_003", "INVALID FIELD FORMAT"),
    ({"status": "complete"}, "ERR_003", "INVALID FIELD FORMAT"),
    ({"status": None}, "ERR_003", "INVALID FIELD FORMAT"),
    ({"status": 1}, "ERR_003", "INVALID FIELD FORMAT"),
])
def test_invalid_status_body(client, headers, placed_order, payload, code, message):
    path = f"/api/orders/{placed_order['order_id']}"
    response = client.patch(path, headers=headers, json=payload)
    assert_error(response, 400, code, message)
    assert client.get(path, headers=headers).json()["status"] == "ORDERED"


def test_missing_status_body(client, headers, placed_order):
    response = client.patch(f"/api/orders/{placed_order['order_id']}", headers=headers)
    assert_error(response, 400, "ERR_002", "MISSING REQUIRED FIELDS")


def test_order_keeps_original_names_and_prices(client, headers, placed_order, catalog, db_session):
    item = db_session.get(Item, catalog["items"][0])
    item.name, item.price = "new item", 1
    item.store.name, item.store.delivery_fee = "new store", 0
    db_session.commit()
    response = client.get(f"/api/orders/{placed_order['order_id']}", headers=headers)
    assert response.status_code == 200
    assert response.json() == placed_order


def test_deleted_item_keeps_order_history(client, headers, placed_order, catalog, db_session):
    # SQLite도 MySQL처럼 FK 삭제 규칙을 실행하도록 이 테스트에서 활성화합니다.
    db_session.commit()
    db_session.connection().exec_driver_sql("PRAGMA foreign_keys=ON")
    assert db_session.connection().exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
    deleted_id = catalog["items"][0]
    db_session.execute(delete(Item).where(Item.id == deleted_id))
    db_session.commit()
    db_session.expire_all()
    response = client.get(f"/api/orders/{placed_order['order_id']}", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total_price"] == 40500
    first = next(group for group in data["details"] if group["store_id"] == catalog["stores"][0])
    assert first["items"] == [{
        "item_id": None, "item_name": "waffle", "price": 10000,
        "quantity": 2, "subtotal": 20000,
    }]
