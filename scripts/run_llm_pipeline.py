"""Run baseline or rewrite-enhanced retrieval pipelines on MSR-VTT."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from tqdm import tqdm

script_path = Path(__file__).resolve()
root_path = script_path.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))
load_dotenv(dotenv_path=root_path / ".env")

from src.config import load_config
from src.evaluation.evaluator_msrvtt import load_manifest_segment_to_video, load_queries_jsonl
from src.evaluation.metrics import compute_metrics
from src.llm.ambiguity import score_query_ambiguity
from src.llm.query_rewriter import rewrite_query_with_cache
from src.retrieval.searcher import FaissSearcher
from src.utils.research_log import append_research_log
from src.utils.stage_status import announce_stage



def _model_suffix(model_name: str, pretrained: str) -> str:
    return f"{model_name}_{pretrained}".replace("/", "_")


def _segment_results_to_video_scores(
    seg_results: list[tuple[str, float]],
    seg2vid: dict[str, str],
) -> dict[str, float]:
    vid2score: dict[str, float] = {}
    for seg_id, score in seg_results:
        vid = seg2vid.get(seg_id)
        if vid is None:
            continue
        prev = vid2score.get(vid)
        score = float(score)
        if prev is None or score > prev:
            vid2score[vid] = score
    return vid2score


def _minmax_map(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    raw = list(values.values())
    low = min(raw)
    high = max(raw)
    if abs(high - low) < 1e-12:
        return {key: 0.5 for key in values}
    return {key: (val - low) / (high - low) for key, val in values.items()}


def _hybrid_video_ranking(
    baseline_results: list[tuple[str, float]],
    rewrite_results: list[tuple[str, float]],
    seg2vid: dict[str, str],
    alpha: float,
) -> list[tuple[str, float]]:
    base_vid2score = _segment_results_to_video_scores(baseline_results, seg2vid)
    rewrite_vid2score = _segment_results_to_video_scores(rewrite_results, seg2vid)
    base_norm = _minmax_map(base_vid2score)
    rewrite_norm = _minmax_map(rewrite_vid2score)
    all_vids = set(base_norm) | set(rewrite_norm)
    fused = {}
    for vid in all_vids:
        fused[vid] = alpha * base_norm.get(vid, 0.0) + (1.0 - alpha) * rewrite_norm.get(vid, 0.0)
    return sorted(fused.items(), key=lambda item: item[1], reverse=True)



def main() -> None:
    announce_stage(
        "stage1",
        note="Run baseline retrieval plus selective query rewrite while preserving the locked 1kA reference.",
        log_step="stage_announcement::run_llm_pipeline",
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=str, default="msrvtt_fixed_1kA.jsonl")
    parser.add_argument("--queries", type=str, default="msrvtt_1kA_test_queries.jsonl")
    parser.add_argument("--pooling", type=str, default="mean", choices=["mean", "max"])
    parser.add_argument("--topk", type=int, default=200)
    parser.add_argument(
        "--mode",
        type=str,
        default="baseline",
        choices=[
            "baseline",
            "rewrite_all",
            "rewrite_selective",
            "rewrite_selective_riskaware",
            "rewrite_selective_hybrid",
        ],
    )
    parser.add_argument("--max_queries", type=int, default=0)
    parser.add_argument("--ambiguity_threshold", type=float, default=0.2)
    parser.add_argument("--riskaware_light_alpha", type=float, default=0.68)
    parser.add_argument("--riskaware_strong_alpha", type=float, default=0.55)
    parser.add_argument("--hybrid_baseline_alpha", type=float, default=0.75)
    parser.add_argument("--model", type=str, default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
    parser.add_argument("--model_name", type=str, default="ViT-B-32")
    parser.add_argument("--pretrained", type=str, default="openai")
    args = parser.parse_args()

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
        queries = queries[: args.max_queries]

    seg2vid = load_manifest_segment_to_video(str(manifest_path))
    searcher = FaissSearcher(
        str(index_dir),
        model_name=args.model_name,
        pretrained=args.pretrained,
    )
    client = None
    if args.mode != "baseline":
        from src.llm.client import OpenAIClient

        client = OpenAIClient(model=args.model)

    out_dir = cfg.paths.project_root / "outputs" / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = cfg.paths.data_dir / "cache" / "rewrites"
    cache_dir.mkdir(parents=True, exist_ok=True)

    suffix_bits = [args.mode, args.pooling, f"topk{args.topk}", f"thr{args.ambiguity_threshold}"]
    if args.mode == "rewrite_selective_riskaware":
        suffix_bits.append(f"la{args.riskaware_light_alpha}")
        suffix_bits.append(f"sa{args.riskaware_strong_alpha}")
    if args.mode == "rewrite_selective_hybrid":
        suffix_bits.append(f"ba{args.hybrid_baseline_alpha}")
    suffix = "_".join(suffix_bits)
    log_path = out_dir / f"final_{suffix}.jsonl"
    summary_path = out_dir / f"final_{suffix}_summary.json"

    ranks = []
    rewrite_count = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0
    total_ms = 0.0

    with open(log_path, "w", encoding="utf-8") as fout:
        pbar = tqdm(queries, desc=f"LLM Pipeline ({args.mode})", dynamic_ncols=True, file=sys.stdout)
        for idx, q in enumerate(pbar):
            original_query = q["query"]
            gt_vid = q["gt_video_id"]
            probe_scores = None
            if client is not None:
                probe = searcher.search(original_query, topk=min(args.topk, 10))
                probe_scores = [score for _, score in probe]
            ambiguity = score_query_ambiguity(
                original_query,
                threshold=args.ambiguity_threshold,
                retrieval_scores=probe_scores,
            )

            if args.mode == "baseline":
                rewrite_info = {
                    "original_query": original_query,
                    "rewritten_query": original_query,
                    "used_rewrite": False,
                    "cache_hit": False,
                    "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                    "ambiguity": ambiguity.__dict__,
                }
                query_for_search = original_query
            else:
                force = args.mode == "rewrite_all"
                riskaware = args.mode == "rewrite_selective_riskaware"
                rewrite_info = rewrite_query_with_cache(
                    query=original_query,
                    ambiguity=ambiguity,
                    client=client,
                    cache_dir=cache_dir,
                    force_rewrite=force,
                    riskaware=riskaware,
                )
                query_for_search = rewrite_info["rewritten_query"]

            if rewrite_info["used_rewrite"]:
                rewrite_count += 1
            total_input_tokens += rewrite_info["usage"]["input_tokens"]
            total_output_tokens += rewrite_info["usage"]["output_tokens"]
            total_tokens += rewrite_info["usage"]["total_tokens"]

            ts = time.time()
            baseline_seg_results = searcher.search(original_query, topk=args.topk)
            if args.mode == "rewrite_selective_hybrid" and rewrite_info["used_rewrite"]:
                rewrite_seg_results = searcher.search(query_for_search, topk=args.topk)
            elif args.mode == "baseline":
                rewrite_seg_results = baseline_seg_results
            else:
                rewrite_seg_results = searcher.search(query_for_search, topk=args.topk)
            total_ms += (time.time() - ts) * 1000

            if args.mode == "rewrite_selective_hybrid" and rewrite_info["used_rewrite"]:
                ambiguity_score = rewrite_info["ambiguity"]["score"]
                alpha = args.hybrid_baseline_alpha if ambiguity_score < 0.4 else min(0.9, args.hybrid_baseline_alpha + 0.1)
                ranked = _hybrid_video_ranking(
                    baseline_results=baseline_seg_results,
                    rewrite_results=rewrite_seg_results,
                    seg2vid=seg2vid,
                    alpha=alpha,
                )
            else:
                vid2score = _segment_results_to_video_scores(rewrite_seg_results, seg2vid)
                ranked = sorted(vid2score.items(), key=lambda item: item[1], reverse=True)

            rank = len(ranked) + 1
            for rank_idx, (vid, _) in enumerate(ranked, start=1):
                if vid == gt_vid:
                    rank = rank_idx
                    break
            ranks.append(rank)

            fout.write(
                json.dumps(
                    {
                        "qid": idx,
                        "gt_video_id": gt_vid,
                        "original_query": original_query,
                        "query_for_search": query_for_search,
                        "rank": rank,
                        "mode": args.mode,
                        "rewrite": rewrite_info,
                        "used_hybrid": args.mode == "rewrite_selective_hybrid" and rewrite_info["used_rewrite"],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            if (idx + 1) % 25 == 0:
                pbar.set_postfix({
                    "avg_ms": f"{total_ms / (idx + 1):.1f}",
                    "rewrite_rate": f"{rewrite_count / (idx + 1):.2f}",
                })

    metrics = compute_metrics(ranks)
    summary = {
        "schema_version": "retrieval_summary_v1",
        "task": "text_to_video_retrieval",
        "mode": args.mode,
        "dataset": "MSR-VTT",
        "protocol": "1kA",
        "manifest": args.manifest,
        "queries": args.queries,
        "pooling": args.pooling,
        "topk_segments": args.topk,
        "queries_planned": len(ranks),
        "queries_evaluated": len(ranks),
        "R@1": metrics.r1,
        "R@5": metrics.r5,
        "R@10": metrics.r10,
        "MedR": metrics.medr,
        "MnR": metrics.mnr,
        "avg_search_ms": round(total_ms / max(1, len(ranks)), 3),
        "rewrite_rate": round(rewrite_count / max(1, len(ranks)), 6),
        "tokens": {
            "input": total_input_tokens,
            "output": total_output_tokens,
            "total": total_tokens,
        },
        "model": {
            "retriever_text_encoder": f"open_clip:{args.model_name}/{args.pretrained}",
            "llm": None if args.mode == "baseline" else args.model,
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    append_research_log(
        step=f"run_llm_pipeline::{args.mode}",
        summary=(
            f"Evaluated Stage 1 system optimization mode={args.mode} on {args.queries} "
            f"with R@1={metrics.r1}, R@5={metrics.r5}, R@10={metrics.r10}."
        ),
        decisions=[
            f"Manifest: {args.manifest}",
            f"Queries: {args.queries}",
            f"Hybrid baseline alpha: {args.hybrid_baseline_alpha}",
        ],
        citations=[
            "sentence_component_cvprw2024",
            "fine_grained_accv2024",
        ],
        artifacts=[
            str(log_path),
            str(summary_path),
        ],
        extra={
            "mode": args.mode,
            "metrics": {
                "R@1": metrics.r1,
                "R@5": metrics.r5,
                "R@10": metrics.r10,
            },
        },
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

