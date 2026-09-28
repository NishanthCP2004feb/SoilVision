"""Create deterministic grouped splits from human-approved usable records."""
from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


SPLITS = ("train", "validation", "test")
TARGETS = {"train": 0.70, "validation": 0.15, "test": 0.15}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("ml/data/manifests/cleaned_manifest.csv"))
    parser.add_argument("--output", type=Path, default=Path("ml/data/manifests"))
    parser.add_argument("--seed", type=int, default=20260810)
    return parser.parse_args()


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "label", "group_id", "split"])
        writer.writeheader(); writer.writerows(rows)


def grouped_split(rows: list[dict[str, str]], seed: int) -> dict[str, list[dict[str, str]]]:
    """Greedily allocate whole related-image groups against per-class target counts."""
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row["group_id"]].append(row)
    label_totals = Counter(row["label"] for row in rows)
    current = {split: Counter() for split in SPLITS}
    current_total = {split: 0 for split in SPLITS}
    assignments: dict[str, str] = {}
    randomized = list(groups.items())
    random.Random(seed).shuffle(randomized)
    for group_id, members in sorted(randomized, key=lambda item: len(item[1]), reverse=True):
        member_counts = Counter(member["label"] for member in members)
        def cost(split: str) -> float:
            # Score the *change* in squared target error. This makes the largest
            # remaining target attractive instead of prematurely filling a 15% split.
            class_delta = sum(
                (((current[split][label] + amount) - label_totals[label] * TARGETS[split]) ** 2 - (current[split][label] - label_totals[label] * TARGETS[split]) ** 2) / max(1, label_totals[label])
                for label, amount in member_counts.items()
            )
            total_target = len(rows) * TARGETS[split]
            total_delta = ((current_total[split] + len(members) - total_target) ** 2 - (current_total[split] - total_target) ** 2) / len(rows)
            return class_delta + total_delta
        chosen = min(SPLITS, key=cost)
        assignments[group_id] = chosen
        current[chosen].update(member_counts)
        current_total[chosen] += len(members)
    result = {split: [] for split in SPLITS}
    for row in rows:
        result[assignments[row["group_id"]]].append({"path": row["path"], "label": row["label"], "group_id": row["group_id"], "split": assignments[row["group_id"]]})
    return result


def main() -> None:
    args = parse_args()
    with args.manifest.open(newline="", encoding="utf-8") as stream:
        approved = [row for row in csv.DictReader(stream) if row["status"] == "USABLE" and row["context_review"] == "APPROVED"]
    if not approved:
        raise SystemExit("No human-approved USABLE images found. Review the cleaning manifest before creating a training split.")
    labels = Counter(row["label"] for row in approved)
    if any(count < 3 for count in labels.values()):
        raise SystemExit("Every label needs at least three approved images for train/validation/test splitting.")
    result = grouped_split(approved, args.seed)
    for split, rows in result.items():
        write_rows(args.output / f"{split}.csv", rows)
    report = {"seed": args.seed, "dataset_version": "soil_dataset_v1_cleaned", "counts": {split: len(rows) for split, rows in result.items()}, "class_counts": {split: dict(Counter(row["label"] for row in rows)) for split, rows in result.items()}, "policy": "Every group_id is allocated to exactly one split."}
    (args.output / "split_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
