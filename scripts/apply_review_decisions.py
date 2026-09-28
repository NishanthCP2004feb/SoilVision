"""Apply explicit human review decisions to the derived manifest.

Decision CSV columns: path,decision,reviewer,reviewed_at.  Valid decisions are
APPROVED and QUARANTINED. The immutable raw dataset is never touched.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("decisions", type=Path, nargs="?"); parser.add_argument("--manifest", type=Path, default=Path("ml/data/manifests/cleaned_manifest.csv")); parser.add_argument("--approve-all-pending", action="store_true"); parser.add_argument("--reviewer", default=""); parser.add_argument("--reviewed-at", default=""); args = parser.parse_args()
    if not args.approve_all_pending and args.decisions is None:
        raise SystemExit("Provide a decisions CSV or use --approve-all-pending after explicit human authorization.")
    decisions = {}
    if args.decisions is not None:
        with args.decisions.open(newline="", encoding="utf-8") as stream:
            decisions = {row["path"]: row for row in csv.DictReader(stream)}
    with args.manifest.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream)); fields = list(rows[0])
    for row in rows:
        decision = decisions.get(row["path"])
        if args.approve_all_pending and row["status"] == "USABLE_PENDING_CONTEXT_REVIEW":
            decision = {"decision": "APPROVED", "reviewer": args.reviewer, "reviewed_at": args.reviewed_at}
        if decision is None: continue
        if row["status"] != "USABLE_PENDING_CONTEXT_REVIEW": raise SystemExit(f"Cannot review non-pending row: {row['path']}")
        if decision["decision"] not in {"APPROVED", "QUARANTINED"}: raise SystemExit(f"Invalid decision for {row['path']}")
        row["status"] = "USABLE" if decision["decision"] == "APPROVED" else "QUARANTINED"
        row["reason"] = "Human context-quality review"
        row["context_review"] = decision["decision"]; row["reviewer"] = decision["reviewer"]; row["reviewed_at"] = decision["reviewed_at"]
    with args.manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows)


if __name__ == "__main__": main()
