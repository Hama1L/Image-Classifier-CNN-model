"""
Model loading and inference.

We use MobileNetV2 pretrained on ImageNet (1000 everyday object classes).
It's a good first "real" model to deploy: small enough to run on a CPU with
no GPU, but accurate enough to give genuinely useful predictions.

The weights download automatically the first time load_model() runs, then
get cached. In the Docker build, we trigger this download once during the
image build (see Dockerfile) so the container never needs internet access
at request time.
"""

import io
from typing import List, Tuple

import torch
from PIL import Image
from torchvision.models import MobileNet_V2_Weights, mobilenet_v2

_weights = MobileNet_V2_Weights.IMAGENET1K_V2
_transforms = _weights.transforms()
_categories = _weights.meta["categories"]

_model: torch.nn.Module | None = None


def load_model() -> torch.nn.Module:
    """Load the pretrained model once and reuse it for every request.

    Loading a model is slow (disk + weight initialization), so we cache it
    in a module-level variable instead of reloading it per request.
    """
    global _model
    if _model is None:
        _model = mobilenet_v2(weights=_weights)
        _model.eval()  # inference mode: disables dropout/batchnorm training behavior
    return _model


def predict(image_bytes: bytes, top_k: int = 3) -> List[Tuple[str, float]]:
    """Classify an image and return the top_k (label, confidence) predictions.

    Args:
        image_bytes: Raw image file bytes (JPEG/PNG/WEBP).
        top_k: How many top predictions to return.

    Returns:
        A list of (label, confidence) tuples, sorted by confidence descending.
    """
    model = load_model()

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    input_tensor = _transforms(image).unsqueeze(0)  # add batch dimension

    with torch.no_grad():  # no gradients needed for inference -> faster, less memory
        logits = model(input_tensor)
        probabilities = torch.nn.functional.softmax(logits[0], dim=0)

    top_probs, top_idxs = torch.topk(probabilities, top_k)

    return [
        (_categories[idx.item()], float(prob.item()))
        for prob, idx in zip(top_probs, top_idxs)
    ]
