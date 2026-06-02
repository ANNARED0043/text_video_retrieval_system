from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
import sys
from dotenv import load_dotenv

script_path = Path(__file__).resolve()
root_path = script_path.parent.parent

if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

env_path = root_path / ".env"
load_dotenv(dotenv_path=env_path)

from src.config import load_config
from src.retrieval.searcher import FaissSearcher
from src.evaluation.evaluator_msrvtt import (
    load_manifest_segment_to_video,
    load_queries_jsonl,
)
from src.evaluation.metrics import compute_metrics
from src.llm.ambiguity import score_query_ambiguity
from src.llm.query_rewriter import rewrite_query_with_cache
from src.llm.reranker import rerank_candidate_with_cache
from src.llm.candidate_semantics import get_candidate_semantics_with_cache
from src.utils.research_log import append_research_log
from src.utils.stage_status import announce_stage


def _model_suffix(model_name: str, pretrained: str) -> str:
    return f"{model_name}_{pretrained}".replace("/", "_")


def load_manifest_rows(manifest_jsonl: Path) -> dict:
    rows = {}
    with open(manifest_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                rows[row["segment_id"]] = row
    return rows


def minmax_norm(vals):
    if not vals:
        return []
    vmin = min(vals)
    vmax = max(vals)
    if abs(vmax - vmin) < 1e-12:
        return [0.5 for _ in vals]
    return [(v - vmin) / (vmax - vmin) for v in vals]


def main():
    announce_stage(
        "stage1",
        note="Run selective rewrite plus candidate rerank inside the system-optimization stage.",
        log_step="stage_announcement::run_rerank_eval",
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=str, default="msrvtt_fixed_1kA.jsonl")
    parser.add_argument("--queries", type=str, default="msrvtt_1kA_test_queries.jsonl")
    parser.add_argument("--pooling", type=str, default="mean", choices=["mean", "max"])
    parser.add_argument("--topk", type=int, default=200)

    parser.add_argument(
        "--rewrite_mode",
        type=str,
        default="rewrite_selective",
        choices=["baseline", "rewrite_all", "rewrite_selective"],
    )
    parser.add_argument("--ambiguity_threshold", type=float, default=0.2)

    parser.add_argument("--rerank_topn", type=int, default=10, choices=[5, 10, 20])
    parser.add_argument("--alpha", type=float, default=0.8)
    parser.add_argument("--rerank_only_if_rewritten", action="store_true")

    parser.add_argument("--max_queries", type=int, default=0)
    parser.add_argument("--model", type=str, default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip())
    parser.add_argument("--model_name", type=str, default="ViT-H-14")
    parser.add_argument("--pretrained", type=str, default="laion2b_s32b_b79k")

    args = parser.parse_args()

    print(f"[run_rerank_eval] using model: {args.model}")

    cfg = load_config()

    manifest_path = cfg.paths.manifests_dir / args.manifest
    queries_path = cfg.paths.data_dir / "annotations" / "msrvtt" / args.queries
    index_dir = (
        cfg.paths.data_dir
        / "indexes"
        / args.manifest.replace(".jsonl", "")
        / args.pooling
        / _model_suffix(args.model_name, args.pretrained)
        / "flat_ip"
    )

    if not manifest_path.exists():
        raise RuntimeError(f"Missing manifest: {manifest_path}")
    if not queries_path.exists():
        raise RuntimeError(f"Missing queries: {queries_path}")
    if not (index_dir / "index.faiss").exists():
        raise RuntimeError(f"Missing index: {index_dir / 'index.faiss'}")

    queries = load_queries_jsonl(str(queries_path))
    if args.max_queries > 0:
        queries = queries[:args.max_queries]

    seg2vid = load_manifest_segment_to_video(str(manifest_path))
    segid2row = load_manifest_rows(manifest_path)
    searcher = FaissSearcher(str(index_dir), model_name=args.model_name, pretrained=args.pretrained)
    from src.llm.client import OpenAIClient

    client = OpenAIClient(model=args.model)

    out_dir = cfg.paths.project_root / "outputs" / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)

    rewrite_cache_dir = cfg.paths.data_dir / "cache" / "rewrites"
    rerank_cache_dir = cfg.paths.data_dir / "cache" / "rerank"
    candidate_sem_cache_dir = cfg.paths.data_dir / "cache" / "candidate_semantics"
    tmp_frame_dir = cfg.paths.project_root / "outputs" / "tmp" / "rerank_frames"

    rewrite_cache_dir.mkdir(parents=True, exist_ok=True)
    rerank_cache_dir.mkdir(parents=True, exist_ok=True)
    candidate_sem_cache_dir.mkdir(parents=True, exist_ok=True)
    tmp_frame_dir.mkdir(parents=True, exist_ok=True)

    suffix = f"{args.rewrite_mode}_{args.pooling}_topk{args.topk}_rerank{args.rerank_topn}_alpha{args.alpha}"
    if args.rewrite_mode == "rewrite_selective":
        suffix += f"_thr{args.ambiguity_threshold}"

    log_path = out_dir / f"week7_{suffix}.jsonl"
    summary_path = out_dir / f"week7_{suffix}_summary.json"

    ranks = []

    rewrite_count = 0
    rewrite_cache_hits = 0
    rerank_cache_hits = 0
    candidate_sem_cache_hits = 0

    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0

    total_search_time = 0.0
    total_rerank_time = 0.0
    total_candidate_sem_time = 0.0

    with open(log_path, "w", encoding="utf-8") as fout:
        for i, q in enumerate(queries, start=1):
            original_query = q["query"]
            gt_vid = q["gt_video_id"]

            # ---- rewrite stage ----
            ambiguity = score_query_ambiguity(original_query, threshold=args.ambiguity_threshold)

            if args.rewrite_mode == "baseline":
                rewrite_info = {
                    "original_query": original_query,
                    "rewritten_query": original_query,
                    "used_rewrite": False,
                    "cache_hit": False,
                    "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                    "ambiguity": {
                        "score": ambiguity.score,
                        "trigger": ambiguity.trigger,
                        "reasons": ambiguity.reasons,
                        "token_count": ambiguity.token_count,
                        "query": ambiguity.query,
                    },
                }
                query_for_search = original_query

            elif args.rewrite_mode == "rewrite_all":
                rewrite_info = rewrite_query_with_cache(
                    query=original_query,
                    ambiguity=ambiguity,
                    client=client,
                    cache_dir=rewrite_cache_dir,
                    force_rewrite=True,
                )
                query_for_search = rewrite_info["rewritten_query"]

            else:
                rewrite_info = rewrite_query_with_cache(
                    query=original_query,
                    ambiguity=ambiguity,
                    client=client,
                    cache_dir=rewrite_cache_dir,
                    force_rewrite=False,
                )
                query_for_search = rewrite_info["rewritten_query"]

            if rewrite_info["used_rewrite"]:
                rewrite_count += 1
            if rewrite_info["cache_hit"]:
                rewrite_cache_hits += 1

            total_input_tokens += rewrite_info["usage"]["input_tokens"]
            total_output_tokens += rewrite_info["usage"]["output_tokens"]
            total_tokens += rewrite_info["usage"]["total_tokens"]

            # ---- retrieval stage ----
            ts = time.time()
            seg_results = searcher.search(query_for_search, topk=args.topk)
            total_search_time += (time.time() - ts)

            # ---- segment -> video aggregation (keep best segment) ----
            vid2best = {}
            for seg_id, score in seg_results:
                vid = seg2vid.get(seg_id)
                if vid is None:
                    continue
                prev = vid2best.get(vid)
                if prev is None or score > prev["retrieval_score"]:
                    row = segid2row[seg_id]
                    vid2best[vid] = {
                        "video_id": vid,
                        "segment_id": seg_id,
                        "retrieval_score": float(score),
                        "start_sec": float(row["start_sec"]),
                        "end_sec": float(row["end_sec"]),
                        "video_path": row["video_path"],
                    }

            ranked = sorted(
                vid2best.values(),
                key=lambda x: x["retrieval_score"],
                reverse=True
            )

            # retrieval rank
            for rank_idx, cand in enumerate(ranked, start=1):
                cand["rank"] = rank_idx

            should_rerank = not args.rerank_only_if_rewritten or rewrite_info["used_rewrite"]

            # ---- rerank top-N only ----
            top_candidates = ranked[:args.rerank_topn]
            rerank_start = time.time()
            reranked = []

            if should_rerank:
                for cand in top_candidates:
                    sem_start = time.time()
                    sem = get_candidate_semantics_with_cache(
                        candidate=cand,
                        client=client,
                        cache_dir=candidate_sem_cache_dir,
                        tmp_frame_dir=tmp_frame_dir,
                    )
                    total_candidate_sem_time += (time.time() - sem_start)

                    cand["semantic_summary"] = sem["summary"]
                    cand["semantic_tags"] = sem["tags"]

                    if sem["cache_hit"]:
                        candidate_sem_cache_hits += 1

                    total_input_tokens += sem["usage"]["input_tokens"]
                    total_output_tokens += sem["usage"]["output_tokens"]
                    total_tokens += sem["usage"]["total_tokens"]

                    rr = rerank_candidate_with_cache(
                        query=original_query,
                        rewritten_query=query_for_search,
                        candidate=cand,
                        client=client,
                        cache_dir=rerank_cache_dir,
                    )
                    reranked.append(rr)

                    if rr["cache_hit"]:
                        rerank_cache_hits += 1

                    total_input_tokens += rr["usage"]["input_tokens"]
                    total_output_tokens += rr["usage"]["output_tokens"]
                    total_tokens += rr["usage"]["total_tokens"]
            else:
                for cand in top_candidates:
                    reranked.append(
                        {
                            "video_id": cand["video_id"],
                            "segment_id": cand["segment_id"],
                            "llm_score": 50,
                            "reason": "rerank skipped because rewrite was not triggered",
                            "cache_hit": False,
                            "model": None,
                            "prompt_version": "skipped",
                            "usage": {
                                "input_tokens": 0,
                                "output_tokens": 0,
                                "total_tokens": 0,
                            },
                            "retrieval_rank": cand["rank"],
                            "retrieval_score": cand["retrieval_score"],
                            "start_sec": cand["start_sec"],
                            "end_sec": cand["end_sec"],
                            "semantic_summary": "",
                            "semantic_tags": [],
                        }
                    )

            total_rerank_time += (time.time() - rerank_start)

            # ---- fused rerank ----
            retrieval_scores = [x["retrieval_score"] for x in reranked]
            llm_scores = [x["llm_score"] for x in reranked]

            retrieval_norm = minmax_norm(retrieval_scores)
            llm_norm = minmax_norm(llm_scores)

            for idx in range(len(reranked)):
                reranked[idx]["retrieval_score_norm"] = retrieval_norm[idx]
                reranked[idx]["llm_score_norm"] = llm_norm[idx]
                reranked[idx]["final_score"] = args.alpha * retrieval_norm[idx] + (1 - args.alpha) * llm_norm[idx]

            reranked = sorted(reranked, key=lambda x: x["final_score"], reverse=True)

            reranked_video_ids = [x["video_id"] for x in reranked]
            remaining_video_ids = [x["video_id"] for x in ranked if x["video_id"] not in reranked_video_ids]
            final_video_order = reranked_video_ids + remaining_video_ids

            # ---- final GT rank ----
            rank = len(final_video_order) + 1
            for r_idx, vid in enumerate(final_video_order, start=1):
                if vid == gt_vid:
                    rank = r_idx
                    break
            ranks.append(rank)

            row = {
                "qid": i - 1,
                "gt_video_id": gt_vid,
                "original_query": original_query,
                "query_for_search": query_for_search,
                "rewrite_mode": args.rewrite_mode,
                "rerank_topn": args.rerank_topn,
                "alpha": args.alpha,
                "rank": rank,
                "rewrite": rewrite_info,
                "reranked_top_candidates": reranked,
            }
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")

            if i % 20 == 0:
                print(f"[{i}/{len(queries)}] done")

    metrics = compute_metrics(ranks)

    summary = {
        "mode": "rewrite_rerank_fused_semantic",
        "rewrite_mode": args.rewrite_mode,
        "manifest": args.manifest,
        "queries": args.queries,
        "pooling": args.pooling,
        "model_name": args.model_name,
        "pretrained": args.pretrained,
        "topk_segments": args.topk,
        "rerank_topn": args.rerank_topn,
        "ambiguity_threshold": args.ambiguity_threshold,
        "alpha": args.alpha,
        "rerank_only_if_rewritten": args.rerank_only_if_rewritten,
        "N": len(ranks),
        "metrics": {
            "R@1": metrics.r1,
            "R@5": metrics.r5,
            "R@10": metrics.r10,
            "MedR": metrics.medr,
            "MnR": metrics.mnr,
        },
        "rewrite_count": rewrite_count,
        "rewrite_rate": round(rewrite_count / max(1, len(ranks)), 4),
        "rewrite_cache_hit_count": rewrite_cache_hits,
        "candidate_semantics_cache_hit_count": candidate_sem_cache_hits,
        "rerank_cache_hit_count": rerank_cache_hits,
        "token_usage": {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": total_tokens,
        },
        "latency": {
            "avg_search_ms": round((total_search_time / max(1, len(ranks))) * 1000, 3),
            "avg_candidate_semantics_ms": round((total_candidate_sem_time / max(1, len(ranks))) * 1000, 3),
            "avg_rerank_ms": round((total_rerank_time / max(1, len(ranks))) * 1000, 3),
            "avg_total_ms": round(((total_search_time + total_candidate_sem_time + total_rerank_time) / max(1, len(ranks))) * 1000, 3),
        },
        "log_path": str(log_path),
    }

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    append_research_log(
        step=f"run_rerank_eval::{args.rewrite_mode}",
        summary=(
            f"Evaluated rewrite+rereank mode on {args.queries} with selective rerank={args.rerank_only_if_rewritten}. "
            f"Metrics: R@1={metrics.r1}, R@5={metrics.r5}, R@10={metrics.r10}."
        ),
        decisions=[
            f"Manifest: {args.manifest}",
            f"Queries: {args.queries}",
            f"Rerank only if rewritten: {args.rerank_only_if_rewritten}",
        ],
        citations=[
            "sentence_component_cvprw2024",
            "fine_grained_accv2024",
        ],
        artifacts=[
            str(log_path),
            str(summary_path),
        ],
    )

    print(f"[OK] summary saved to: {summary_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
