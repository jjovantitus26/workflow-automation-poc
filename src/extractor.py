"""
Extracts structured fields (name, state, income, loan amount, purpose,
debt, employment) from free-text loan-application documents.

Two interchangeable backends:
  - ClaudeExtractor: calls the Claude API with a structured-JSON prompt.
    Used automatically when ANTHROPIC_API_KEY is set in the environment.
  - RuleBasedExtractor: regex/heuristic fallback that requires no API key,
    so the pipeline is fully runnable and demoable offline.

This mirrors a real "AI Solutions Analyst" decision: prefer the AI-based
extractor when available, but keep a deterministic fallback so the
workflow is never blocked on external dependencies.
"""
import os
import re
import json


class RuleBasedExtractor:
    """Deterministic fallback extractor. No external calls."""

    STATE_RE = re.compile(r"\b(IL|WI|FL)\b")
    INCOME_RE = re.compile(
        r"(?:Annual Income|Income \(annual\)|I make about|make)\D{0,15}\$?([\d,]{4,})"
    )
    LOAN_RE = re.compile(
        r"(?:Requested Loan Amount|Loan requested|borrow)\D{0,15}\$?([\d,]{3,})"
    )
    DEBT_RE = re.compile(
        r"(?:Existing Monthly Debt Payments|Monthly debt|debt payments? are around)"
        r"\D{0,15}\$?([\d,]{1,6})"
    )
    NAME_RE = re.compile(r"(?:Applicant Name|Full Name|name is)\s*[:|]?\s*([A-Za-z]+ [A-Za-z]+)")
    EMPLOYMENT_RE = re.compile(
        r"Employment(?: Status)?\s*[:|]?\s*([A-Za-z\-]+(?: [A-Za-z\-]+)?)|"
        r"(?:currently|I am currently) ([a-z\-]+(?: [a-z\-]+)?)"
    )
    PURPOSE_RE = re.compile(
        r"(?:Purpose|purpose)\s*[:|]?\s*(?:-- purpose: )?(home purchase|auto loan|"
        r"small business expansion|debt consolidation|home improvement)"
    )

    def extract(self, text: str) -> dict:
        def find(regex, group=1):
            m = regex.search(text)
            if not m:
                return None
            return m.group(group)

        income_raw = find(self.INCOME_RE)
        loan_raw = find(self.LOAN_RE)
        debt_raw = find(self.DEBT_RE)
        name = find(self.NAME_RE)
        state = find(self.STATE_RE)
        purpose = find(self.PURPOSE_RE)

        emp_match = self.EMPLOYMENT_RE.search(text)
        employment = None
        if emp_match:
            employment = emp_match.group(1) or emp_match.group(2)

        def to_int(raw):
            if raw is None:
                return None
            digits = raw.replace(",", "").strip()
            return int(digits) if digits.isdigit() else None

        return {
            "name": name,
            "state": state,
            "income": to_int(income_raw),
            "loan_amount": to_int(loan_raw),
            "debt": to_int(debt_raw),
            "purpose": purpose,
            "employment": employment,
        }


class ClaudeExtractor:
    """
    Calls the Claude API to extract the same field set as a structured
    JSON object. Requires the `anthropic` package and ANTHROPIC_API_KEY.
    """

    SYSTEM_PROMPT = (
        "Extract the following fields from the loan application text and "
        "return ONLY a JSON object with these exact keys: name, state, "
        "income (integer or null), loan_amount (integer or null), debt "
        "(integer or null), purpose, employment. No commentary, no markdown "
        "fences, JSON only."
    )

    def __init__(self, model="claude-sonnet-4-6"):
        import anthropic  # imported lazily so the fallback works without it
        self.client = anthropic.Anthropic()
        self.model = model

    def extract(self, text: str) -> dict:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text}],
        )
        raw = "".join(
            block.text for block in resp.content if getattr(block, "type", "") == "text"
        )
        return json.loads(raw)


def get_extractor():
    """Returns ClaudeExtractor if an API key is configured, else the
    deterministic fallback. This is the single seam the rest of the
    pipeline depends on."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return ClaudeExtractor()
        except Exception:
            pass
    return RuleBasedExtractor()
