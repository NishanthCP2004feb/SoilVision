"""Export a selected checkpoint with the exact serving contract."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import torch

from ml.src.models.factory import create_model


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("checkpoint", type=Path); parser.add_argument("--architecture", required=True); parser.add_argument("--train-manifest", type=Path, default=Path("ml/data/manifests/train.csv")); parser.add_argument("--output", type=Path, default=Path("ml/artifacts/soil_classifier_v1.0")); args = parser.parse_args()
    with args.train_manifest.open(newline="", encoding="utf-8") as stream: labels = sorted({row["label"] for row in csv.DictReader(stream)})
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=True); model = create_model(args.architecture, len(labels), pretrained=False); model.load_state_dict(state["state_dict"]); model.eval()
    args.output.mkdir(parents=True, exist_ok=True)
    torch.jit.trace(model, torch.zeros(1, 3, 224, 224)).save(str(args.output / "model.pt"))
    torch.save(state["state_dict"], args.output / "state_dict.pt")
    metrics_path = Path("ml/reports/model_evaluation/metrics.json")
    test_metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else None
    metadata = {"model_version": "soil_classifier_v1.0", "architecture": args.architecture, "dataset_version": "soil_dataset_v1_cleaned", "training_date": datetime.now(UTC).isoformat(), "class_labels": labels, "preprocessing": {"image_size": 224, "mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]}, "selection_metric": "validation_macro_f1", "validation_macro_f1": state.get("validation_macro_f1"), "test_metrics": {key: test_metrics[key] for key in ("accuracy", "macro_f1", "weighted_f1", "top_3_accuracy")} if test_metrics else None}
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__": main()
