import pytest
from sqlalchemy import create_engine, create_mock_engine, delete, event, select, text
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import Session
from uuid6 import uuid7

from wapang.database.common import Base
from wapang.database.models import Item, Order, OrderItem, OrderStatus, OrderStore, Store, User


@pytest.fixture
def orm_session():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()


@pytest.fixture
def placed_order(orm_session):
    stores = [
        Store(
            user=User(email=f"seller{i}@example.com", hashed_password="test-hash"),
            name=f"상점{i}",
            address="서울시 관악구",
            email=f"store{i}@example.com",
            phone_number=f"010-0000-000{i}",
            delivery_fee=fee,
        )
        for i, fee in enumerate((3000, 2500), start=1)
    ]
    items = [
        Item(store=stores[0], name="와플", price=10000, stock=10),
        Item(store=stores[1], name="초콜릿", price=15000, stock=5),
    ]
    order = Order(
        user=User(email="buyer@example.com", hashed_password="test-hash"),
        total_price=40500,
        order_stores=[
            OrderStore(
                store=item.store,
                store_name=item.store.name,
                delivery_fee=item.store.delivery_fee,
                order_items=[
                    OrderItem(
                        item=item,
                        item_name=item.name,
                        price=item.price,
                        quantity=quantity,
                    )
                ],
            )
            for item, quantity in zip(items, (2, 1))
        ],
    )
    orm_session.add(order)
    orm_session.commit()
    return order, items


def test_order_groups_items_from_multiple_stores(placed_order):
    order, items = placed_order
    assert order.status == OrderStatus.ORDERED
    assert order.user.store is None
    assert len(order.order_stores) == 2
    assert {group.store_id for group in order.order_stores} == {
        item.store_id for item in items
    }
    assert sum(
        group.delivery_fee
        + sum(entry.price * entry.quantity for entry in group.order_items)
        for group in order.order_stores
    ) == order.total_price
    assert all(item.store.user.store is item.store for item in items)


@pytest.mark.parametrize("delete_mode", ["orm_loaded", "orm_unloaded", "sql"])
def test_deleting_item_preserves_order_snapshots(orm_session, placed_order, delete_mode):
    order, items = placed_order
    item = items[0]
    entry = orm_session.scalar(select(OrderItem).where(OrderItem.item_id == item.id))
    entry_id, group_id, order_id, item_id = (
        entry.id, entry.order_store_id, order.id, item.id
    )
    item.name, item.price = "변경된 상품", 1
    item.store.name, item.store.delivery_fee = "변경된 상점", 0
    orm_session.commit()

    if delete_mode == "orm_loaded":
        assert len(item.order_items) == 1
    elif delete_mode == "orm_unloaded":
        orm_session.expire(item, ["order_items"])

    if delete_mode == "sql":
        orm_session.execute(delete(Item).where(Item.id == item_id))
    else:
        orm_session.delete(item)
    orm_session.commit()
    orm_session.expire_all()

    saved_entry = orm_session.get(OrderItem, entry_id)
    saved_group = orm_session.get(OrderStore, group_id)
    assert orm_session.get(Item, item_id) is None
    assert saved_entry.item_id is None
    assert saved_entry.item is None
    assert (saved_entry.item_name, saved_entry.price, saved_entry.quantity) == (
        "와플", 10000, 2
    )
    assert (saved_group.store_name, saved_group.delivery_fee) == ("상점1", 3000)
    assert orm_session.get(Order, order_id).total_price == 40500


def test_multiple_deleted_items_keep_separate_order_lines(orm_session, placed_order):
    _, items = placed_order
    first = items[0]
    entry = orm_session.scalar(select(OrderItem).where(OrderItem.item_id == first.id))
    group_id = entry.order_store_id
    extra = Item(store=first.store, name="추가 상품", price=500, stock=1)
    orm_session.add(OrderItem(
        order_store_id=group_id,
        item=extra,
        item_name=extra.name,
        price=extra.price,
        quantity=1,
    ))
    orm_session.flush()
    orm_session.execute(delete(Item).where(Item.id.in_([first.id, extra.id])))
    orm_session.commit()

    entries = orm_session.scalars(
        select(OrderItem).where(OrderItem.order_store_id == group_id)
    ).all()
    assert len(entries) == 2
    assert all(line.item_id is None for line in entries)
    assert {line.item_name for line in entries} == {"와플", "추가 상품"}


@pytest.mark.parametrize("duplicate", ["owner", "order_store", "order_item"])
def test_duplicate_ownership_and_order_lines_are_rejected(
    orm_session, placed_order, duplicate
):
    order, items = placed_order
    item = items[0]
    entry = orm_session.scalar(select(OrderItem).where(OrderItem.item_id == item.id))
    if duplicate == "owner":
        row = Store(
            user_id=item.store.user_id,
            name="두 번째 상점",
            address="서울",
            email="another-store@example.com",
            phone_number="010-9999-9999",
            delivery_fee=0,
        )
    elif duplicate == "order_store":
        row = OrderStore(
            order_id=order.id,
            store_id=item.store_id,
            store_name=item.store.name,
            delivery_fee=0,
        )
    else:
        row = OrderItem(
            order_store_id=entry.order_store_id,
            item_id=item.id,
            item_name=item.name,
            price=item.price,
            quantity=1,
        )
    orm_session.add(row)
    with pytest.raises(IntegrityError):
        orm_session.flush()


def test_database_default_status_and_large_total(orm_session):
    user = User(email="default@example.com", hashed_password="test-hash")
    orm_session.add(user)
    orm_session.flush()
    order_id = str(uuid7())
    orm_session.execute(
        text("INSERT INTO orders (id, user_id, total_price) VALUES (:id, :user_id, :total)"),
        {"id": order_id, "user_id": user.id, "total": 5_000_000_000},
    )
    order = orm_session.get(Order, order_id)
    assert order.status == OrderStatus.ORDERED
    assert order.total_price == 5_000_000_000


def test_unknown_order_status_is_rejected(orm_session, placed_order):
    order, _ = placed_order
    order.status = "SHIPPED"
    with pytest.raises(StatementError):
        orm_session.flush()


def test_order_line_requires_an_existing_order_store(orm_session):
    orm_session.add(OrderItem(
        order_store_id=str(uuid7()), item_name="상품", price=0, quantity=1
    ))
    with pytest.raises(IntegrityError):
        orm_session.flush()


def test_models_compile_for_mysql():
    statements = []

    def collect(statement, *_args, **_kwargs):
        statements.append(str(statement.compile(dialect=engine.dialect)))

    engine = create_mock_engine("mysql+pymysql://", collect)
    Base.metadata.create_all(engine)
    ddl = "\n".join(statements)
    assert "ON DELETE SET NULL" in ddl
    assert "ENUM('CANCELED','ORDERED','COMPLETE')" in ddl
    assert "total_price BIGINT" in ddl
