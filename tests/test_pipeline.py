import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.extractor import RuleBasedExtractor
from src.validator import validate


def test_rule_based_extractor_finds_core_fields():
    text = (
        "Loan Application Intake Form\n"
        "Applicant Name: Jane Doe\n"
        "State: IL\n"
        "Annual Income: $85,000\n"
        "Requested Loan Amount: $20,000\n"
        "Purpose: home improvement\n"
        "Existing Monthly Debt Payments: $400\n"
        "Employment Status: employed full-time\n"
    )
    result = RuleBasedExtractor().extract(text)
    assert result["name"] == "Jane Doe"
    assert result["state"] == "IL"
    assert result["income"] == 85000
    assert result["loan_amount"] == 20000
    assert result["debt"] == 400


def test_validator_flags_missing_income():
    record = {"name": "Jane Doe", "state": "IL", "income": None,
              "loan_amount": 20000, "employment": "employed full-time", "debt": 400}
    result = validate(record)
    assert result["status"] == "needs_review"
    assert any("income" in r for r in result["reasons"])


def test_validator_auto_approves_clean_record():
    record = {"name": "Jane Doe", "state": "IL", "income": 85000,
              "loan_amount": 20000, "employment": "employed full-time", "debt": 400}
    result = validate(record)
    assert result["status"] == "auto_approved"
    assert result["reasons"] == []


def test_validator_flags_high_debt_to_income():
    record = {"name": "Jane Doe", "state": "IL", "income": 30000,
              "loan_amount": 5000, "employment": "employed full-time", "debt": 2000}
    result = validate(record)
    assert result["status"] == "needs_review"
