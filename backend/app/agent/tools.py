from __future__ import annotations

from datetime import date
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.agent.models import AgentRecommendation, TraceEvent, TraceEventType
from app.domain.crm_repository import CRMRepository
from app.domain.models import (
    CustomerNotFoundError,
    OrderNotFoundError,
    PolicyRuleNotFoundError,
    RefundRequest,
    RefundStatus,
    RequiredAction,
)
from app.domain.policy_engine import PolicyEngine


class LookupCustomerInput(BaseModel):
    email: str = Field(description="Customer email address on file with Worknoon")


class SearchCustomerByNameInput(BaseModel):
    name: str = Field(description="Customer full or partial name, e.g. Drew Walsh")


class ListCustomerOrdersInput(BaseModel):
    customer_id: str = Field(description="Worknoon customer ID, e.g. cust-009")


class GetOrderInput(BaseModel):
    order_id: str = Field(description="Worknoon order ID, e.g. VG-10001")


class CheckEligibilityInput(BaseModel):
    order_id: str
    customer_email: str | None = None
    customer_id: str | None = None
    serial_number: str | None = None
    is_doa_claim: bool = False
    laptop_opened: bool = False
    item_skus: list[str] | None = None
    requested_amount_cents: int | None = None


class PolicyExcerptInput(BaseModel):
    rule_id: str = Field(description="Policy rule ID, e.g. RULE-RET-30")


class RecordRecommendationInput(BaseModel):
    action: RequiredAction
    order_id: str
    amount_cents: int = Field(ge=0)
    reason: str
    rule_ids: list[str] = Field(default_factory=list)


class EscalateInput(BaseModel):
    order_id: str
    reason: str
    rule_ids: list[str] = Field(default_factory=list)


class ToolExecutionContext(BaseModel):
    """Mutable per-run context updated by tool execution."""

    model_config = {"arbitrary_types_allowed": True}

    trace_events: list[TraceEvent]
    latest_eligibility: Any | None = None
    latest_eligibility_order_id: str | None = None
    latest_recommendation: AgentRecommendation | None = None


class AgentToolkit:
    """Agent tools — all CRM/policy access goes through the domain layer."""

    def __init__(
        self,
        crm: CRMRepository,
        policy: PolicyEngine,
        context: ToolExecutionContext,
        as_of_date: date,
    ) -> None:
        self._crm = crm
        self._policy = policy
        self._context = context
        self._as_of_date = as_of_date

    def lookup_customer_by_email(self, email: str) -> dict[str, Any]:
        self._emit_start("lookup_customer_by_email", {"email": email})
        try:
            customer = self._crm.get_customer_by_email(email)
            result = customer.model_dump(mode="json")
            result.update(self._customer_risk_summary(customer.id))
        except CustomerNotFoundError as exc:
            result = {"found": False, "error": str(exc)}
        self._emit_end("lookup_customer_by_email", result)
        return result

    def search_customer_by_name(self, name: str) -> dict[str, Any]:
        self._emit_start("search_customer_by_name", {"name": name})
        customers = self._crm.search_customers_by_name(name)
        result = {
            "query": name,
            "count": len(customers),
            "customers": [
                {
                    **customer.model_dump(mode="json"),
                    **self._customer_risk_summary(customer.id),
                }
                for customer in customers
            ],
        }
        self._emit_end("search_customer_by_name", result)
        return result

    def list_customer_orders(self, customer_id: str) -> dict[str, Any]:
        self._emit_start("list_customer_orders", {"customer_id": customer_id})
        try:
            customer = self._crm.get_customer_by_id(customer_id)
            orders = self._crm.get_orders_for_customer(customer_id)
            result = {
                "customer": customer.model_dump(mode="json"),
                "orders": [order.model_dump(mode="json") for order in orders],
            }
        except CustomerNotFoundError as exc:
            result = {"found": False, "error": str(exc)}
        self._emit_end("list_customer_orders", result)
        return result

    def get_order_details(self, order_id: str) -> dict[str, Any]:
        self._emit_start("get_order_details", {"order_id": order_id})
        try:
            order = self._crm.get_order(order_id)
            result = order.model_dump(mode="json")
        except OrderNotFoundError as exc:
            result = {"found": False, "error": str(exc)}
        self._emit_end("get_order_details", result)
        return result

    def check_refund_eligibility(
        self,
        order_id: str,
        customer_email: str | None = None,
        customer_id: str | None = None,
        serial_number: str | None = None,
        is_doa_claim: bool = False,
        laptop_opened: bool = False,
        item_skus: list[str] | None = None,
        requested_amount_cents: int | None = None,
    ) -> dict[str, Any]:
        args = {
            "order_id": order_id,
            "customer_email": customer_email,
            "customer_id": customer_id,
            "serial_number": serial_number,
            "is_doa_claim": is_doa_claim,
            "laptop_opened": laptop_opened,
            "item_skus": item_skus,
            "requested_amount_cents": requested_amount_cents,
        }
        self._emit_start("check_refund_eligibility", args)
        order = self._crm.get_order(order_id)
        customer = self._crm.get_customer_by_id(order.customer_id)
        request = RefundRequest(
            order_id=order_id,
            customer_email=customer_email,
            customer_id=customer_id,
            serial_number=serial_number,
            as_of_date=self._as_of_date,
            is_doa_claim=is_doa_claim,
            laptop_opened=laptop_opened,
            item_skus=item_skus,
            requested_amount_cents=requested_amount_cents,
        )
        eligibility = self._policy.check_eligibility(order, request, customer=customer)
        self._context.latest_eligibility = eligibility
        self._context.latest_eligibility_order_id = order_id
        result = eligibility.model_dump(mode="json")
        self._emit_end("check_refund_eligibility", result)
        return result

    def get_policy_excerpt(self, rule_id: str) -> dict[str, Any]:
        self._emit_start("get_policy_excerpt", {"rule_id": rule_id})
        try:
            excerpt = self._policy.get_excerpt(rule_id)
            result = {"rule_id": rule_id, "excerpt": excerpt}
        except PolicyRuleNotFoundError as exc:
            result = {"rule_id": rule_id, "error": str(exc)}
        self._emit_end("get_policy_excerpt", result)
        return result

    def record_agent_recommendation(
        self,
        action: RequiredAction,
        order_id: str,
        amount_cents: int,
        reason: str,
        rule_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        args = {
            "action": action.value,
            "order_id": order_id,
            "amount_cents": amount_cents,
            "reason": reason,
            "rule_ids": rule_ids or [],
        }
        self._emit_start("record_agent_recommendation", args)
        recommendation = AgentRecommendation(
            action=action,
            order_id=order_id,
            amount_cents=amount_cents,
            reason=reason,
            rule_ids=rule_ids or [],
        )
        self._context.latest_recommendation = recommendation
        result = recommendation.model_dump(mode="json")
        self._emit_end("record_agent_recommendation", result)
        return result

    def escalate_to_human(
        self,
        order_id: str,
        reason: str,
        rule_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        args = {"order_id": order_id, "reason": reason, "rule_ids": rule_ids or []}
        self._emit_start("escalate_to_human", args)
        recommendation = AgentRecommendation(
            action=RequiredAction.ESCALATE,
            order_id=order_id,
            amount_cents=0,
            reason=reason,
            rule_ids=rule_ids or [],
        )
        self._context.latest_recommendation = recommendation
        result = recommendation.model_dump(mode="json")
        self._emit_end("escalate_to_human", result)
        return result

    def as_langchain_tools(self) -> list[StructuredTool]:
        return [
            StructuredTool.from_function(
                func=self.lookup_customer_by_email,
                name="lookup_customer_by_email",
                description="Look up a Worknoon customer by email address.",
                args_schema=LookupCustomerInput,
            ),
            StructuredTool.from_function(
                func=self.search_customer_by_name,
                name="search_customer_by_name",
                description=(
                    "Search Worknoon customers by full or partial name. Use this when "
                    "the customer gives a name like Drew Walsh instead of an email or order ID."
                ),
                args_schema=SearchCustomerByNameInput,
            ),
            StructuredTool.from_function(
                func=self.list_customer_orders,
                name="list_customer_orders",
                description=(
                    "List all orders for a verified Worknoon customer ID. Use this before "
                    "discussing orders when the user identifies a customer by name or profile."
                ),
                args_schema=ListCustomerOrdersInput,
            ),
            StructuredTool.from_function(
                func=self.get_order_details,
                name="get_order_details",
                description="Fetch full order details including line items and refund status.",
                args_schema=GetOrderInput,
            ),
            StructuredTool.from_function(
                func=self.check_refund_eligibility,
                name="check_refund_eligibility",
                description=(
                    "Deterministic policy check. Must be called before any refund decision. "
                    "Pass any customer email, customer ID, or serial number the user provided "
                    "so ownership mismatches can be escalated. Returns eligible, max_refund_cents, "
                    "required_action, and rule_ids."
                ),
                args_schema=CheckEligibilityInput,
            ),
            StructuredTool.from_function(
                func=self.get_policy_excerpt,
                name="get_policy_excerpt",
                description="Return verbatim policy text for a rule ID to cite to the customer.",
                args_schema=PolicyExcerptInput,
            ),
            StructuredTool.from_function(
                func=self.record_agent_recommendation,
                name="record_agent_recommendation",
                description="Record the final approve or deny recommendation after eligibility check.",
                args_schema=RecordRecommendationInput,
            ),
            StructuredTool.from_function(
                func=self.escalate_to_human,
                name="escalate_to_human",
                description="Escalate to a human agent when policy requires it (e.g. refunds over $500).",
                args_schema=EscalateInput,
            ),
        ]

    def _emit_start(self, tool_name: str, args: dict[str, Any]) -> None:
        self._context.trace_events.append(
            TraceEvent(
                type=TraceEventType.TOOL_START,
                payload={"tool": tool_name, "args": args},
            )
        )

    def _emit_end(self, tool_name: str, result: dict[str, Any]) -> None:
        self._context.trace_events.append(
            TraceEvent(
                type=TraceEventType.TOOL_END,
                payload={"tool": tool_name, "result": result},
            )
        )

    def _customer_risk_summary(self, customer_id: str) -> dict[str, Any]:
        orders = self._crm.get_orders_for_customer(customer_id)
        previous_refund_count = sum(
            1 for order in orders if order.refund_status != RefundStatus.NONE
        )
        customer = self._crm.get_customer_by_id(customer_id)
        notes = (customer.notes or "").lower()
        risk_score = min(
            100,
            previous_refund_count * 25
            + (20 if "dispute" in notes else 0)
            + (10 if "frequent" in notes else 0),
        )
        if risk_score >= 60:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "previous_refund_count": previous_refund_count,
            "risk_score": risk_score,
            "risk_level": risk_level,
        }
