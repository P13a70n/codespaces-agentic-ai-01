"""Deterministic loan calculations and eligibility rules."""

import math


DEFAULT_ANNUAL_INTEREST_RATE = 12.0
MAX_EMI_TO_INCOME_RATIO = 0.40


def calculate_emi(
    principal: float,
    tenure_months: int,
    annual_interest_rate: float = DEFAULT_ANNUAL_INTEREST_RATE,
) -> float:
    """Return the monthly EMI for a reducing-balance loan."""
    values = (principal, annual_interest_rate)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Loan amount and interest rate must be finite numbers.")
    if principal <= 0 or tenure_months <= 0 or annual_interest_rate < 0:
        raise ValueError("Loan amount and tenure must be positive; rate cannot be negative.")

    monthly_rate = annual_interest_rate / 100 / 12
    if monthly_rate == 0:
        return round(principal / tenure_months, 2)

    growth = (1 + monthly_rate) ** tenure_months
    return round(principal * monthly_rate * growth / (growth - 1), 2)


def assess_loan_eligibility(
    monthly_salary: float,
    existing_monthly_emi: float,
    proposed_monthly_emi: float,
    max_emi_ratio: float = MAX_EMI_TO_INCOME_RATIO,
) -> dict[str, float | bool | str]:
    """Assess affordability using the configured total EMI-to-income cap."""
    values = (monthly_salary, existing_monthly_emi, proposed_monthly_emi, max_emi_ratio)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Salary, EMIs, and eligibility ratio must be finite numbers.")
    if monthly_salary <= 0 or existing_monthly_emi < 0 or proposed_monthly_emi < 0:
        raise ValueError("Salary must be positive and EMI amounts cannot be negative.")
    if not 0 < max_emi_ratio <= 1:
        raise ValueError("Eligibility ratio must be greater than 0 and at most 1.")

    total_emi = round(existing_monthly_emi + proposed_monthly_emi, 2)
    emi_ratio = total_emi / monthly_salary
    eligible = emi_ratio <= max_emi_ratio
    return {
        "eligible": eligible,
        "monthly_salary": round(monthly_salary, 2),
        "existing_monthly_emi": round(existing_monthly_emi, 2),
        "proposed_monthly_emi": round(proposed_monthly_emi, 2),
        "total_monthly_emi": total_emi,
        "emi_to_income_ratio": round(emi_ratio, 4),
        "maximum_emi_to_income_ratio": max_emi_ratio,
        "reason": (
            "Total monthly EMIs are within the affordability limit."
            if eligible
            else "Total monthly EMIs exceed the affordability limit."
        ),
    }