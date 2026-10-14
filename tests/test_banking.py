import json

import pytest

from banking_agent.domain import assess_loan_eligibility, calculate_emi
from banking_agent.tools import BankingState, build_tools


def test_calculates_reducing_balance_emi():
    assert calculate_emi(500_000, 36, 12) == pytest.approx(16_607.15)


def test_zero_interest_emi_is_principal_divided_by_months():
    assert calculate_emi(120_000, 12, 0) == 10_000


def test_eligibility_includes_existing_emi():
    result = assess_loan_eligibility(60_000, 5_000, 16_607.15)

    assert result["eligible"] is True
    assert result["total_monthly_emi"] == 21_607.15
    assert result["emi_to_income_ratio"] == pytest.approx(0.3601, abs=0.0001)


def test_rejects_when_total_emi_exceeds_cap():
    result = assess_loan_eligibility(40_000, 8_000, 10_000)

    assert result["eligible"] is False


def test_submission_tool_stages_until_explicit_confirmation():
    state = BankingState()
    submission_tool = next(
        tool for tool in build_tools(state) if tool.name == "submit_loan_application"
    )
    application = {
        "customer_id": "CUST-1001",
        "principal": 500_000,
        "tenure_months": 36,
        "monthly_salary": 60_000,
        "existing_monthly_emi": 5_000,
        "annual_interest_rate": 12,
    }

    staged = json.loads(submission_tool.invoke(application))
    assert staged["status"] == "awaiting_confirmation"
    assert state.submitted_applications == []

    state.confirmed_application_id = staged["application_id"]
    submitted = json.loads(
        submission_tool.invoke(
            {**application, "application_id": staged["application_id"]}
        )
    )

    assert submitted["status"] == "submitted"
    assert len(state.submitted_applications) == 1
    assert state.pending_application is None


def test_account_lookup_only_returns_synthetic_demo_account():
    account_tool = next(
        tool for tool in build_tools(BankingState()) if tool.name == "get_account_details"
    )

    account = json.loads(account_tool.invoke({"customer_id": "CUST-1001"}))
    unknown = json.loads(account_tool.invoke({"customer_id": "CUST-9999"}))

    assert account["found"] is True
    assert account["data_notice"].startswith("Synthetic")
    assert unknown["found"] is False