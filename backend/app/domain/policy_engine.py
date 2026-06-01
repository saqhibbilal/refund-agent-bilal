from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.models import (
    Customer,
    CustomerTier,
    EligibilityResult,
    Order,
    OrderItem,
    OrderStatus,
    PolicyRuleNotFoundError,
    RefundRequest,
    RefundStatus,
    RequiredAction,
)

RULE_HEADER_PATTERN = re.compile(
    r"^##\s+(RULE-[A-Z0-9-]+):\s*(.+)$",
    re.MULTILINE,
)

RETURN_WINDOW_DAYS = 30
DOA_WINDOW_DAYS = 7
ESCALATION_THRESHOLD_CENTS = 50_000
LAPTOP_RESTOCKING_RATE = 0.15
LAPTOP_SKU_PREFIX = "VG-LAP-"


@dataclass(frozen=True)
class PolicyRule:
    rule_id: str
    title: str
    body: str


class PolicyEngine:
    """Deterministic refund eligibility evaluator — no LLM involvement."""

    def __init__(self, policy_text: str) -> None:
        self._policy_text = policy_text
        self._rules = self._parse_rules(policy_text)

    @property
    def rule_ids(self) -> list[str]:
        return list(self._rules.keys())

    def get_excerpt(self, rule_id: str) -> str:
        rule = self._rules.get(rule_id)
        if rule is None:
            raise PolicyRuleNotFoundError(rule_id)
        return f"{rule.rule_id}: {rule.title}\n\n{rule.body}".strip()

    def check_eligibility(
        self,
        order: Order,
        request: RefundRequest,
        customer: Customer | None = None,
    ) -> EligibilityResult:
        if order.order_id != request.order_id:
            return self._apply_customer_care(
                self._deny(
                    rule_ids=[],
                    reason="Refund request order_id does not match the provided order.",
                ),
                customer,
            )

        if order.status == OrderStatus.CANCELLED:
            return self._apply_customer_care(
                self._deny(
                    rule_ids=["RULE-CANCELLED-ORDER"],
                    reason="Cancelled orders are not eligible under the refund policy.",
                ),
                customer,
            )

        if order.status != OrderStatus.DELIVERED or order.delivered_at is None:
            return self._apply_customer_care(
                self._deny(
                    rule_ids=["RULE-DELIVERED-ONLY"],
                    reason="Refunds require a delivered order with a recorded delivery date.",
                ),
                customer,
            )

        if order.refund_status in (RefundStatus.PARTIAL, RefundStatus.FULL):
            return self._apply_customer_care(
                self._deny(
                    rule_ids=["RULE-ONE-REFUND"],
                    reason="This order already has a refund on record.",
                ),
                customer,
            )

        ownership_issue = self._ownership_verification_issue(order, request, customer)
        if ownership_issue is not None:
            return self._apply_customer_care(
                EligibilityResult(
                    eligible=False,
                    max_refund_cents=0,
                    required_action=RequiredAction.ESCALATE,
                    rule_ids=["RULE-FRAUD-OWNERSHIP"],
                    reason=self._with_policy_sections(
                        ["RULE-FRAUD-OWNERSHIP"],
                        ownership_issue,
                    ),
                ),
                customer,
            )

        target_items = self._resolve_target_items(order, request.item_skus)
        if not target_items:
            return self._apply_customer_care(
                self._deny(
                    rule_ids=[],
                    reason="No matching line items found for this refund request.",
                ),
                customer,
            )

        days_since_delivery = (request.as_of_date - order.delivered_at).days
        doa_window_open = request.is_doa_claim and days_since_delivery <= DOA_WINDOW_DAYS

        eligible_items: list[OrderItem] = []
        ineligible_items: list[OrderItem] = []
        rule_ids: list[str] = []

        for item in target_items:
            item_rules: list[str] = []

            if item.final_sale:
                item_rules.append("RULE-FINAL-SALE")
                ineligible_items.append(item)
                rule_ids.extend(item_rules)
                continue

            if item.warranty_activated:
                item_rules.append("RULE-WARRANTY-DIGITAL")
                ineligible_items.append(item)
                rule_ids.extend(item_rules)
                continue

            if doa_window_open:
                item_rules.append("RULE-DOA-7")
                eligible_items.append(item)
                rule_ids.extend(item_rules)
                continue

            if days_since_delivery > RETURN_WINDOW_DAYS:
                item_rules.append("RULE-RET-30")
                ineligible_items.append(item)
                rule_ids.extend(item_rules)
                continue

            item_rules.append("RULE-RET-30")
            eligible_items.append(item)
            rule_ids.extend(item_rules)

        rule_ids = self._dedupe(rule_ids)

        serial_issue = self._serial_verification_issue(target_items, request.serial_number)
        if (
            serial_issue is not None
            and eligible_items
            and not self._has_hard_item_exclusion(ineligible_items)
        ):
            return self._apply_customer_care(
                EligibilityResult(
                    eligible=False,
                    max_refund_cents=0,
                    required_action=RequiredAction.ESCALATE,
                    rule_ids=["RULE-FRAUD-OWNERSHIP"],
                    reason=self._with_policy_sections(
                        ["RULE-FRAUD-OWNERSHIP"],
                        serial_issue,
                    ),
                    ineligible_item_skus=[item.sku for item in ineligible_items],
                ),
                customer,
            )

        if not eligible_items:
            primary_rule = rule_ids[0] if rule_ids else "RULE-RET-30"
            return self._apply_customer_care(
                self._deny(
                    rule_ids=rule_ids or [primary_rule],
                    reason=self._build_ineligibility_reason(ineligible_items, rule_ids),
                    ineligible_item_skus=[item.sku for item in ineligible_items],
                ),
                customer,
            )

        gross_refund_cents = sum(item.price_cents for item in eligible_items)
        restocking_fee_cents = self._calculate_restocking_fee(
            eligible_items,
            request.laptop_opened,
        )
        if restocking_fee_cents:
            rule_ids.append("RULE-RESTOCK-LAPTOP")
        if eligible_items and ineligible_items:
            rule_ids.append("RULE-PARTIAL-ITEM")
        max_refund_cents = max(gross_refund_cents - restocking_fee_cents, 0)

        if request.requested_amount_cents is not None:
            if request.requested_amount_cents > max_refund_cents:
                return self._apply_customer_care(
                    self._deny(
                        rule_ids=self._dedupe(rule_ids + ["RULE-AMOUNT-AUTHORITY"]),
                        reason=(
                            f"Requested amount ({request.requested_amount_cents} cents) exceeds "
                            f"the maximum eligible refund ({max_refund_cents} cents)."
                        ),
                        ineligible_item_skus=[item.sku for item in ineligible_items],
                    ),
                    customer,
                )

        eligible_skus = [item.sku for item in eligible_items]
        ineligible_skus = [item.sku for item in ineligible_items]

        if max_refund_cents > ESCALATION_THRESHOLD_CENTS:
            escalation_rule_ids = self._dedupe(rule_ids + ["RULE-ESC-500"])
            return self._apply_customer_care(
                EligibilityResult(
                    eligible=True,
                    max_refund_cents=max_refund_cents,
                    required_action=RequiredAction.ESCALATE,
                    rule_ids=escalation_rule_ids,
                    reason=self._with_policy_sections(
                        escalation_rule_ids,
                        (
                            f"Refund of {max_refund_cents} cents exceeds the "
                            f"${ESCALATION_THRESHOLD_CENTS // 100} automated approval "
                            "threshold and requires human review."
                        ),
                    ),
                    restocking_fee_cents=restocking_fee_cents,
                    eligible_item_skus=eligible_skus,
                    ineligible_item_skus=ineligible_skus,
                ),
                customer,
            )

        reason = self._build_approval_reason(
            max_refund_cents=max_refund_cents,
            eligible_items=eligible_items,
            ineligible_items=ineligible_items,
            restocking_fee_cents=restocking_fee_cents,
        )

        return self._apply_customer_care(
            EligibilityResult(
                eligible=True,
                max_refund_cents=max_refund_cents,
                required_action=RequiredAction.APPROVE,
                rule_ids=self._dedupe(rule_ids),
                reason=self._with_policy_sections(rule_ids, reason),
                restocking_fee_cents=restocking_fee_cents,
                eligible_item_skus=eligible_skus,
                ineligible_item_skus=ineligible_skus,
            ),
            customer,
        )

    def _resolve_target_items(
        self,
        order: Order,
        item_skus: list[str] | None,
    ) -> list[OrderItem]:
        if not item_skus:
            return list(order.items)

        sku_set = {sku.strip() for sku in item_skus}
        return [item for item in order.items if item.sku in sku_set]

    def _ownership_verification_issue(
        self,
        order: Order,
        request: RefundRequest,
        customer: Customer | None,
    ) -> str | None:
        if request.customer_id and request.customer_id != order.customer_id:
            return (
                "The provided customer ID does not match the order owner. "
                "Ownership verification is required before a refund decision."
            )

        if request.customer_email and customer is not None:
            if request.customer_email.strip().lower() != customer.email.lower():
                return (
                    "The provided customer email does not match the order owner. "
                    "Ownership verification is required before a refund decision."
                )

        return None

    @staticmethod
    def _serial_verification_issue(
        target_items: list[OrderItem],
        serial_number: str | None,
    ) -> str | None:
        if not serial_number:
            return None

        expected_serials = {
            item.serial_number.strip().lower()
            for item in target_items
            if item.serial_number
        }
        if expected_serials and serial_number.strip().lower() not in expected_serials:
            return (
                "The provided serial number does not match the selected order item. "
                "Ownership verification is required before a refund decision."
            )

        return None

    @staticmethod
    def _has_hard_item_exclusion(items: list[OrderItem]) -> bool:
        return any(item.final_sale or item.warranty_activated for item in items)

    def _calculate_restocking_fee(
        self,
        eligible_items: list[OrderItem],
        laptop_opened: bool,
    ) -> int:
        if not laptop_opened:
            return 0

        laptop_total = sum(
            item.price_cents
            for item in eligible_items
            if item.sku.startswith(LAPTOP_SKU_PREFIX)
        )
        if laptop_total == 0:
            return 0

        return int(laptop_total * LAPTOP_RESTOCKING_RATE)

    def _build_ineligibility_reason(
        self,
        ineligible_items: list[OrderItem],
        rule_ids: list[str],
    ) -> str:
        if any(item.final_sale for item in ineligible_items):
            return "Final sale and clearance items are non-refundable per Worknoon policy."
        if any(item.warranty_activated for item in ineligible_items):
            return "Activated digital warranty products are non-refundable."
        if "RULE-RET-30" in rule_ids:
            return "The return window has expired (30 days from delivery)."
        return "Requested items are not eligible for a refund."

    def _build_approval_reason(
        self,
        max_refund_cents: int,
        eligible_items: list[OrderItem],
        ineligible_items: list[OrderItem],
        restocking_fee_cents: int,
    ) -> str:
        eligible_names = ", ".join(item.name for item in eligible_items)
        base = f"Eligible refund up to {max_refund_cents} cents for: {eligible_names}."
        if restocking_fee_cents:
            base += f" A restocking fee of {restocking_fee_cents} cents was applied."
        if ineligible_items:
            blocked = ", ".join(item.name for item in ineligible_items)
            base += f" Ineligible items excluded: {blocked}."
        return base

    def _deny(
        self,
        rule_ids: list[str],
        reason: str,
        ineligible_item_skus: list[str] | None = None,
    ) -> EligibilityResult:
        normalized_rule_ids = self._dedupe(rule_ids)
        return EligibilityResult(
            eligible=False,
            max_refund_cents=0,
            required_action=RequiredAction.DENY,
            rule_ids=normalized_rule_ids,
            reason=self._with_policy_sections(normalized_rule_ids, reason),
            ineligible_item_skus=ineligible_item_skus or [],
        )

    def _apply_customer_care(
        self,
        result: EligibilityResult,
        customer: Customer | None,
    ) -> EligibilityResult:
        if customer is None or customer.tier != CustomerTier.VIP:
            return result

        if result.required_action == RequiredAction.ESCALATE:
            vip_note = (
                "VIP priority care applies: route this review ahead of standard support "
                "while keeping the same policy limits."
            )
        elif result.required_action == RequiredAction.DENY:
            vip_note = (
                "VIP priority care applies: explain the policy clearly and offer specialist review "
                "if the customer believes the order record is wrong; VIP status does not override this rule."
            )
        else:
            vip_note = "VIP priority care applies: provide clear next steps and priority handling."

        return result.model_copy(
            update={
                "rule_ids": self._dedupe([*result.rule_ids, "RULE-VIP-CARE"]),
                "reason": (
                    f"{result.reason} "
                    f"{self._policy_section_label('RULE-VIP-CARE')}: {vip_note}"
                ),
            }
        )

    def _with_policy_sections(self, rule_ids: list[str], reason: str) -> str:
        normalized_rule_ids = self._dedupe(rule_ids)
        if not normalized_rule_ids:
            return reason

        noun = "section" if len(normalized_rule_ids) == 1 else "sections"
        labels = ", ".join(
            self._policy_section_label(rule_id) for rule_id in normalized_rule_ids
        )
        return f"Policy {noun} {labels}: {reason}"

    def _policy_section_label(self, rule_id: str) -> str:
        rule = self._rules.get(rule_id)
        if rule is None:
            return rule_id
        return f"{rule.rule_id} ({rule.title})"

    @staticmethod
    def _dedupe(rule_ids: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for rule_id in rule_ids:
            if rule_id not in seen:
                seen.add(rule_id)
                ordered.append(rule_id)
        return ordered

    @staticmethod
    def _parse_rules(policy_text: str) -> dict[str, PolicyRule]:
        matches = list(RULE_HEADER_PATTERN.finditer(policy_text))
        rules: dict[str, PolicyRule] = {}

        for index, match in enumerate(matches):
            rule_id = match.group(1)
            title = match.group(2).strip()
            body_start = match.end()
            body_end = matches[index + 1].start() if index + 1 < len(matches) else len(policy_text)
            body = policy_text[body_start:body_end].strip()
            rules[rule_id] = PolicyRule(rule_id=rule_id, title=title, body=body)

        return rules
