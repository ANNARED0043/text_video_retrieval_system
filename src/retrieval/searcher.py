from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np

from src.features.clip_encoder import encode_text, load_clip


class FaissSearcher:
    def __init__(
        self,
        index_dir: str,
        model_name: str = "ViT-B-32",
        pretrained: str = "openai",
        device: str | None = None,
    ):
        index_dir = Path(index_dir)
        self.index = faiss.read_index(str(index_dir / "index.faiss"))
        self.segment_ids = json.loads((index_dir / "segment_ids.json").read_text(encoding="utf-8"))
        self.clip = load_clip(model_name=model_name, pretrained=pretrained, device=device)

    def search(self, query: str, topk: int = 5) -> List[Tuple[str, float]]:
        q = encode_text(self.clip, query).astype(np.float32)
        q = q.reshape(1, -1)
        scores, idxs = self.index.search(q, topk)
        results: List[Tuple[str, float]] = []
        for i, s in zip(idxs[0], scores[0]):
            if i < 0:
                continue
            results.append((self.segment_ids[int(i)], float(s)))
        return results
