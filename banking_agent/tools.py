"""LangChain tools backed by deterministic, session-local demo data."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from langchain.tools import tool

from banking_agent.domain import (
    DEFAULT_ANNUAL_INTEREST_RATE,
    assess_loan_eligibility,
    calculate_emi as calculate_monthly_emi,
)


DEMO_CUSTOMER_ID = "CUST-1001"


@dataclass
class BankingState:
    """Per-browser-session state; never connected to a banking system."""

    pending_application: dict[str, Any] | None = None
    confirmed_application_id: str | None = None
    submitted_applications: list[dict[str, Any]] = field(default_factory=list)
    next_application_number: int = 1


def build_tools(state: BankingState) -> list[Any]:
    """Create the agent's four tools, bound to the current demo session."""

    @tool
    def calculate_emi(
        principal: float,
        tenure_months: int,
        annual_interest_rate: float = DEFAULT_ANNUAL_INTEREST_RATE,
    ) -> str:
        """Calculate monthly EMI using a reducing-balance interest rate."""
        emi = calculate_monthly_emi(principal, tenure_months, annual_interest_rate)
        return json.dumps(
            {
                "monthly_emi": emi,
                "principal": round(principal, 2),
                "tenure_months": tenure_months,
                "annual_interest_rate": annual_interest_rate,
                "currency": "INR",
            }
        )

    @tool
    def check_loan_eligibility(
        monthly_salary: float,
        existing_monthly_emi: float,
        proposed_monthly_emi: float,
    ) -> str:
        """Check affordability; total EMIs must not exceed 40% of salary."""
        return json.dumps(
            assess_loan_eligibility(
                monthly_salary, existing_monthly_emi, proposed_monthly_emi
            )
        )

    @tool
    def get_account_details(customer_id: str = DEMO_CUSTOMER_ID) -> str:
        """Retrieve the signed-in synthetic demo customer's account summary."""
        if customer_id != DEMO_CUSTOMER_ID:
            return json.dumps(
                {"found": False, "message": "No demo account matches that customer ID."}
            )
        return json.dumps(
            {
                "found": True,
                "customer_id": DEMO_CUSTOMER_ID,
                "account_number": "XXXXXX4821",
                "account_type": "Savings",
                "available_balance": 245000.00,
                "currency": "INR",
                "branch": "Bengaluru Central (demo)",
                "data_notice": "Synthetic sample data; not a real bank account.",
            }
        )

    @tool
    def submit_loan_application(
        customer_id: str,
        principal: float,
        tenure_months: int,
        monthly_salary: float,
        existing_monthly_emi: float,
        annual_interest_rate: float = DEFAULT_ANNUAL_INTEREST_RATE,
        application_id: str | None = None,
    ) -> str:
        """Stage an eligible loan application; submit only after UI confirmation."""
        if customer_id != DEMO_CUSTOMER_ID:
            return json.dumps({"status": "error", "message": "Unknown demo customer."})

        monthly_emi = calculate_monthly_emi(
            principal, tenure_months, annual_interest_rate
        )
        eligibility = assess_loan_eligibility(
            monthly_salary, existing_monthly_emi, monthly_emi
        )
        if not eligibility["eligible"]:
            return json.dumps(
                {"status": "not_eligible", "eligibility": eligibility}
            )

        application = {
            "customer_id": customer_id,
            "principal": round(principal, 2),
            "tenure_months": tenure_months,
            "monthly_salary": round(monthly_salary, 2),
            "existing_monthly_emi": round(existing_monthly_emi, 2),
            "annual_interest_rate": round(annual_interest_rate, 4),
            "monthly_emi": monthly_emi,
        }

        pending = state.pending_application
        if pending is None:
            generated_id = f"APP-{state.next_application_number:04d}"
            state.next_application_number += 1
            state.pending_application = {
                "application_id": generated_id,
                "application": application,
                "eligibility": eligibility,
            }
            return json.dumps(
                {
                    "status": "awaiting_confirmation",
                    "application_id": generated_id,
                    "application": application,
                    "eligibility": eligibility,
                    "message": "The application is prepared but has not been submitted.",
                }
            )

        if pending["application"] != application:
            return json.dumps(
                {
                    "status": "pending_application_exists",
                    "application_id": pending["application_id"],
                    "message": "Resolve the pending application before preparing another.",
                }
            )

        expected_id = pending["application_id"]
        if (
            application_id != expected_id
            or state.confirmed_application_id != expected_id
        ):
            return json.dumps(
                {
                    "status": "awaiting_confirmation",
                    "application_id": expected_id,
                    "application": application,
                    "eligibility": eligibility,
                    "message": "Explicit customer confirmation is required before submission.",
                }
            )

        receipt = {
            "status": "submitted",
            "application_id": expected_id,
            "application": application,
            "eligibility": eligibility,
        }
        state.submitted_applications.append(receipt)
        state.pending_application = None
        state.confirmed_application_id = None
        return json.dumps(receipt)

    return [
        calculate_emi,
        check_loan_eligibility,
        get_account_details,
        submit_loan_application,
    ]