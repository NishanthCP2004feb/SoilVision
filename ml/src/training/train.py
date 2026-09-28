"""Train one approved classifier candidate; never reads the final test split."""
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms
from PIL import Image

from ml.src.models.factory import create_model

MEAN, STD, IMAGE_SIZE = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225], 224


class ManifestDataset(Dataset):
    def __init__(self, csv_path: Path, labels: list[str], training: bool) -> None:
        with csv_path.open(newline="", encoding="utf-8") as stream:
            self.rows = list(csv.DictReader(stream))
        self.label_index = {label: index for index, label in enumerate(labels)}
        base = [transforms.Resize((IMAGE_SIZE, IMAGE_SIZE))]
        if training:
            base += [transforms.RandomHorizontalFlip(), transforms.RandomRotation(10), transforms.ColorJitter(brightness=0.12, contrast=0.12, saturation=0.06)]
        self.transform = transforms.Compose(base + [transforms.ToTensor(), transforms.Normalize(MEAN, STD)])

    def __len__(self) -> int: return len(self.rows)
    def __getitem__(self, index: int):
        row = self.rows[index]
        with Image.open(row["path"]) as image:
            return self.transform(image.convert("RGB")), self.label_index[row["label"]]


def seed_everything(seed: int) -> None:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--architecture", choices=["mobilenet_v3_small", "efficientnet_b0", "resnet50"], default="mobilenet_v3_small")
    parser.add_argument("--manifests", type=Path, default=Path("ml/data/manifests"))
    parser.add_argument("--artifacts", type=Path, default=Path("ml/artifacts"))
    parser.add_argument("--epochs", type=int, default=20); parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=20260810); parser.add_argument("--patience", type=int, default=5)
    return parser.parse_args()


def validation_macro_f1(model: nn.Module, loader: DataLoader, device: torch.device, classes: int) -> float:
    from sklearn.metrics import f1_score
    model.eval(); actual, predicted = [], []
    with torch.inference_mode():
        for images, labels in loader:
            output = model(images.to(device)); predicted.extend(output.argmax(1).cpu().tolist()); actual.extend(labels.tolist())
    return float(f1_score(actual, predicted, labels=list(range(classes)), average="macro", zero_division=0))


def main() -> None:
    args = parse_args(); seed_everything(args.seed)
    train_path, validation_path = args.manifests / "train.csv", args.manifests / "validation.csv"
    if not train_path.exists() or not validation_path.exists(): raise SystemExit("Approved grouped train.csv and validation.csv are required; test.csv is intentionally not read here.")
    with train_path.open(newline="", encoding="utf-8") as stream: train_rows = list(csv.DictReader(stream))
    labels = sorted({row["label"] for row in train_rows})
    train, validation = ManifestDataset(train_path, labels, True), ManifestDataset(validation_path, labels, False)
    counts = np.bincount([train.label_index[row["label"]] for row in train.rows], minlength=len(labels))
    sampler = WeightedRandomSampler([1 / counts[train.label_index[row["label"]]] for row in train.rows], len(train), replacement=True)
    train_loader = DataLoader(train, batch_size=args.batch_size, sampler=sampler); validation_loader = DataLoader(validation, batch_size=args.batch_size)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = create_model(args.architecture, len(labels), pretrained=True).to(device)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(len(train) / (len(labels) * counts), dtype=torch.float32, device=device))
    optimizer = AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4); scheduler = ReduceLROnPlateau(optimizer, mode="max", patience=2, factor=0.3)
    best, stale, checkpoint = -1.0, 0, args.artifacts / f"{args.architecture}_best.pt"; args.artifacts.mkdir(parents=True, exist_ok=True)
    for epoch in range(1, args.epochs + 1):
        model.train()
        for images, targets in train_loader:
            optimizer.zero_grad(); loss = criterion(model(images.to(device)), targets.to(device)); loss.backward(); optimizer.step()
        score = validation_macro_f1(model, validation_loader, device, len(labels)); scheduler.step(score)
        if score > best:
            best, stale = score, 0; torch.save({"state_dict": model.state_dict(), "epoch": epoch, "validation_macro_f1": score}, checkpoint)
        else: stale += 1
        print(json.dumps({"epoch": epoch, "validation_macro_f1": score, "best": best}))
        if stale >= args.patience: break
    print(json.dumps({"checkpoint": str(checkpoint), "best_validation_macro_f1": best, "next_step": "Run ml/src/evaluation/evaluate.py once to evaluate this selected checkpoint on the untouched test split."}))


if __name__ == "__main__": main()
