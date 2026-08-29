# AI-Assisted Workflow Automation POC (Document Intake & Validation)

A small end-to-end proof of concept for a pattern common in bank operations:
unstructured document intake -> AI field extraction -> business-rule
validation -> structured, dashboard-ready output. Built to mirror the core
loop an AI Solutions Analyst runs when evaluating whether an AI/automation
solution is worth piloting for a given workflow.

## Why this exists

Manually reviewing every incoming application/document for completeness and
basic eligibility is slow and inconsistent. This POC demonstrates:
1. Extracting structured fields from free-text intake documents.
2. Applying transparent, auditable business rules to flag records that
   genuinely need a human vs. those that can proceed automatically.
3. Producing output ready to drop straight into a Power BI dashboard, plus a
   lightweight local chart for a quick sanity check.

## Architecture

```
data/applications/*.txt  --(extractor.py)-->  structured fields
                                                    |
                                              (validator.py)
                                                    |
                                    output/processed_applications.csv
                                    output/run_summary.json
                                    output/dashboard_preview.png
```

**Extraction is pluggable by design.** `get_extractor()` uses the Claude API
(`ClaudeExtractor`) when `ANTHROPIC_API_KEY` is set, and falls back to a
deterministic regex-based extractor (`RuleBasedExtractor`) otherwise. This
means the pipeline is never blocked on an external API key or network
access -- a real operational concern for a bank environment with strict
egress controls.

## Results (synthetic data, this repo)

Generated 120 synthetic loan-application documents (`data/generate_synthetic_applications.py`),
deliberately varied across 3 free-text formats and with ~12% missing a
required field, to give the extractor and validator real work to do.

Running the pipeline with the rule-based extractor (no API key needed):

```
applications_processed: 120
auto_approved:          55
needs_review:            65
auto_approval_rate:     45.8%
processing_time:        0.002s for all 120 documents
```

Field-level extraction accuracy vs. ground truth (`src/evaluate.py`):

```
name          100.0%
state         100.0%
income        100.0%
loan_amount   100.0%
debt          100.0%
employment    100.0%
```

**Honest caveat:** 100% accuracy reflects that the rule-based extractor's
regex patterns were written against this synthetic dataset's own templates
-- it is not evidence the extractor would generalize to arbitrary real-world
documents. The `ClaudeExtractor` path (same interface, swap in an API key)
is the one designed to generalize; the rule-based path exists specifically
so the demo runs deterministically and offline.

The ~46% auto-approval rate is a direct result of the debt-to-income and
loan-to-income thresholds defined in `src/validator.py` against randomly
generated synthetic financials -- it's illustrative of the pattern
(quantifying how much manual review volume a rule set removes), not a
claim about real applicant populations.

## Run it yourself

```bash
pip install -r requirements.txt
python data/generate_synthetic_applications.py   # generates 120 sample docs
python -m src.pipeline                            # runs extraction + validation
python -m src.evaluate                             # field-level accuracy vs. ground truth
python -m src.report                                # dashboard_preview.png
```

To use the Claude API extractor instead of the rule-based fallback:
```bash
export ANTHROPIC_API_KEY=your_key_here
python -m src.pipeline
```

## Tests

```bash
python -m pytest tests/
```

## What I'd build next

- Swap the flat CSV for a proper Power BI `.pbix` with drill-through by
  validation-failure reason.
- Add a confidence score per extracted field so borderline extractions
  route to review even when all fields are technically present.
- Replace the synthetic dataset with a public, anonymized dataset (e.g.
  a subset of the LendingClub loan dataset) for a more realistic accuracy
  benchmark.
