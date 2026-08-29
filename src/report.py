"""
Generates a lightweight dashboard-preview chart from the pipeline's CSV
output. The CSV itself (output/processed_applications.csv) is what you'd
actually import into Power BI; this script just gives a quick visual
sanity check without needing Power BI installed.
"""
import os
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import Counter

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
CSV_PATH = os.path.join(OUTPUT_DIR, "processed_applications.csv")


def run():
    with open(CSV_PATH) as f:
        rows = list(csv.DictReader(f))

    status_counts = Counter(r["status"] for r in rows)
    purpose_counts = Counter(r["purpose"] for r in rows if r["purpose"])

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    axes[0].bar(status_counts.keys(), status_counts.values(), color=["#2E7D32", "#C62828"])
    axes[0].set_title("Applications: Auto-Approved vs. Needs Review")
    axes[0].set_ylabel("Count")

    axes[1].bar(purpose_counts.keys(), purpose_counts.values(), color="#1F3864")
    axes[1].set_title("Applications by Loan Purpose")
    axes[1].tick_params(axis="x", rotation=30)

    fig.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "dashboard_preview.png")
    fig.savefig(out_path, dpi=150)
    print(f"Saved dashboard preview to {out_path}")


if __name__ == "__main__":
    run()
