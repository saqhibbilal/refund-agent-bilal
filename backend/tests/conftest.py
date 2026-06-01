from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.domain.crm_repository import CRMRepository
from app.domain.models import RefundRequest
from app.domain.policy_engine import PolicyEngine
from app.infrastructure.data_loader import DataLoader, LoadedData

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="session")
def loaded_data() -> LoadedData:
    return DataLoader(DATA_DIR).load()


@pytest.fixture(scope="session")
def crm(loaded_data: LoadedData) -> CRMRepository:
    return CRMRepository(loaded_data)


@pytest.fixture(scope="session")
def policy(loaded_data: LoadedData) -> PolicyEngine:
    return PolicyEngine(loaded_data.policy_text)


@pytest.fixture
def refund_request_factory():
    def _factory(
        order_id: str,
        *,
        as_of_date: date = date(2025, 5, 30),
        item_skus: list[str] | None = None,
        requested_amount_cents: int | None = None,
        customer_email: str | None = None,
        customer_id: str | None = None,
        serial_number: str | None = None,
        is_doa_claim: bool = False,
        laptop_opened: bool = False,
    ) -> RefundRequest:
        return RefundRequest(
            order_id=order_id,
            as_of_date=as_of_date,
            customer_email=customer_email,
            customer_id=customer_id,
            serial_number=serial_number,
            item_skus=item_skus,
            requested_amount_cents=requested_amount_cents,
            is_doa_claim=is_doa_claim,
            laptop_opened=laptop_opened,
        )

    return _factory
