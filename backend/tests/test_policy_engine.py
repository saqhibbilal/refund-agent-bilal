from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.domain.models import (
    CustomerNotFoundError,
    OrderNotFoundError,
    PolicyRuleNotFoundError,
    RequiredAction,
)
from app.infrastructure.data_loader import DataLoader, DataLoadError

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


class TestDataLoader:
    def test_loads_and_validates_data(self, loaded_data):
        assert len(loaded_data.customers) == 15
        assert len(loaded_data.orders) >= 15
        assert "RULE-RET-30" in loaded_data.policy_text

    def test_builds_email_and_order_indexes(self, loaded_data):
        assert "alex.rivera@example.com" in loaded_data.customers_by_email
        assert "VG-10001" in loaded_data.orders_by_id
        assert any(
            order.order_id == "VG-10016"
            for order in loaded_data.orders_by_customer_id["cust-001"]
        )

    def test_missing_file_raises(self, tmp_path):
        loader = DataLoader(tmp_path)
        with pytest.raises(DataLoadError, match="Missing required data file"):
            loader.load()


class TestCRMRepository:
    def test_lookup_customer_by_email(self, crm):
        customer = crm.get_customer_by_email("Jordan.Kim@example.com")
        assert customer.id == "cust-002"
        assert customer.tier.value == "vip"

    def test_customer_not_found(self, crm):
        with pytest.raises(CustomerNotFoundError):
            crm.get_customer_by_email("missing@example.com")

    def test_get_order(self, crm):
        order = crm.get_order("VG-10003")
        assert order.items[0].final_sale is True

    def test_order_not_found(self, crm):
        with pytest.raises(OrderNotFoundError):
            crm.get_order("VG-99999")

    def test_orders_for_customer(self, crm):
        orders = crm.get_orders_for_customer("cust-001")
        order_ids = {order.order_id for order in orders}
        assert {"VG-10001", "VG-10016"}.issubset(order_ids)


class TestPolicyEngine:
    def test_all_rule_ids_parsed(self, policy):
        expected = {
            "RULE-RET-30",
            "RULE-FINAL-SALE",
            "RULE-ESC-500",
            "RULE-DOA-7",
            "RULE-WARRANTY-DIGITAL",
            "RULE-ONE-REFUND",
            "RULE-RESTOCK-LAPTOP",
            "RULE-DELIVERED-ONLY",
            "RULE-CANCELLED-ORDER",
            "RULE-PARTIAL-ITEM",
            "RULE-AMOUNT-AUTHORITY",
            "RULE-VIP-CARE",
            "RULE-SUPPORTIVE-CLARIFY",
            "RULE-CUSTOMER-VERIFY",
            "RULE-FRAUD-OWNERSHIP",
            "RULE-PRIORITY",
        }
        assert expected.issubset(set(policy.rule_ids))

    def test_get_excerpt(self, policy):
        excerpt = policy.get_excerpt("RULE-FINAL-SALE")
        assert "non-refundable" in excerpt.lower()

    def test_unknown_rule_raises(self, policy):
        with pytest.raises(PolicyRuleNotFoundError):
            policy.get_excerpt("RULE-DOES-NOT-EXIST")

    def test_standard_return_approved(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10001")
        request = refund_request_factory("VG-10001", as_of_date=date(2025, 5, 1))
        result = policy.check_eligibility(order, request)

        assert result.eligible is True
        assert result.required_action == RequiredAction.APPROVE
        assert result.max_refund_cents == 12999
        assert "RULE-RET-30" in result.rule_ids
        assert "RULE-RET-30 (Standard Return Window)" in result.reason

    def test_final_sale_denied(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10003")
        request = refund_request_factory("VG-10003")
        result = policy.check_eligibility(order, request)

        assert result.eligible is False
        assert result.required_action == RequiredAction.DENY
        assert result.max_refund_cents == 0
        assert "RULE-FINAL-SALE" in result.rule_ids
        assert "RULE-FINAL-SALE (Final Sale and Clearance Items)" in result.reason

    def test_high_value_escalation(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10002")
        request = refund_request_factory("VG-10002", as_of_date=date(2025, 5, 20))
        result = policy.check_eligibility(order, request)

        assert result.eligible is True
        assert result.required_action == RequiredAction.ESCALATE
        assert result.max_refund_cents == 89900
        assert "RULE-ESC-500" in result.rule_ids
        assert "RULE-ESC-500 (High-Value Refund Escalation)" in result.reason

    def test_doa_within_seven_days(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10005")
        request = refund_request_factory(
            "VG-10005",
            as_of_date=date(2025, 5, 30),
            is_doa_claim=True,
        )
        result = policy.check_eligibility(order, request)

        assert result.eligible is True
        assert result.required_action == RequiredAction.APPROVE
        assert result.max_refund_cents == 8999
        assert "RULE-DOA-7" in result.rule_ids

    def test_expired_return_window(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10006")
        request = refund_request_factory("VG-10006", as_of_date=date(2025, 5, 30))
        result = policy.check_eligibility(order, request)

        assert result.eligible is False
        assert result.required_action == RequiredAction.DENY
        assert "RULE-RET-30" in result.rule_ids

    def test_already_refunded_denied(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10007")
        request = refund_request_factory("VG-10007")
        result = policy.check_eligibility(order, request)

        assert result.eligible is False
        assert result.required_action == RequiredAction.DENY
        assert "RULE-ONE-REFUND" in result.rule_ids

    def test_partial_refund_status_denied(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10013")
        request = refund_request_factory("VG-10013", as_of_date=date(2025, 5, 20))
        result = policy.check_eligibility(order, request)

        assert result.eligible is False
        assert "RULE-ONE-REFUND" in result.rule_ids

    def test_activated_warranty_denied(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10004")
        request = refund_request_factory("VG-10004", as_of_date=date(2025, 3, 15))
        result = policy.check_eligibility(order, request)

        assert result.eligible is False
        assert "RULE-WARRANTY-DIGITAL" in result.rule_ids

    def test_mixed_cart_partial_eligibility(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10008")
        request = refund_request_factory(
            "VG-10008",
            as_of_date=date(2025, 5, 25),
            item_skus=["VG-BUDS-PRO", "VG-GPU-OPENBOX"],
        )
        result = policy.check_eligibility(order, request)

        assert result.eligible is True
        assert result.required_action == RequiredAction.APPROVE
        assert result.max_refund_cents == 12999
        assert result.eligible_item_skus == ["VG-BUDS-PRO"]
        assert "VG-GPU-OPENBOX" in result.ineligible_item_skus
        assert "RULE-PARTIAL-ITEM" in result.rule_ids

    def test_mixed_cart_gpu_only_denied(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10008")
        request = refund_request_factory(
            "VG-10008",
            item_skus=["VG-GPU-OPENBOX"],
        )
        result = policy.check_eligibility(order, request)

        assert result.eligible is False
        assert "RULE-FINAL-SALE" in result.rule_ids

    def test_laptop_restocking_fee(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10002")
        request = refund_request_factory(
            "VG-10002",
            as_of_date=date(2025, 5, 20),
            laptop_opened=True,
            requested_amount_cents=76415,
        )
        result = policy.check_eligibility(order, request)

        assert result.eligible is True
        assert result.restocking_fee_cents == 13485
        assert result.max_refund_cents == 76415
        assert result.required_action == RequiredAction.ESCALATE
        assert "RULE-RESTOCK-LAPTOP" in result.rule_ids

    def test_vip_high_value_refund_gets_priority_care(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10002")
        customer = crm.get_customer_by_id(order.customer_id)
        request = refund_request_factory(
            "VG-10002",
            as_of_date=date(2025, 5, 20),
        )
        result = policy.check_eligibility(order, request, customer=customer)

        assert result.required_action == RequiredAction.ESCALATE
        assert "RULE-ESC-500" in result.rule_ids
        assert "RULE-VIP-CARE" in result.rule_ids
        assert "VIP priority care" in result.reason

    def test_vip_status_does_not_override_expired_window(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10006")
        customer = crm.get_customer_by_id(order.customer_id)
        request = refund_request_factory(
            "VG-10006",
            as_of_date=date(2025, 5, 30),
        )
        result = policy.check_eligibility(order, request, customer=customer)

        assert result.eligible is False
        assert result.required_action == RequiredAction.DENY
        assert "RULE-RET-30" in result.rule_ids
        assert "RULE-VIP-CARE" in result.rule_ids
        assert "does not override" in result.reason

    def test_sub_500_item_on_high_value_order_approved(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10012")
        request = refund_request_factory(
            "VG-10012",
            as_of_date=date(2025, 5, 25),
            item_skus=["VG-DOCK-USBC"],
        )
        result = policy.check_eligibility(order, request)

        assert result.eligible is True
        assert result.required_action == RequiredAction.APPROVE
        assert result.max_refund_cents == 8999

    def test_not_delivered_denied(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10010")
        request = refund_request_factory("VG-10010")
        result = policy.check_eligibility(order, request)

        assert result.eligible is False
        assert result.max_refund_cents == 0
        assert "RULE-DELIVERED-ONLY" in result.rule_ids

    def test_cancelled_order_denied(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10014")
        request = refund_request_factory("VG-10014")
        result = policy.check_eligibility(order, request)

        assert result.eligible is False
        assert "RULE-CANCELLED-ORDER" in result.rule_ids

    def test_requested_amount_exceeds_max_denied(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10001")
        request = refund_request_factory(
            "VG-10001",
            as_of_date=date(2025, 5, 1),
            requested_amount_cents=20000,
        )
        result = policy.check_eligibility(order, request)

        assert result.eligible is False
        assert result.required_action == RequiredAction.DENY
        assert "RULE-AMOUNT-AUTHORITY" in result.rule_ids

    def test_final_sale_not_overridden_by_doa(self, crm, policy, refund_request_factory):
        order = crm.get_order("VG-10003")
        request = refund_request_factory(
            "VG-10003",
            is_doa_claim=True,
        )
        result = policy.check_eligibility(order, request)

        assert result.eligible is False
        assert "RULE-FINAL-SALE" in result.rule_ids

    def test_customer_email_mismatch_escalates_for_ownership_review(
        self,
        crm,
        policy,
        refund_request_factory,
    ):
        order = crm.get_order("VG-10001")
        customer = crm.get_customer_by_id(order.customer_id)
        request = refund_request_factory(
            "VG-10001",
            as_of_date=date(2025, 5, 1),
            customer_email="someone.else@example.com",
        )
        result = policy.check_eligibility(order, request, customer=customer)

        assert result.eligible is False
        assert result.required_action == RequiredAction.ESCALATE
        assert "RULE-FRAUD-OWNERSHIP" in result.rule_ids
        assert "email does not match" in result.reason

    def test_customer_id_mismatch_escalates_for_ownership_review(
        self,
        crm,
        policy,
        refund_request_factory,
    ):
        order = crm.get_order("VG-10001")
        customer = crm.get_customer_by_id(order.customer_id)
        request = refund_request_factory(
            "VG-10001",
            as_of_date=date(2025, 5, 1),
            customer_id="cust-999",
        )
        result = policy.check_eligibility(order, request, customer=customer)

        assert result.required_action == RequiredAction.ESCALATE
        assert "RULE-FRAUD-OWNERSHIP" in result.rule_ids

    def test_serial_number_mismatch_escalates_when_no_hard_denial(
        self,
        crm,
        policy,
        refund_request_factory,
    ):
        order = crm.get_order("VG-10001")
        request = refund_request_factory(
            "VG-10001",
            as_of_date=date(2025, 5, 1),
            serial_number="SN-WRONG-123",
        )
        result = policy.check_eligibility(order, request)

        assert result.required_action == RequiredAction.ESCALATE
        assert "RULE-FRAUD-OWNERSHIP" in result.rule_ids
        assert "serial number" in result.reason

    def test_hard_denial_priority_wins_over_serial_mismatch(
        self,
        crm,
        policy,
        refund_request_factory,
    ):
        order = crm.get_order("VG-10003")
        request = refund_request_factory(
            "VG-10003",
            serial_number="SN-WRONG-123",
        )
        result = policy.check_eligibility(order, request)

        assert result.required_action == RequiredAction.DENY
        assert "RULE-FINAL-SALE" in result.rule_ids
        assert "RULE-FRAUD-OWNERSHIP" not in result.rule_ids
