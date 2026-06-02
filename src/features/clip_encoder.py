# 加载 CLIP 模型、把一批帧变成 embedding。
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
import torch
import open_clip


@dataclass
class ClipModelBundle:
    model: torch.nn.Module
    preprocess: callable
    tokenizer: callable
    device: str


def _local_pretrained_weight_path(model_name: str, pretrained: str) -> str | None:
    repo_map = {
        ("ViT-H-14", "laion2b_s32b_b79k"): "laion/CLIP-ViT-H-14-laion2B-s32B-b79K",
    }
    repo_id = repo_map.get((model_name, pretrained))
    if repo_id is None:
        return None

    repo_dir = Path.home() / ".cache" / "huggingface" / "hub" / f"models--{repo_id.replace('/', '--')}" / "snapshots"
    if not repo_dir.exists():
        return None

    for snapshot_dir in sorted(repo_dir.iterdir(), reverse=True):
        if not snapshot_dir.is_dir():
            continue
        for filename in ("open_clip_pytorch_model.bin", "open_clip_model.safetensors"):
            candidate = snapshot_dir / filename
            if candidate.exists():
                return str(candidate)
    return None


def load_clip(model_name: str = "ViT-B-32", pretrained: str = "openai", device: str | None = None) -> ClipModelBundle:
    """
    Load OpenCLIP model for image+text encoding.
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    pretrained_ref = _local_pretrained_weight_path(model_name, pretrained) or pretrained
    model, _, preprocess = open_clip.create_model_and_transforms(model_name, pretrained=pretrained_ref)
    tokenizer = open_clip.get_tokenizer(model_name)
    model = model.to(device)
    model.eval()
    return ClipModelBundle(model=model, preprocess=preprocess, tokenizer=tokenizer, device=device)


@torch.no_grad()
def encode_images(model_bundle: ClipModelBundle, images_rgb_uint8: List[np.ndarray], batch_size: int = 16) -> np.ndarray:
    """
    Encode a list of RGB images (uint8 HxWx3) into CLIP embeddings.
    Returns: (N, D) float32
    """
    device = model_bundle.device
    model = model_bundle.model
    preprocess = model_bundle.preprocess

    # preprocess uses PIL; convert via PIL inside
    from PIL import Image

    feats = []
    for i in range(0, len(images_rgb_uint8), batch_size):
        batch = images_rgb_uint8[i:i + batch_size]
        pil_imgs = [Image.fromarray(img) for img in batch]
        input_tensor = torch.stack([preprocess(im) for im in pil_imgs]).to(device)

        img_feat = model.encode_image(input_tensor)
        img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
        feats.append(img_feat.detach().cpu().numpy().astype(np.float32))

    return np.concatenate(feats, axis=0)


@torch.no_grad()
def encode_text(model_bundle: ClipModelBundle, text: str) -> np.ndarray:
    """
    Encode a query text into CLIP text embedding. Returns (D,) float32.
    """
    device = model_bundle.device
    model = model_bundle.model
    tokenizer = model_bundle.tokenizer

    tokens = tokenizer([text]).to(device)
    txt_feat = model.encode_text(tokens)
    txt_feat = txt_feat / txt_feat.norm(dim=-1, keepdim=True)
    return txt_feat.squeeze(0).detach().cpu().numpy().astype(np.float32)
