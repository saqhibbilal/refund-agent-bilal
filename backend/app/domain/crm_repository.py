from __future__ import annotations

from app.domain.models import Customer, CustomerNotFoundError, Order, OrderNotFoundError
from app.infrastructure.data_loader import LoadedData


class CRMRepository:
    """Read-only access to synthetic CRM data with O(1) lookups."""

    def __init__(self, data: LoadedData) -> None:
        self._data = data

    def get_customer_by_email(self, email: str) -> Customer:
        customer = self._data.customers_by_email.get(email.strip().lower())
        if customer is None:
            raise CustomerNotFoundError(email)
        return customer

    def get_customer_by_id(self, customer_id: str) -> Customer:
        customer = self._data.customers_by_id.get(customer_id)
        if customer is None:
            raise CustomerNotFoundError(customer_id)
        return customer

    def search_customers_by_name(self, name: str) -> list[Customer]:
        normalized = " ".join(name.strip().lower().split())
        if not normalized:
            return []

        exact_matches = [
            customer
            for customer in self._data.customers
            if customer.name.lower() == normalized
        ]
        if exact_matches:
            return exact_matches

        return [
            customer
            for customer in self._data.customers
            if normalized in customer.name.lower()
        ]

    def get_order(self, order_id: str) -> Order:
        order = self._data.orders_by_id.get(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        return order

    def get_orders_for_customer(self, customer_id: str) -> list[Order]:
        return list(self._data.orders_by_customer_id.get(customer_id, []))
