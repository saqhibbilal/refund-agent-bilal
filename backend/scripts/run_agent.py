"""Manual agent CLI — requires MISTRAL_API_KEY."""

from __future__ import annotations

import argparse
from datetime import date

from app.agent.execution import AgentRunner
from app.domain.crm_repository import CRMRepository
from app.domain.policy_engine import PolicyEngine
from app.infrastructure.data_loader import DataLoader
from app.infrastructure.mistral_client import create_chat_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Worknoon refund agent once.")
    parser.add_argument("message", help="Customer message")
    parser.add_argument("--as-of", dest="as_of", default=None, help="ISO date (YYYY-MM-DD)")
    args = parser.parse_args()

    data = DataLoader().load()
    crm = CRMRepository(data)
    policy = PolicyEngine(data.policy_text)
    llm = create_chat_model()
    runner = AgentRunner(crm=crm, policy=policy, llm=llm)

    as_of_date = date.fromisoformat(args.as_of) if args.as_of else None
    result = runner.run(args.message, as_of_date=as_of_date)

    print("\n--- Agent Response ---")
    print(result.response_text)
    print("\n--- Validation ---")
    print(f"passed={result.validation_passed}")
    if result.recommendation:
        print(f"action={result.recommendation.action.value} amount={result.recommendation.amount_cents}")
    print(f"trace_events={len(result.trace_events)}")


if __name__ == "__main__":
    main()
