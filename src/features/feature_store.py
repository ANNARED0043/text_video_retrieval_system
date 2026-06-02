# 统一保存/读取 segment 特征（按 segment_id 存 .npy，简单稳定
from __future__ import annotations
from pathlib import Path
import numpy as np


def feature_path(features_dir: str, segment_id: str) -> Path:
    return Path(features_dir) / f"{segment_id}.npy"


def save_feature(features_dir: str, segment_id: str, vec: np.ndarray) -> None:
    out = feature_path(features_dir, segment_id)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(out), vec.astype(np.float32))


def load_feature(features_dir: str, segment_id: str) -> np.ndarray:
    p = feature_path(features_dir, segment_id)
    return np.load(str(p)).astype(np.float32)


def exists(features_dir: str, segment_id: str) -> bool:
    return feature_path(features_dir, segment_id).exists()