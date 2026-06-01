from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import jsonschema
from pydantic import TypeAdapter

from app.domain.models import Customer, Order


class DataLoadError(Exception):
    """Raised when synthetic data fails validation or is missing."""


@dataclass(frozen=True)
class LoadedData:
    customers: list[Customer]
    orders: list[Order]
    policy_text: str
    customers_by_email: dict[str, Customer]
    customers_by_id: dict[str, Customer]
    orders_by_id: dict[str, Order]
    orders_by_customer_id: dict[str, list[Order]]


class DataLoader:
    def __init__(self, data_dir: Path | None = None) -> None:
        if data_dir is None:
            data_dir = Path(__file__).resolve().parents[2] / "data"
        self._data_dir = data_dir

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    def load(self) -> LoadedData:
        customers_path = self._data_dir / "customers.json"
        orders_path = self._data_dir / "orders.json"
        policy_path = self._data_dir / "refund_policy.md"
        customers_schema_path = self._data_dir / "schemas" / "customers.schema.json"
        orders_schema_path = self._data_dir / "schemas" / "orders.schema.json"

        self._ensure_files_exist(
            customers_path,
            orders_path,
            policy_path,
            customers_schema_path,
            orders_schema_path,
        )

        customers_raw = self._read_json(customers_path)
        orders_raw = self._read_json(orders_path)
        customers_schema = self._read_json(customers_schema_path)
        orders_schema = self._read_json(orders_schema_path)

        jsonschema.validate(instance=customers_raw, schema=customers_schema)
        jsonschema.validate(instance=orders_raw, schema=orders_schema)

        customer_adapter = TypeAdapter(list[Customer])
        order_adapter = TypeAdapter(list[Order])

        customers = customer_adapter.validate_python(customers_raw["customers"])
        orders = order_adapter.validate_python(orders_raw["orders"])
        policy_text = policy_path.read_text(encoding="utf-8")

        customers_by_email = {customer.email.lower(): customer for customer in customers}
        customers_by_id = {customer.id: customer for customer in customers}
        orders_by_id = {order.order_id: order for order in orders}

        orders_by_customer_id: dict[str, list[Order]] = {}
        for order in orders:
            orders_by_customer_id.setdefault(order.customer_id, []).append(order)

        return LoadedData(
            customers=customers,
            orders=orders,
            policy_text=policy_text,
            customers_by_email=customers_by_email,
            customers_by_id=customers_by_id,
            orders_by_id=orders_by_id,
            orders_by_customer_id=orders_by_customer_id,
        )

    @staticmethod
    def _ensure_files_exist(*paths: Path) -> None:
        missing = [str(path) for path in paths if not path.is_file()]
        if missing:
            raise DataLoadError(f"Missing required data file(s): {', '.join(missing)}")

    @staticmethod
    def _read_json(path: Path) -> dict:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise DataLoadError(f"Invalid JSON in {path}: {exc}") from exc
