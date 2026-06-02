from __future__ import annotations

import importlib
import importlib.util
import os
import sys
import types
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import torch
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file


VICLIP_REPO_ID = "OpenGVLab/ViCLIP-L-14-hf"
VICLIP_REVISION = "1652361522e1cb41c28cdfae870f690d00e7456b"
V_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 1, 3)
V_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 1, 3)


@dataclass
class ViCLIPBundle:
    model: torch.nn.Module
    tokenizer: object
    device: str
    num_frames: int = 8
    image_size: tuple[int, int] = (224, 224)


def _snapshot_dir() -> Path:
    config_path = hf_hub_download(VICLIP_REPO_ID, "config.json", revision=VICLIP_REVISION)
    return Path(config_path).parent


def _candidate_module_roots() -> list[Path]:
    roots: list[Path] = []
    env_hf_home = os.environ.get("HF_HOME", "").strip()
    if env_hf_home:
        roots.append(Path(env_hf_home) / "modules")
    env_huggingface_home = os.environ.get("HUGGINGFACE_HUB_CACHE", "").strip()
    if env_huggingface_home:
        roots.append(Path(env_huggingface_home).parent / "modules")
    roots.append(Path.home() / ".cache" / "huggingface" / "modules")
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app_data:
        roots.append(Path(local_app_data) / "huggingface" / "modules")

    uniq: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root).lower()
        if key not in seen:
            uniq.append(root)
            seen.add(key)
    return uniq


def _find_dynamic_module_pkg(base_dir: Path) -> str | None:
    package_rel = Path("transformers_modules") / "OpenGVLab" / "ViCLIP_hyphen_L_hyphen_14_hyphen_hf" / base_dir.name
    for modules_root in _candidate_module_roots():
        package_dir = modules_root / package_rel
        if package_dir.exists():
            if str(modules_root) not in sys.path:
                sys.path.insert(0, str(modules_root))
            return ".".join(package_rel.parts)
    return None


def _ensure_local_package(package_name: str, package_dir: Path) -> None:
    if package_name in sys.modules:
        return
    pkg = types.ModuleType(package_name)
    pkg.__path__ = [str(package_dir)]
    sys.modules[package_name] = pkg


def _load_module_from_file(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create spec for {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _required_snapshot_files(base_dir: Path) -> list[Path]:
    return [
        base_dir / "configuration_viclip.py",
        base_dir / "viclip.py",
        base_dir / "model.safetensors",
        base_dir / "bpe_simple_vocab_16e6.txt.gz",
    ]


def load_viclip(device: str | None = None) -> ViCLIPBundle:
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    base_dir = _snapshot_dir()
    tokenizer_path = str(base_dir / "bpe_simple_vocab_16e6.txt.gz")
    model_path = base_dir / "model.safetensors"
    missing_required = [str(path) for path in _required_snapshot_files(base_dir) if not path.exists()]
    if missing_required:
        raise FileNotFoundError(
            "ViCLIP local snapshot is incomplete. Missing files: "
            + ", ".join(missing_required)
            + ". Please ensure the full HuggingFace snapshot is available locally."
        )

    base_pkg = _find_dynamic_module_pkg(base_dir)
    if base_pkg is not None:
        config_mod = importlib.import_module(base_pkg + ".configuration_viclip")
        viclip_mod = importlib.import_module(base_pkg + ".viclip")
    else:
        local_pkg = "viclip_local_pkg"
        _ensure_local_package(local_pkg, base_dir)
        config_mod = _load_module_from_file(f"{local_pkg}.configuration_viclip", base_dir / "configuration_viclip.py")
        viclip_mod = _load_module_from_file(f"{local_pkg}.viclip", base_dir / "viclip.py")
    cfg = config_mod.Config(size="l", tokenizer_path=tokenizer_path)
    model = viclip_mod.ViCLIP(cfg)
    state = load_file(str(model_path))
    missing, unexpected = model.load_state_dict(state, strict=False)
    if missing or unexpected:
        raise RuntimeError(
            f"Unexpected ViCLIP state mismatch: missing={len(missing)} unexpected={len(unexpected)}"
        )
    model = model.to(device)
    model.eval()
    return ViCLIPBundle(model=model, tokenizer=model.tokenizer, device=device)


def _normalize_frame(frame_rgb: np.ndarray) -> np.ndarray:
    return (frame_rgb.astype(np.float32) / 255.0 - V_MEAN) / V_STD


def sample_viclip_frames(
    video_path: str,
    num_frames: int = 8,
    target_size: tuple[int, int] = (224, 224),
) -> torch.Tensor:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video for ViCLIP: {video_path}")

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_count <= 0:
        cap.release()
        raise RuntimeError(f"Invalid frame count for ViCLIP: {video_path}")

    positions = np.linspace(0, max(frame_count - 1, 0), num=num_frames, dtype=int)
    frames: list[np.ndarray] = []
    for pos in positions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(pos))
        ok, bgr = cap.read()
        if not ok or bgr is None:
            break
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, target_size)
        frames.append(_normalize_frame(resized))
    cap.release()

    if not frames:
        raise RuntimeError(f"No readable frames for ViCLIP: {video_path}")

    while len(frames) < num_frames:
        frames.append(frames[-1].copy())

    tube = np.stack(frames[:num_frames], axis=0)  # T H W C
    tube = np.transpose(tube, (0, 3, 1, 2))  # T C H W
    tube = np.expand_dims(tube, axis=0)  # 1 T C H W
    return torch.from_numpy(tube).float()


@torch.no_grad()
def encode_text_viclip(bundle: ViCLIPBundle, text: str) -> np.ndarray:
    feat = bundle.model.get_text_features(text, bundle.tokenizer)
    feat = feat / feat.norm(dim=-1, keepdim=True)
    return feat.squeeze(0).detach().cpu().numpy().astype(np.float32)


@torch.no_grad()
def encode_video_viclip(bundle: ViCLIPBundle, video_path: str) -> np.ndarray:
    frames = sample_viclip_frames(video_path, num_frames=bundle.num_frames, target_size=bundle.image_size)
    frames = frames.to(bundle.device, non_blocking=True)
    feat = bundle.model.get_vid_features(frames)
    feat = feat / feat.norm(dim=-1, keepdim=True)
    return feat.squeeze(0).detach().cpu().numpy().astype(np.float32)
