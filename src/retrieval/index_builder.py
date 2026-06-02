# 所有 segment 向量堆起来，建一个 FAISS 索引并保存。

from __future__ import annotations
import json
from pathlib import Path
from typing import List, Tuple

import numpy as np
import faiss

from src.features.feature_store import load_feature


def load_segment_ids_from_manifest(manifest_path: str) -> List[str]:
    ids = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                ids.append(json.loads(line)["segment_id"])
    return ids


def build_faiss_flat_index(features_dir: str, segment_ids: List[str]) -> Tuple[faiss.Index, np.ndarray]:
    """
    Build FAISS IndexFlatIP (inner product) for normalized vectors.
    Returns: index, matrix (N, D)
    """
    vecs = []
    for sid in segment_ids:
        vec = load_feature(features_dir, sid)  # (D,)
        vecs.append(vec)

    mat = np.stack(vecs, axis=0).astype(np.float32)  # (N, D)
    d = mat.shape[1]
    index = faiss.IndexFlatIP(d)
    index.add(mat)
    return index, mat


def save_index(index: faiss.Index, segment_ids: List[str], out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(out / "index.faiss"))
    # 保存 id 映射：faiss 返回的是 row idx，我们需要 row idx -> segment_id
    (out / "segment_ids.json").write_text(json.dumps(segment_ids, ensure_ascii=False, indent=2), encoding="utf-8")