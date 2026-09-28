from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms

from app.core.config import settings


class ModelUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class InferenceResult:
    soil_type: str
    confidence: float
    alternatives: list[dict[str, float | str]]
    model_version: str
    warning: str | None


class ClassifierService:
    """Loads one versioned artifact once and applies its serialized preprocessing contract."""

    def __init__(self, artifact_dir: Path | None = None) -> None:
        self.artifact_dir = artifact_dir or settings.model_dir
        self._model: torch.nn.Module | None = None
        self._metadata: dict | None = None

    def _load(self) -> None:
        metadata_path = self.artifact_dir / "metadata.json"
        weights_path = self.artifact_dir / "model.pt"
        if not metadata_path.is_file() or not weights_path.is_file():
            raise ModelUnavailable("No approved trained classifier artifact is installed. Complete data review and training before enabling inference.")
        # The training exporter stores a TorchScript model to avoid architecture drift at serving time.
        self._metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self._model = torch.jit.load(str(weights_path), map_location="cpu").eval()

    def predict(self, image_path: Path) -> InferenceResult:
        if self._model is None or self._metadata is None:
            self._load()
        assert self._model is not None and self._metadata is not None
        preprocessing = self._metadata["preprocessing"]
        transform = transforms.Compose([
            transforms.Resize((preprocessing["image_size"], preprocessing["image_size"])),
            transforms.ToTensor(),
            transforms.Normalize(preprocessing["mean"], preprocessing["std"]),
        ])
        with Image.open(image_path) as image, torch.inference_mode():
            logits = self._model(transform(image.convert("RGB")).unsqueeze(0))
            probabilities = torch.softmax(logits, dim=1)[0]
        labels = self._metadata["class_labels"]
        top_k = min(3, len(labels))
        scores, indices = torch.topk(probabilities, k=top_k)
        alternatives = [{"soil_type": labels[index], "confidence": round(float(score), 6)} for score, index in zip(scores.tolist(), indices.tolist())]
        confidence = float(scores[0])
        return InferenceResult(labels[indices[0]], confidence, alternatives, self._metadata["model_version"], "Prediction confidence is low; obtain another image or expert review." if confidence < 0.60 else None)


classifier_service = ClassifierService()
