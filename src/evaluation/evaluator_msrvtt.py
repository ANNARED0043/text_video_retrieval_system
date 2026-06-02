# 用“segment 检索结果”评估“video-level retrieval”
# segment-level -> video-level (max aggregation) -> compute ranks -> metrics + latency

from __future__ import annotations

import json
import time
from typing import Dict, List, Tuple, Optional

from tqdm import tqdm

from src.retrieval.searcher import FaissSearcher
from src.evaluation.metrics import compute_metrics, RetrievalMetrics


def load_manifest_segment_to_video(manifest_jsonl: str) -> Dict[str, str]:
    """segment_id -> video_id"""
    mapping: Dict[str, str] = {}
    with open(manifest_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            mapping[row["segment_id"]] = row["video_id"]
    return mapping


def load_queries_jsonl(queries_jsonl: str) -> List[dict]:
    rows: List[dict] = []
    with open(queries_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _percentile(sorted_vals: List[float], p: float) -> float:
    """p in [0,100], vals must be sorted ascending."""
    if not sorted_vals:
        return 0.0
    if p <= 0:
        return sorted_vals[0]
    if p >= 100:
        return sorted_vals[-1]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (k - f) * (sorted_vals[c] - sorted_vals[f])


def eval_msrvtt_video_retrieval(
    searcher: FaissSearcher,
    queries_jsonl: str,
    manifest_jsonl: str,
    topk_segments: int = 200,
    max_queries: Optional[int] = None,
    log_every: int = 50,
) -> Tuple[RetrievalMetrics, List[int], dict]:
    """
    Evaluate text->video retrieval.

    Steps:
      1) Search topk_segments segments
      2) Aggregate segment scores to video scores by MAX
      3) Rank videos by score desc
      4) GT rank: 1-based; if not present, rank = len(ranked)+1

    Returns:
      metrics, ranks, latency_dict
    """
    t0 = time.time()
    print("[eval] loading seg2vid ...")
    seg2vid = load_manifest_segment_to_video(manifest_jsonl)
    print(f"[eval] seg2vid size = {len(seg2vid)}")

    print("[eval] loading queries ...")
    queries = load_queries_jsonl(queries_jsonl)
    if max_queries is not None:
        queries = queries[:max_queries]
    print(f"[eval] queries = {len(queries)}")

    ranks: List[int] = []

    # latency collectors (seconds)
    search_times: List[float] = []     # searcher.search total time (encode + faiss inside)
    agg_times: List[float] = []        # seg->video aggregation + ranking time
    total_times: List[float] = []      # end-to-end per query time

    pbar = tqdm(queries, desc=f"Eval (topk_segments={topk_segments})", dynamic_ncols=True)

    for idx, q in enumerate(pbar, start=1):
        query = q["query"]
        gt_vid = q["gt_video_id"]

        t_all0 = time.time()

        # ---- search timing (includes text encoding inside searcher) ----
        ts = time.time()
        seg_results = searcher.search(query, topk=topk_segments)  # [(seg_id, score), ...]
        t_search = time.time() - ts
        search_times.append(t_search)

        # ---- aggregate to video scores by max ----
        ta = time.time()
        vid2score: Dict[str, float] = {}
        for seg_id, score in seg_results:
            vid = seg2vid.get(seg_id)
            if vid is None:
                continue
            prev = vid2score.get(vid)
            if prev is None or score > prev:
                vid2score[vid] = score

        ranked = sorted(vid2score.items(), key=lambda x: x[1], reverse=True)

        # ---- find gt rank ----
        rank = len(ranked) + 1
        for i, (vid, _) in enumerate(ranked, start=1):
            if vid == gt_vid:
                rank = i
                break

        t_agg = time.time() - ta
        agg_times.append(t_agg)

        t_total = time.time() - t_all0
        total_times.append(t_total)

        ranks.append(rank)

        # ---- progress info ----
        if idx == 1 or (log_every > 0 and idx % log_every == 0):
            win = min(log_every, len(search_times))
            avg_search = sum(search_times[-win:]) / win
            avg_agg = sum(agg_times[-win:]) / win
            avg_total = sum(total_times[-win:]) / win
            pbar.set_postfix({
                "last_rank": rank,
                "search_ms": f"{avg_search*1000:.1f}",
                "agg_ms": f"{avg_agg*1000:.1f}",
                "total_ms": f"{avg_total*1000:.1f}",
            })

    metrics = compute_metrics(ranks)

    elapsed = time.time() - t0

    # summarize latency (ms)
    s_sorted = sorted(search_times)
    a_sorted = sorted(agg_times)
    t_sorted = sorted(total_times)

    latency = {
        "elapsed_s": round(elapsed, 3),
        "N": len(ranks),

        "search_ms": {
            "avg": round((sum(search_times) / max(1, len(search_times))) * 1000, 3),
            "p50": round(_percentile(s_sorted, 50) * 1000, 3),
            "p90": round(_percentile(s_sorted, 90) * 1000, 3),
            "p95": round(_percentile(s_sorted, 95) * 1000, 3),
        },
        "aggregate_ms": {
            "avg": round((sum(agg_times) / max(1, len(agg_times))) * 1000, 3),
            "p50": round(_percentile(a_sorted, 50) * 1000, 3),
            "p90": round(_percentile(a_sorted, 90) * 1000, 3),
            "p95": round(_percentile(a_sorted, 95) * 1000, 3),
        },
        "total_ms": {
            "avg": round((sum(total_times) / max(1, len(total_times))) * 1000, 3),
            "p50": round(_percentile(t_sorted, 50) * 1000, 3),
            "p90": round(_percentile(t_sorted, 90) * 1000, 3),
            "p95": round(_percentile(t_sorted, 95) * 1000, 3),
        },
    }

    print(f"[eval] done. elapsed={elapsed:.1f}s "
          f"search_avg={latency['search_ms']['avg']:.1f}ms "
          f"agg_avg={latency['aggregate_ms']['avg']:.1f}ms "
          f"total_avg={latency['total_ms']['avg']:.1f}ms")

    return metrics, ranks, latency