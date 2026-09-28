from __future__ import annotations

import torch.nn as nn
from torchvision.models import EfficientNet_B0_Weights, MobileNet_V3_Small_Weights, ResNet50_Weights, efficientnet_b0, mobilenet_v3_small, resnet50


def create_model(architecture: str, classes: int, pretrained: bool = True) -> nn.Module:
    """Create a transfer-learning candidate with a replaceable classifier head."""
    if architecture == "mobilenet_v3_small":
        model = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT if pretrained else None)
        model.classifier[3] = nn.Linear(model.classifier[3].in_features, classes)
    elif architecture == "efficientnet_b0":
        model = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT if pretrained else None)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, classes)
    elif architecture == "resnet50":
        model = resnet50(weights=ResNet50_Weights.DEFAULT if pretrained else None)
        model.fc = nn.Linear(model.fc.in_features, classes)
    else:
        raise ValueError(f"Unsupported architecture: {architecture}")
    return model
