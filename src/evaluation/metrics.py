# 计算 R@K / MedR / MnR。
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
import numpy as np


@dataclass
class RetrievalMetrics:
    r1: float
    r5: float
    r10: float
    medr: float
    mnr: float
    n: int


def compute_metrics(ranks_1based: List[int]) -> RetrievalMetrics:
    """
    ranks_1based: list of ranks for each query (1=best)
    """
    arr = np.array(ranks_1based, dtype=np.int32)
    n = int(arr.shape[0])
    r1 = float((arr <= 1).mean() * 100.0)
    r5 = float((arr <= 5).mean() * 100.0)
    r10 = float((arr <= 10).mean() * 100.0)
    medr = float(np.median(arr))
    mnr = float(np.mean(arr))
    return RetrievalMetrics(r1=r1, r5=r5, r10=r10, medr=medr, mnr=mnr, n=n)