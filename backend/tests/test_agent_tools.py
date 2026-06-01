from __future__ import annotations

from datetime import date

import pytest

from app.agent.models import TraceEventType
from app.agent.tools import AgentToolkit, ToolExecutionContext
from app.domain.models import RequiredAction


class TestAgentToolkit:
    @pytest.fixture
    def toolkit(self, crm, policy) -> AgentToolkit:
        context = ToolExecutionContext(trace_events=[])
        return AgentToolkit(
            crm=crm,
            policy=policy,
            context=context,
            as_of_date=date(2025, 5, 30),
        )

    def test_lookup_customer_found(self, toolkit):
        result = toolkit.lookup_customer_by_email("alex.rivera@example.com")
        assert result["id"] == "cust-001"
        assert "previous_refund_count" in result
        assert "risk_score" in result
        assert "risk_level" in result
        assert any(event.type == TraceEventType.TOOL_START for event in toolkit._context.trace_events)

    def test_lookup_customer_missing(self, toolkit):
        result = toolkit.lookup_customer_by_email("missing@example.com")
        assert result["found"] is False

    def test_get_order_details(self, toolkit):
        result = toolkit.get_order_details("VG-10001")
        assert result["order_id"] == "VG-10001"

    def test_check_eligibility_stores_context(self, crm, policy):
        context = ToolExecutionContext(trace_events=[])
        toolkit = AgentToolkit(
            crm=crm,
            policy=policy,
            context=context,
            as_of_date=date(2025, 5, 1),
        )
        toolkit.check_refund_eligibility("VG-10001", requested_amount_cents=12999)
        assert toolkit._context.latest_eligibility is not None
        assert toolkit._context.latest_eligibility_order_id == "VG-10001"
        assert toolkit._context.latest_eligibility.required_action == RequiredAction.APPROVE

    def test_final_sale_eligibility_deny(self, toolkit):
        toolkit.check_refund_eligibility("VG-10003")
        assert toolkit._context.latest_eligibility.required_action == RequiredAction.DENY

    def test_vip_eligibility_includes_priority_care(self, toolkit):
        result = toolkit.check_refund_eligibility("VG-10002")
        assert "RULE-VIP-CARE" in result["rule_ids"]
        assert "VIP priority care" in result["reason"]

    def test_customer_email_mismatch_escalates(self, toolkit):
        result = toolkit.check_refund_eligibility(
            "VG-10001",
            customer_email="someone.else@example.com",
        )
        assert result["required_action"] == RequiredAction.ESCALATE.value
        assert "RULE-FRAUD-OWNERSHIP" in result["rule_ids"]

    def test_get_policy_excerpt(self, toolkit):
        result = toolkit.get_policy_excerpt("RULE-FINAL-SALE")
        assert "non-refundable" in result["excerpt"].lower()

    def test_record_recommendation(self, toolkit):
        toolkit.record_agent_recommendation(
            action=RequiredAction.APPROVE,
            order_id="VG-10001",
            amount_cents=12999,
            reason="Within return window.",
            rule_ids=["RULE-RET-30"],
        )
        assert toolkit._context.latest_recommendation is not None
        assert toolkit._context.latest_recommendation.action == RequiredAction.APPROVE

    def test_escalate_to_human(self, toolkit):
        toolkit.escalate_to_human(
            order_id="VG-10002",
            reason="Over $500 threshold.",
            rule_ids=["RULE-ESC-500"],
        )
        assert toolkit._context.latest_recommendation.action == RequiredAction.ESCALATE
