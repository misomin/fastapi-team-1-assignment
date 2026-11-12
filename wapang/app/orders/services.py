from typing import Annotated

from fastapi import Depends

from wapang.app.orders.exceptions import (
    InvalidOrderStatusException,
    ItemNotFoundException,
    NotEnoughStockException,
    NotYourOrderException,
    OrderNotFoundException,
)
from wapang.app.orders.models import Order, OrderItem, OrderStatus, OrderStore
from wapang.app.orders.repositories import OrderRepository
from wapang.app.orders.schemas import (
    OrderCreateRequest,
    OrderItemResponse,
    OrderResponse,
    OrderStatusUpdateRequest,
    OrderStoreResponse,
)


class OrderService:
    def __init__(
        self,
        order_repository: Annotated[OrderRepository, Depends()],
    ) -> None:
        self.order_repository = order_repository

    def create_order(
        self,
        user_id: str,
        request: OrderCreateRequest,
    ) -> OrderResponse:
        # 주문할 상품들을 조회한다.
        item_ids = [entry.item_id for entry in request.items]
        items = self.order_repository.get_items_for_update(item_ids)
        items_by_id = {item.id: item for item in items}

        # 모든 상품이 존재하는지 확인한다.
        for entry in request.items:
            if entry.item_id not in items_by_id:
                raise ItemNotFoundException()

        # 모든 상품의 재고를 먼저 검사한다.
        for entry in request.items:
            if items_by_id[entry.item_id].stock < entry.quantity:
                raise NotEnoughStockException()

        # 상품들이 속한 상점의 정보를 조회한다.
        store_ids = sorted({item.store_id for item in items})
        stores = self.order_repository.get_stores_by_ids(store_ids)
        stores_by_id = {store.id: store for store in stores}

        order = Order(
            user_id=user_id,
            status=OrderStatus.ORDERED,
            total_price=0,
        )
        groups: dict[str, OrderStore] = {}

        for entry in request.items:
            item = items_by_id[entry.item_id]
            store = stores_by_id[item.store_id]

            # 같은 상점의 배송비는 한 번만 더한다.
            if store.id not in groups:
                group = OrderStore(
                    store_id=store.id,
                    store_name=store.name,
                    delivery_fee=store.delivery_fee,
                )
                groups[store.id] = group
                order.order_stores.append(group)
                order.total_price += store.delivery_fee

            # 주문 당시 상품명과 가격을 기록한다.
            groups[store.id].order_items.append(
                OrderItem(
                    item_id=item.id,
                    item_name=item.name,
                    price=item.price,
                    quantity=entry.quantity,
                )
            )

            order.total_price += item.price * entry.quantity
            self.order_repository.decrease_stock(item, entry.quantity)

        self.order_repository.save_order(order)
        return self._to_response(order)

    def get_order(
        self,
        user_id: str,
        order_id: str,
    ) -> OrderResponse:
        order = self.order_repository.get_order_by_id(order_id)

        if order is None:
            raise OrderNotFoundException()

        if order.user_id != user_id:
            raise NotYourOrderException()

        return self._to_response(order)

    def update_order_status(
        self,
        user_id: str,
        order_id: str,
        request: OrderStatusUpdateRequest,
    ) -> None:
        order = self.order_repository.get_order_for_update(order_id)

        if order is None:
            raise OrderNotFoundException()

        if order.user_id != user_id:
            raise NotYourOrderException()

        if order.status != OrderStatus.ORDERED:
            raise InvalidOrderStatusException()

        order.status = OrderStatus(request.status)
        self.order_repository.save_order(order)

    @staticmethod
    def _to_response(order: Order) -> OrderResponse:
        """DB의 주문 데이터를 API 응답 형식으로 변환한다."""
        details: list[OrderStoreResponse] = []

        for group in sorted(
            order.order_stores,
            key=lambda entry: entry.store_id,
        ):
            items = [
                OrderItemResponse(
                    item_id=entry.item_id,
                    item_name=entry.item_name,
                    price=entry.price,
                    quantity=entry.quantity,
                    subtotal=entry.price * entry.quantity,
                )
                for entry in sorted(
                    group.order_items,
                    key=lambda entry: entry.id,
                )
            ]

            details.append(
                OrderStoreResponse(
                    store_id=group.store_id,
                    store_name=group.store_name,
                    delivery_fee=group.delivery_fee,
                    store_total_price=(
                        sum(item.subtotal for item in items)
                        + group.delivery_fee
                    ),
                    items=items,
                )
            )

        return OrderResponse(
            order_id=order.id,
            details=details,
            total_price=order.total_price,
            status=order.status,
        )