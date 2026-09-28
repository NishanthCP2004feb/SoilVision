"""Create a reproducible quality and leakage report for a class-folder image dataset.

The script is intentionally independent of the training pipeline.  It only reads
the source dataset and writes derived reports, so the original evidence remains
untouched.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
PHASH_SIZE = 32
PHASH_LOW_FREQUENCY_SIZE = 8


@dataclass(frozen=True)
class ImageRecord:
    """Metadata required to audit an image without changing it."""

    path: str
    label: str
    extension: str
    image_format: str
    mode: str
    width: int
    height: int
    bytes: int
    sha256: str
    phash: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="Dataset root with one folder per class")
    parser.add_argument("--output", type=Path, default=Path("ml/reports/dataset_inspection"))
    parser.add_argument(
        "--near-duplicate-distance",
        type=int,
        default=6,
        help="Maximum 64-bit perceptual-hash Hamming distance to flag (default: 6)",
    )
    parser.add_argument("--samples-per-class", type=int, default=6)
    return parser.parse_args()


def dct_basis(size: int) -> np.ndarray:
    """Return an orthogonal DCT-II basis without requiring SciPy."""

    positions = np.arange(size)[:, None] + 0.5
    frequencies = np.arange(size)[None, :]
    return np.cos(np.pi / size * positions * frequencies)


def perceptual_hash(image: Image.Image, basis: np.ndarray) -> int:
    """Return a 64-bit DCT perceptual hash for robust duplicate screening."""

    grayscale = image.convert("L").resize((PHASH_SIZE, PHASH_SIZE), Image.Resampling.LANCZOS)
    pixels = np.asarray(grayscale, dtype=np.float64)
    coefficients = basis.T @ pixels @ basis
    low_frequency = coefficients[:PHASH_LOW_FREQUENCY_SIZE, :PHASH_LOW_FREQUENCY_SIZE].ravel()
    median = np.median(low_frequency[1:])  # Exclude the brightness-dominant DC coefficient.
    return sum(int(value > median) << index for index, value in enumerate(low_frequency))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_images(dataset: Path) -> tuple[list[ImageRecord], list[dict[str, str]]]:
    """Decode every supported file and collect deterministic metadata."""

    basis = dct_basis(PHASH_SIZE)
    records: list[ImageRecord] = []
    corrupted: list[dict[str, str]] = []
    for class_dir in sorted(path for path in dataset.iterdir() if path.is_dir()):
        for path in sorted(item for item in class_dir.rglob("*") if item.is_file()):
            if path.suffix.lower() not in IMAGE_EXTENSIONS:
                corrupted.append({"path": str(path), "reason": "Unsupported extension"})
                continue
            try:
                with Image.open(path) as opened:
                    opened.verify()
                with Image.open(path) as opened:
                    image = opened.convert("RGB")
                    records.append(
                        ImageRecord(
                            path=path.as_posix(),
                            label=class_dir.name,
                            extension=path.suffix.lower(),
                            image_format=opened.format or "unknown",
                            mode=opened.mode,
                            width=opened.width,
                            height=opened.height,
                            bytes=path.stat().st_size,
                            sha256=file_sha256(path),
                            phash=perceptual_hash(image, basis),
                        )
                    )
            except (OSError, ValueError, Image.DecompressionBombError) as error:
                corrupted.append({"path": path.as_posix(), "reason": str(error)})
    return records, corrupted


def connected_components(records: list[ImageRecord], pairs: list[dict[str, object]]) -> list[list[ImageRecord]]:
    """Build groups that must be kept together during a future split."""

    parent = list(range(len(records)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(first: int, second: int) -> None:
        first_root, second_root = find(first), find(second)
        if first_root != second_root:
            parent[second_root] = first_root

    index_by_path = {record.path: index for index, record in enumerate(records)}
    for pair in pairs:
        union(index_by_path[str(pair["path_a"])], index_by_path[str(pair["path_b"])])
    groups: dict[int, list[ImageRecord]] = defaultdict(list)
    for index, record in enumerate(records):
        groups[find(index)].append(record)
    return [group for group in groups.values() if len(group) > 1]


def duplicate_audit(records: list[ImageRecord], maximum_distance: int) -> tuple[list[dict[str, object]], list[list[ImageRecord]]]:
    """Find exact and visually near duplicate pairs using SHA-256 and pHash."""

    exact_by_hash: dict[str, list[ImageRecord]] = defaultdict(list)
    for record in records:
        exact_by_hash[record.sha256].append(record)

    pairs: dict[tuple[str, str], dict[str, object]] = {}
    for group in exact_by_hash.values():
        for first, second in combinations(group, 2):
            key = tuple(sorted((first.path, second.path)))
            pairs[key] = {
                "path_a": key[0],
                "label_a": first.label if first.path == key[0] else second.label,
                "path_b": key[1],
                "label_b": second.label if second.path == key[1] else first.label,
                "kind": "exact",
                "phash_distance": 0,
            }
    for first, second in combinations(records, 2):
        distance = (first.phash ^ second.phash).bit_count()
        if distance <= maximum_distance:
            key = tuple(sorted((first.path, second.path)))
            current = pairs.get(key)
            if current is None:
                pairs[key] = {
                    "path_a": key[0],
                    "label_a": first.label if first.path == key[0] else second.label,
                    "path_b": key[1],
                    "label_b": second.label if second.path == key[1] else first.label,
                    "kind": "near",
                    "phash_distance": distance,
                }
    ordered_pairs = sorted(pairs.values(), key=lambda item: (int(item["phash_distance"]), str(item["path_a"])))
    return ordered_pairs, connected_components(records, ordered_pairs)


def create_contact_sheet(records: list[ImageRecord], output: Path, samples_per_class: int) -> None:
    """Create a deterministic representative visual sample for manual review."""

    by_label: dict[str, list[ImageRecord]] = defaultdict(list)
    for record in records:
        by_label[record.label].append(record)
    thumb_width, thumb_height, label_height = 180, 135, 24
    labels = sorted(by_label)
    rows = len(labels)
    columns = samples_per_class
    canvas = Image.new("RGB", (columns * thumb_width, rows * (thumb_height + label_height)), "white")
    draw = ImageDraw.Draw(canvas)
    for row, label in enumerate(labels):
        samples = sorted(by_label[label], key=lambda record: record.path)[:samples_per_class]
        for column, record in enumerate(samples):
            with Image.open(record.path) as source:
                thumbnail = ImageOps.fit(source.convert("RGB"), (thumb_width, thumb_height), Image.Resampling.LANCZOS)
            x, y = column * thumb_width, row * (thumb_height + label_height)
            canvas.paste(thumbnail, (x, y))
            caption = f"{label}: {Path(record.path).name}"
            draw.text((x + 3, y + thumb_height + 4), caption, fill="black")
    canvas.save(output)


def write_csv(records: list[ImageRecord], output: Path) -> None:
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        for record in records:
            row = asdict(record)
            row["phash"] = f"{record.phash:016x}"
            writer.writerow(row)


def write_markdown(report: dict[str, object], output: Path) -> None:
    distribution = report["class_distribution"]
    duplicate_summary = report["duplicates"]
    lines = [
        "# Dataset Inspection Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Dataset root: `{report['dataset_root']}`",
        f"- Valid images: {report['valid_images']}",
        f"- Corrupted or unsupported files: {report['corrupted_or_unsupported_files']}",
        f"- Classes: {len(distribution)}",
        f"- Pixel dimensions: {report['min_width']}–{report['max_width']} wide × {report['min_height']}–{report['max_height']} high",
        "",
        "## Class distribution",
        "",
        "| Class | Images | Share |",
        "| --- | ---: | ---: |",
    ]
    total = int(report["valid_images"])
    lines.extend(f"| {label} | {count} | {count / total:.1%} |" for label, count in distribution.items())
    lines.extend(
        [
            "",
            "## Leakage and cleaning findings",
            "",
            f"- Exact-duplicate pairs: {duplicate_summary['exact_pairs']}",
            f"- Near-duplicate pairs (pHash distance ≤ {duplicate_summary['threshold']}): {duplicate_summary['near_pairs']}",
            f"- Cross-class duplicate/near-duplicate pairs requiring label review: {duplicate_summary['cross_class_pairs']}",
            f"- Related-image groups that must not cross train/validation/test boundaries: {duplicate_summary['related_groups']}",
            "- The dataset is materially imbalanced; class-weighted loss and macro-F1 are required for model selection.",
            "- Do not remove or split the original files in place. A later split must operate from the generated manifest and preserve every related-image group.",
            "",
            "## Scientific label availability",
            "",
            "The dataset contains image files arranged by soil class only. It contains no image-level pH, N, P, K, moisture, organic-carbon, EC, weather, or location labels. This release therefore supports soil-type classification only; soil-property regression must remain unavailable until ground-truth measurements are supplied.",
            "",
            "## Generated artifacts",
            "",
            "- `dataset_report.json`: machine-readable audit",
            "- `image_manifest.csv`: image metadata and hashes",
            "- `duplicate_pairs.json`: records to group/review before splitting",
            "- `representative_samples.jpg`: deterministic visual sample sheet",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    if not args.dataset.is_dir():
        raise SystemExit(f"Dataset directory does not exist: {args.dataset}")
    args.output.mkdir(parents=True, exist_ok=True)
    records, corrupted = inspect_images(args.dataset)
    if not records:
        raise SystemExit("No valid supported images were found.")
    pairs, related_groups = duplicate_audit(records, args.near_duplicate_distance)
    distribution = Counter(record.label for record in records)
    exact_pairs = sum(1 for pair in pairs if pair["kind"] == "exact")
    cross_class_pairs = sum(1 for pair in pairs if pair["label_a"] != pair["label_b"])
    dimensions = Counter((record.width, record.height) for record in records)
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_root": args.dataset.as_posix(),
        "valid_images": len(records),
        "corrupted_or_unsupported_files": len(corrupted),
        "class_distribution": dict(sorted(distribution.items())),
        "formats": dict(sorted(Counter(record.image_format for record in records).items())),
        "extensions": dict(sorted(Counter(record.extension for record in records).items())),
        "modes": dict(sorted(Counter(record.mode for record in records).items())),
        "unique_dimensions": len(dimensions),
        "most_common_dimensions": [{"width": width, "height": height, "count": count} for (width, height), count in dimensions.most_common(25)],
        "min_width": min(record.width for record in records),
        "max_width": max(record.width for record in records),
        "min_height": min(record.height for record in records),
        "max_height": max(record.height for record in records),
        "duplicates": {
            "threshold": args.near_duplicate_distance,
            "exact_pairs": exact_pairs,
            "near_pairs": len(pairs) - exact_pairs,
            "cross_class_pairs": cross_class_pairs,
            "related_groups": len(related_groups),
        },
    }
    write_csv(records, args.output / "image_manifest.csv")
    (args.output / "duplicate_pairs.json").write_text(json.dumps(pairs, indent=2) + "\n", encoding="utf-8")
    (args.output / "related_groups.json").write_text(
        json.dumps([[record.path for record in group] for group in related_groups], indent=2) + "\n", encoding="utf-8"
    )
    (args.output / "dataset_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.output / "corrupted_or_unsupported.json").write_text(json.dumps(corrupted, indent=2) + "\n", encoding="utf-8")
    create_contact_sheet(records, args.output / "representative_samples.jpg", args.samples_per_class)
    write_markdown(report, args.output / "DATASET_REPORT.md")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
