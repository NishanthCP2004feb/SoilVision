"""Evaluate a selected checkpoint on the untouched test partition once."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from torch.utils.data import DataLoader

from ml.src.models.factory import create_model
from ml.src.training.train import ManifestDataset


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("checkpoint", type=Path); parser.add_argument("--architecture", required=True); parser.add_argument("--manifests", type=Path, default=Path("ml/data/manifests")); parser.add_argument("--output", type=Path, default=Path("ml/reports/model_evaluation")); args = parser.parse_args()
    with (args.manifests / "train.csv").open(newline="", encoding="utf-8") as stream: labels = sorted({row["label"] for row in csv.DictReader(stream)})
    dataset = ManifestDataset(args.manifests / "test.csv", labels, False); loader = DataLoader(dataset, batch_size=32)
    model = create_model(args.architecture, len(labels), pretrained=False); model.load_state_dict(torch.load(args.checkpoint, map_location="cpu", weights_only=True)["state_dict"]); model.eval()
    actual, predictions, probabilities = [], [], []
    with torch.inference_mode():
        for images, targets in loader:
            output = model(images); probabilities.extend(torch.softmax(output, 1).tolist()); predictions.extend(output.argmax(1).tolist()); actual.extend(targets.tolist())
    matrix = confusion_matrix(actual, predictions, labels=list(range(len(labels))))
    per_class = classification_report(actual, predictions, target_names=labels, output_dict=True, zero_division=0)
    metrics = {"status": "COMPLETED", "accuracy": accuracy_score(actual, predictions), "macro_f1": f1_score(actual, predictions, average="macro", zero_division=0), "weighted_f1": f1_score(actual, predictions, average="weighted", zero_division=0), "top_3_accuracy": sum(target in sorted(range(len(row)), key=lambda index: row[index], reverse=True)[:3] for target, row in zip(actual, probabilities)) / len(actual), "per_class": per_class, "confusion_matrix": matrix.tolist()}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(matrix, index=labels, columns=labels).to_csv(args.output / "confusion_matrix.csv")
    pd.DataFrame({label: {metric: values.get(metric) for metric in ("precision", "recall", "f1-score", "support")} for label, values in per_class.items() if label in labels}).T.to_csv(args.output / "per_class_metrics.csv")
    figure, axis = plt.subplots(figsize=(8, 6)); image = axis.imshow(matrix, cmap="YlGnBu"); figure.colorbar(image, ax=axis); axis.set(xticks=range(len(labels)), yticks=range(len(labels)), xticklabels=labels, yticklabels=labels, xlabel="Predicted", ylabel="Actual", title="Test Confusion Matrix")
    plt.setp(axis.get_xticklabels(), rotation=45, ha="right")
    for row in range(len(labels)):
        for column in range(len(labels)): axis.text(column, row, str(matrix[row, column]), ha="center", va="center")
    figure.tight_layout(); figure.savefig(args.output / "confusion_matrix.png", dpi=180); plt.close(figure)
    print(json.dumps({key: metrics[key] for key in ("accuracy", "macro_f1", "weighted_f1", "top_3_accuracy")}, indent=2))


if __name__ == "__main__": main()
