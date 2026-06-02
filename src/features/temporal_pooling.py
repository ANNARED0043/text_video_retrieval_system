# 把多帧 embedding 聚合成一个 segment embedding（mean/max 可切）。

from __future__ import annotations
import numpy as np


def mean_pool(frame_feats: np.ndarray) -> np.ndarray:
    """
    frame_feats: (T, D)
    return: (D,)
    """
    if frame_feats.ndim != 2 or frame_feats.shape[0] == 0:
        raise ValueError("frame_feats must be (T, D) with T>0")
    vec = frame_feats.mean(axis=0)
    vec = vec / (np.linalg.norm(vec) + 1e-12)
    return vec.astype(np.float32)


def max_pool(frame_feats: np.ndarray) -> np.ndarray:
    """
    frame_feats: (T, D)
    return: (D,)
    """
    if frame_feats.ndim != 2 or frame_feats.shape[0] == 0:
        raise ValueError("frame_feats must be (T, D) with T>0")
    vec = frame_feats.max(axis=0)
    vec = vec / (np.linalg.norm(vec) + 1e-12)
    return vec.astype(np.float32)


def pool(frame_feats: np.ndarray, mode: str = "mean") -> np.ndarray:
    """
    mode: 'mean' or 'max'
    """
    mode = mode.lower().strip()
    if mode == "mean":
        return mean_pool(frame_feats)
    if mode == "max":
        return max_pool(frame_feats)
    raise ValueError(f"Unknown pooling mode: {mode}")