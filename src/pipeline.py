"""
Orchestrates the end-to-end workflow:
  document intake -> AI/rule-based field extraction -> business-rule
  validation -> structured output (CSV, ready for a Power BI import)
  + a plain-text summary report.

Run with: python -m src.pipeline
"""
import os
import csv
import glob
import json
import time

from src.extractor import get_extractor
from src.validator import validate

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "applications")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")


def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    extractor = get_extractor()
    backend = type(extractor).__name__

    files = sorted(glob.glob(os.path.join(DATA_DIR, "*.txt")))
    rows = []
    start = time.time()

    for path in files:
        with open(path) as f:
            text = f.read()
        extracted = extractor.extract(text)
        result = validate(extracted)
        row = {
            "file": os.path.basename(path),
            **extracted,
            "status": result["status"],
            "reasons": "; ".join(result["reasons"]),
        }
        rows.append(row)

    elapsed = time.time() - start

    # Structured, Power-BI-ready CSV output.
    csv_path = os.path.join(OUTPUT_DIR, "processed_applications.csv")
    fieldnames = ["file", "name", "state", "income", "loan_amount", "debt",
                  "purpose", "employment", "status", "reasons"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    n = len(rows)
    n_review = sum(1 for r in rows if r["status"] == "needs_review")
    n_auto = n - n_review

    summary = {
        "extractor_backend": backend,
        "applications_processed": n,
        "auto_approved": n_auto,
        "needs_review": n_review,
        "auto_approval_rate_pct": round(100 * n_auto / n, 1) if n else 0,
        "processing_time_seconds": round(elapsed, 3),
    }

    with open(os.path.join(OUTPUT_DIR, "run_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    run()
