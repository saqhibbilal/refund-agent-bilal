from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class RefundStatus(str, Enum):
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"


class OrderStatus(str, Enum):
    DELIVERED = "delivered"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class RequiredAction(str, Enum):
    APPROVE = "approve"
    DENY = "deny"
    ESCALATE = "escalate"


class CustomerTier(str, Enum):
    STANDARD = "standard"
    VIP = "vip"


class Customer(BaseModel):
    id: str
    name: str
    email: str
    tier: CustomerTier = CustomerTier.STANDARD
    notes: str | None = None


class OrderItem(BaseModel):
    sku: str
    name: str
    category: str
    price_cents: int = Field(ge=0)
    final_sale: bool = False
    serial_number: str | None = None
    warranty_activated: bool = False


class Order(BaseModel):
    order_id: str
    customer_id: str
    items: list[OrderItem]
    total_cents: int = Field(ge=0)
    status: OrderStatus
    purchase_date: date
    delivered_at: date | None = None
    refund_status: RefundStatus = RefundStatus.NONE


class RefundRequest(BaseModel):
    """Inputs for deterministic eligibility evaluation."""

    order_id: str
    customer_email: str | None = None
    customer_id: str | None = None
    serial_number: str | None = None
    requested_amount_cents: int | None = None
    item_skus: list[str] | None = None
    reason: str | None = None
    is_doa_claim: bool = False
    laptop_opened: bool = False
    as_of_date: date


class EligibilityResult(BaseModel):
    eligible: bool
    max_refund_cents: int = Field(ge=0)
    required_action: RequiredAction
    rule_ids: list[str]
    reason: str
    restocking_fee_cents: int = Field(default=0, ge=0)
    eligible_item_skus: list[str] = Field(default_factory=list)
    ineligible_item_skus: list[str] = Field(default_factory=list)


class DomainError(Exception):
    """Base class for domain-layer errors."""


class CustomerNotFoundError(DomainError):
    def __init__(self, identifier: str) -> None:
        super().__init__(f"Customer not found: {identifier}")
        self.identifier = identifier


class OrderNotFoundError(DomainError):
    def __init__(self, order_id: str) -> None:
        super().__init__(f"Order not found: {order_id}")
        self.order_id = order_id


class PolicyRuleNotFoundError(DomainError):
    def __init__(self, rule_id: str) -> None:
        super().__init__(f"Policy rule not found: {rule_id}")
        self.rule_id = rule_id
