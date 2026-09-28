"""Create an auditable derived cleaning manifest from inspection outputs.

This tool intentionally does not make semantic claims from unreliable heuristics.
Context quality requires a human review decision before a production training run.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspection", type=Path, default=Path("ml/reports/dataset_inspection"))
    parser.add_argument("--output", type=Path, default=Path("ml/data/manifests"))
    return parser.parse_args()


class UnionFind:
    def __init__(self, values: list[str]) -> None:
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        if self.parent[value] != value:
            self.parent[value] = self.find(self.parent[value])
        return self.parent[value]

    def union(self, left: str, right: str) -> None:
        left, right = self.find(left), self.find(right)
        if left != right:
            self.parent[right] = left


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_review_sheet(rows: list[dict[str, str]], output: Path) -> None:
    """Render quarantined candidates for explicit label/context review."""

    if not rows:
        return
    thumb = (180, 135)
    canvas = Image.new("RGB", (thumb[0] * 4, 170 * ((len(rows) + 3) // 4)), "white")
    draw = ImageDraw.Draw(canvas)
    for index, row in enumerate(rows):
        x, y = (index % 4) * thumb[0], (index // 4) * 170
        try:
            with Image.open(row["path"]) as image:
                canvas.paste(ImageOps.fit(image.convert("RGB"), thumb, Image.Resampling.LANCZOS), (x, y))
        except OSError:
            draw.rectangle((x, y, x + thumb[0], y + thumb[1]), outline="red")
        draw.text((x + 3, y + 139), f"{row['label']} | {Path(row['path']).name}", fill="black")
        draw.text((x + 3, y + 153), row["reason"][:28], fill="black")
    canvas.save(output)


def write_pending_review_sheets(rows: list[dict[str, str]], output: Path, page_size: int = 24) -> None:
    """Create paged visual evidence for the required human context-quality review."""
    output.mkdir(parents=True, exist_ok=True)
    for page, start in enumerate(range(0, len(rows), page_size), 1):
        write_review_sheet(rows[start:start + page_size], output / f"pending_{page:03d}.jpg")


def main() -> None:
    args = parse_args()
    manifest = read_csv(args.inspection / "image_manifest.csv")
    pairs = json.loads((args.inspection / "duplicate_pairs.json").read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)
    by_path = {row["path"]: row for row in manifest}
    groups = UnionFind(list(by_path))
    for pair in pairs:
        groups.union(pair["path_a"], pair["path_b"])
    members: dict[str, list[str]] = defaultdict(list)
    for path in by_path:
        members[groups.find(path)].append(path)
    group_id = {path: f"grp_{index:04d}" for index, paths in enumerate(sorted(members.values(), key=min), 1) for path in paths}
    cross_class_roots = {
        groups.find(path)
        for pair in pairs
        if pair["label_a"] != pair["label_b"]
        for path in (pair["path_a"], pair["path_b"])
    }
    cross_class_paths = {
        path
        for path in by_path
        if groups.find(path) in cross_class_roots
    }
    exact_duplicates: dict[str, list[str]] = defaultdict(list)
    for pair in pairs:
        if pair["kind"] == "exact":
            exact_duplicates[pair["path_a"]].append(pair["path_b"])
    # Pick one canonical source in each exact-hash connected component; all other byte-identical copies are excluded.
    exact_components = UnionFind(list(by_path))
    for pair in pairs:
        if pair["kind"] == "exact":
            exact_components.union(pair["path_a"], pair["path_b"])
    canonical = {min(paths) for paths in defaultdict(list, {root: [path for path in by_path if exact_components.find(path) == root] for root in {exact_components.find(path) for path in by_path}}).values()}
    rows: list[dict[str, str]] = []
    quarantine: list[dict[str, str]] = []
    fields = ["path", "label", "group_id", "status", "reason", "context_review", "reviewer", "reviewed_at"]
    for row in sorted(manifest, key=lambda item: item["path"]):
        path = row["path"]
        status, reason, review = "USABLE_PENDING_CONTEXT_REVIEW", "No automatic semantic-context decision", "PENDING"
        if path in cross_class_paths:
            status, reason, review = "QUARANTINED", "Cross-class near-duplicate candidate; label review required", "PENDING"
        elif exact_components.find(path) != path and path not in canonical:
            status, reason, review = "DUPLICATE", "Non-canonical exact duplicate", "NOT_REQUIRED"
        cleaned = {"path": path, "label": row["label"], "group_id": group_id[path], "status": status, "reason": reason, "context_review": review, "reviewer": "", "reviewed_at": ""}
        rows.append(cleaned)
        if status != "USABLE_PENDING_CONTEXT_REVIEW":
            quarantine.append(cleaned)
    write_csv(args.output / "cleaned_manifest.csv", rows, fields)
    write_csv(args.output / "quarantine.csv", quarantine, fields)
    write_review_sheet(quarantine, args.output / "quarantine_review.jpg")
    write_pending_review_sheets([row for row in rows if row["status"] == "USABLE_PENDING_CONTEXT_REVIEW"], args.output.parent / "review_sheets")
    summary = {"dataset_version": "soil_dataset_v1_cleaning_pending_review", "total": len(rows), "statuses": {status: sum(item["status"] == status for item in rows) for status in sorted({item["status"] for item in rows})}, "policy": "Only rows changed to USABLE after documented human context review may enter a final training split."}
    (args.output / "cleaning_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
