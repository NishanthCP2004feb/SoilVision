"""Reproducible non-neural image-color baseline for comparison only."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from joblib import dump


def features(path: str) -> np.ndarray:
    image = cv2.imread(path)
    if image is None: raise ValueError(f"Cannot decode {path}")
    hsv = cv2.cvtColor(cv2.resize(image, (128, 128)), cv2.COLOR_BGR2HSV)
    return np.concatenate([cv2.calcHist([hsv], [channel], None, [24], [0, 256]).ravel() for channel in range(3)]).astype("float32") / (128 * 128)


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream: return list(csv.DictReader(stream))


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--manifests", type=Path, default=Path("ml/data/manifests")); parser.add_argument("--output", type=Path, default=Path("ml/reports/model_evaluation")); args = parser.parse_args()
    train, validation, test = (read(args.manifests / name) for name in ("train.csv", "validation.csv", "test.csv")); labels = sorted({row["label"] for row in train}); index = {label: value for value, label in enumerate(labels)}
    model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=20260810)
    model.fit(np.vstack([features(row["path"]) for row in train]), [index[row["label"]] for row in train])
    def measure(rows: list[dict[str, str]]) -> dict[str, float]:
        actual = [index[row["label"]] for row in rows]; predicted = model.predict(np.vstack([features(row["path"]) for row in rows])); return {"accuracy": float(accuracy_score(actual, predicted)), "macro_f1": float(f1_score(actual, predicted, average="macro", zero_division=0))}
    args.output.mkdir(parents=True, exist_ok=True); results = {"model": "HSV histogram logistic regression baseline", "validation": measure(validation), "test": measure(test)}
    (args.output / "baseline_metrics.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8"); dump(model, args.output / "baseline.joblib"); print(json.dumps(results, indent=2))


if __name__ == "__main__": main()
