from __future__ import annotations

import io
import json
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms

from app.core.config import settings
from ml.src.explainability.gradcam import gradcam, overlay
from ml.src.models.factory import create_model


class ExplanationUnavailable(RuntimeError):
    pass


class ExplanationService:
    """Caches an eager model solely for Grad-CAM; inference remains TorchScript."""
    def __init__(self) -> None:
        self.model: torch.nn.Module | None = None
        self.metadata: dict | None = None

    def load(self) -> None:
        metadata_path, state_path = settings.model_dir / "metadata.json", settings.model_dir / "state_dict.pt"
        if not metadata_path.exists() or not state_path.exists(): raise ExplanationUnavailable("Explainability artifact is not installed")
        self.metadata = json.loads(metadata_path.read_text(encoding="utf-8")); self.model = create_model(self.metadata["architecture"], len(self.metadata["class_labels"]), pretrained=False)
        self.model.load_state_dict(torch.load(state_path, map_location="cpu", weights_only=True)); self.model.eval()

    def render(self, image_path: Path) -> bytes:
        if self.model is None or self.metadata is None: self.load()
        assert self.model is not None and self.metadata is not None
        if self.metadata["architecture"] != "mobilenet_v3_small": raise ExplanationUnavailable("The selected architecture does not have a configured Grad-CAM target layer")
        spec = self.metadata["preprocessing"]; transform = transforms.Compose([transforms.Resize((spec["image_size"], spec["image_size"])), transforms.ToTensor(), transforms.Normalize(spec["mean"], spec["std"])])
        with Image.open(image_path) as source:
            image = source.convert("RGB"); heatmap = gradcam(self.model, transform(image).unsqueeze(0), self.model.features[-1]); result = overlay(image, heatmap)
        stream = io.BytesIO(); result.save(stream, format="JPEG", quality=90); return stream.getvalue()


explanation_service = ExplanationService()
