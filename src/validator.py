"""
Applies simple, transparent business rules to extracted loan-application
fields and flags applications that need manual review vs. those that can
proceed automatically. Rules are intentionally simple and fully documented
here (auditability matters more than sophistication for this kind of
governance-adjacent workflow).
"""

REQUIRED_FIELDS = ["name", "state", "income", "loan_amount", "employment"]
MAX_DEBT_TO_INCOME_RATIO = 0.45  # monthly debt / (annual income / 12)
MAX_LOAN_TO_INCOME_RATIO = 5.0   # loan amount / annual income


def validate(record: dict) -> dict:
    """Returns a dict with 'status' ('auto_approved' | 'needs_review') and
    a list of human-readable 'reasons' explaining any flags raised."""
    reasons = []

    for field in REQUIRED_FIELDS:
        if not record.get(field):
            reasons.append(f"Missing required field: {field}")

    income = record.get("income")
    loan_amount = record.get("loan_amount")
    debt = record.get("debt") or 0

    if income:
        monthly_income = income / 12
        if monthly_income > 0 and debt / monthly_income > MAX_DEBT_TO_INCOME_RATIO:
            reasons.append(
                f"Debt-to-income ratio {debt / monthly_income:.2f} exceeds "
                f"threshold {MAX_DEBT_TO_INCOME_RATIO}"
            )
        if loan_amount and income > 0 and loan_amount / income > MAX_LOAN_TO_INCOME_RATIO:
            reasons.append(
                f"Loan-to-income ratio {loan_amount / income:.2f} exceeds "
                f"threshold {MAX_LOAN_TO_INCOME_RATIO}"
            )

    if record.get("employment", "").lower().strip() in ("unemployed",):
        reasons.append("Applicant employment status is 'unemployed'")

    status = "needs_review" if reasons else "auto_approved"
    return {"status": status, "reasons": reasons}
