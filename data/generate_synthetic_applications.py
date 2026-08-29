"""
Generates synthetic, unstructured loan-application text documents so the
pipeline can be demoed end-to-end without any real customer data.

Each document is deliberately written in free-text / semi-structured form
(the way a scanned intake form or emailed application might read) so the
extraction step has real work to do, not just a CSV to parse.
"""
import random
import os

random.seed(42)

FIRST_NAMES = ["Maria", "James", "Wei", "Fatima", "Liam", "Aisha", "Noah",
               "Priya", "Carlos", "Emma", "Yusuf", "Grace", "Daniel", "Sofia"]
LAST_NAMES = ["Garcia", "Smith", "Chen", "Khan", "Murphy", "Ali", "Johnson",
              "Patel", "Rodriguez", "Novak", "Brown", "Kim", "Lopez", "Nguyen"]
STATES = ["IL", "WI", "FL"]
LOAN_PURPOSES = ["home purchase", "auto loan", "small business expansion",
                 "debt consolidation", "home improvement"]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "applications")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TEMPLATES = [
    (
        "Loan Application Intake Form\n"
        "Applicant Name: {name}\n"
        "State: {state}\n"
        "Annual Income: ${income:,}\n"
        "Requested Loan Amount: ${loan_amount:,}\n"
        "Purpose: {purpose}\n"
        "Existing Monthly Debt Payments: ${debt:,}\n"
        "Employment Status: {employment}\n"
        "Notes: {notes}\n"
    ),
    (
        "Hi, I'd like to apply for a loan. My name is {name}, I live in {state}. "
        "I make about ${income:,} a year and I'm looking to borrow ${loan_amount:,} "
        "for {purpose}. My monthly debt payments are around ${debt:,}. "
        "I am currently {employment}. {notes}\n"
    ),
    (
        "APPLICATION\n"
        "Full Name: {name} | State: {state}\n"
        "Income (annual): {income:,}\n"
        "Loan requested: {loan_amount:,} -- purpose: {purpose}\n"
        "Monthly debt obligations: {debt:,}\n"
        "Employment: {employment}\n"
        "{notes}\n"
    ),
]

NOTE_OPTIONS = [
    "No additional notes.",
    "Applicant mentioned a recent job change.",
    "Co-signer may be available if needed.",
    "Applicant is a first-time borrower.",
    "",
]


def make_application(i):
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    state = random.choice(STATES)
    income = random.choice(range(28000, 165000, 1000))
    loan_amount = random.choice(range(3000, 400000, 500))
    debt = random.choice(range(0, 4000, 50))
    purpose = random.choice(LOAN_PURPOSES)
    employment = random.choice(["employed full-time", "self-employed",
                                 "employed part-time", "unemployed"])
    notes = random.choice(NOTE_OPTIONS)

    # ~12% of applications are deliberately missing a field to simulate
    # incomplete real-world intake and exercise the validator's checks.
    missing_field = random.random() < 0.12
    template = random.choice(TEMPLATES)
    text = template.format(
        name=name, state=state, income=income, loan_amount=loan_amount,
        purpose=purpose, debt=debt, employment=employment, notes=notes,
    )
    if missing_field:
        # Strip the income line/phrase to simulate an incomplete submission.
        text = text.replace(f"{income:,}", "").replace(f"${income:,}", "not provided")

    ground_truth = {
        "id": i,
        "name": name,
        "state": state,
        "income": None if missing_field else income,
        "loan_amount": loan_amount,
        "purpose": purpose,
        "debt": debt,
        "employment": employment,
    }
    return text, ground_truth


def main(n=120):
    import json
    truth = []
    for i in range(1, n + 1):
        text, gt = make_application(i)
        with open(os.path.join(OUTPUT_DIR, f"application_{i:03d}.txt"), "w") as f:
            f.write(text)
        truth.append(gt)

    with open(os.path.join(os.path.dirname(__file__), "ground_truth.json"), "w") as f:
        json.dump(truth, f, indent=2)

    print(f"Generated {n} synthetic applications in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
