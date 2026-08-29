"""
Compares extracted fields against the ground truth generated alongside the
synthetic dataset, and reports per-field accuracy. This is the honest,
computed number for the README/resume -- not an invented one.
"""
import os
import json
import glob

from src.extractor import get_extractor

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "applications")
GT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ground_truth.json")
FIELDS = ["name", "state", "income", "loan_amount", "debt", "employment"]


def normalize(value):
    if isinstance(value, str):
        return value.strip().lower()
    return value


def run():
    with open(GT_PATH) as f:
        ground_truth = {g["id"]: g for g in json.load(f)}

    extractor = get_extractor()
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*.txt")))

    field_correct = {f: 0 for f in FIELDS}
    field_total = {f: 0 for f in FIELDS}

    for path in files:
        app_id = int(os.path.basename(path).split("_")[1].split(".")[0])
        gt = ground_truth[app_id]
        with open(path) as f:
            text = f.read()
        extracted = extractor.extract(text)

        for field in FIELDS:
            gt_val = gt.get(field)
            if gt_val is None:
                continue  # skip fields deliberately missing in this sample
            field_total[field] += 1
            if normalize(extracted.get(field)) == normalize(gt_val):
                field_correct[field] += 1

    print(f"Extractor backend: {type(extractor).__name__}")
    print(f"{'Field':<15}{'Accuracy':>10}   (n)")
    overall_correct, overall_total = 0, 0
    for field in FIELDS:
        total = field_total[field]
        correct = field_correct[field]
        overall_correct += correct
        overall_total += total
        acc = 100 * correct / total if total else 0
        print(f"{field:<15}{acc:>9.1f}%   ({total})")

    overall = 100 * overall_correct / overall_total if overall_total else 0
    print(f"\nOverall field-level accuracy: {overall:.1f}% ({overall_total} field checks)")
    return overall


if __name__ == "__main__":
    run()
