"""Handlers de inferencia para SageMaker PyTorch container.

SageMaker PyTorch Inference llama estas funciones en orden:
    model_fn(model_dir) -> model
    input_fn(request_body, content_type) -> input_data
    predict_fn(input_data, model) -> prediction
    output_fn(prediction, accept) -> response_body

Empaquetar este archivo junto con model.pth en model.tar.gz al registrar el
Model Package (lo hace SageMaker automaticamente si se incluye source_dir).
"""
import io
import json
import os
import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms
from torchvision.models import mobilenet_v2

CLASS_NAMES = ["good_quality", "bad_quality"]

# Transform de inferencia: igual al eval_transform del training
_inference_transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)


def model_fn(model_dir):
    model = mobilenet_v2(weights=None)
    model.classifier[1] = nn.Linear(model.last_channel, 2)
    state_dict = torch.load(os.path.join(model_dir, "modelo_a.pth"), map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()
    return model


def input_fn(request_body, content_type):
    if content_type == "application/x-image":
        img = Image.open(io.BytesIO(request_body)).convert("RGB")
        return _inference_transform(img).unsqueeze(0)
    raise ValueError(f"Content type no soportado: {content_type}")


def predict_fn(input_data, model):
    with torch.no_grad():
        logits = model(input_data)
        probs = torch.softmax(logits, dim=1)[0]
        idx = int(probs.argmax().item())
    return {
        "class": idx,
        "class_name": CLASS_NAMES[idx],
        "confidence": float(probs[idx].item()),
        "probs": probs.tolist(),
    }


def output_fn(prediction, accept):
    return json.dumps(prediction), accept or "application/json"
