"""Generate a Grad-CAM overlay from an eager selected model and its target layer."""
from __future__ import annotations

import numpy as np
import torch
from PIL import Image


def gradcam(model: torch.nn.Module, image: torch.Tensor, target_layer: torch.nn.Module, target_class: int | None = None) -> np.ndarray:
    """Return a normalized heatmap; it is an interpretability aid, not proof of correctness."""
    activations: list[torch.Tensor] = []; gradients: list[torch.Tensor] = []
    forward = target_layer.register_forward_hook(lambda _, __, output: activations.append(output))
    backward = target_layer.register_full_backward_hook(lambda _, __, output: gradients.append(output[0]))
    try:
        output = model(image); class_index = int(output.argmax(1).item()) if target_class is None else target_class
        model.zero_grad(); output[0, class_index].backward()
        weights = gradients[0].mean(dim=(2, 3), keepdim=True); heatmap = torch.relu((weights * activations[0]).sum(1))[0]
        heatmap = heatmap.detach().cpu().numpy(); return (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8)
    finally:
        forward.remove(); backward.remove()


def overlay(image: Image.Image, heatmap: np.ndarray, opacity: float = 0.42) -> Image.Image:
    resized = Image.fromarray(np.uint8(heatmap * 255)).resize(image.size, Image.Resampling.BILINEAR)
    colored = Image.merge("RGB", (resized, Image.new("L", image.size), Image.eval(resized, lambda value: 255 - value)))
    return Image.blend(image.convert("RGB"), colored, opacity)
