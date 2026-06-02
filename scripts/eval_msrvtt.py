from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.evaluation.evaluator_msrvtt import eval_msrvtt_video_retrieval
from src.retrieval.searcher import FaissSearcher


def count_nonempty_lines(path: Path) -> int:
    n = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=str, default="msrvtt_fixed_1kA.jsonl")
    parser.add_argument("--queries", type=str, default="msrvtt_1kA_test_queries.jsonl")
    parser.add_argument("--pooling", type=str, default="mean", choices=["mean", "max"])
    parser.add_argument("--model_name", type=str, default="ViT-B-32")
    parser.add_argument("--pretrained", type=str, default="openai")
    parser.add_argument("--topk", type=int, default=200)
    parser.add_argument("--aggregation", type=str, default="max", choices=["max"])
    parser.add_argument("--max_queries", type=int, default=0)
    parser.add_argument("--out", type=str, default="")
    parser.add_argument("--estimate", action="store_true")
    args = parser.parse_args()

    cfg = load_config()
    manifest_path = cfg.paths.manifests_dir / args.manifest
    queries_path = cfg.paths.data_dir / "annotations" / "msrvtt" / args.queries
    model_suffix = f"{args.model_name}_{args.pretrained}".replace("/", "_")
    index_dir = (
        cfg.paths.data_dir
        / "indexes"
        / args.manifest.replace(".jsonl", "")
        / args.pooling
        / model_suffix
        / "flat_ip"
    )

    print("[eval_msrvtt] manifest :", manifest_path)
    print("[eval_msrvtt] queries  :", queries_path)
    print("[eval_msrvtt] index_dir:", index_dir)

    if not manifest_path.exists():
        raise RuntimeError(f"Missing manifest: {manifest_path}")
    if not queries_path.exists():
        raise RuntimeError(f"Missing queries: {queries_path}")
    if not index_dir.exists():
        raise RuntimeError(f"Missing index dir: {index_dir}")

    total_q = count_nonempty_lines(queries_path)
    planned = total_q if args.max_queries <= 0 else min(total_q, args.max_queries)
    max_q = None if args.max_queries <= 0 else args.max_queries

    print(f"[eval_msrvtt] total queries in file = {total_q}")
    print(f"[eval_msrvtt] planned queries = {planned}")
    print("[eval_msrvtt] creating searcher ...")
    searcher = FaissSearcher(
        str(index_dir),
        model_name=args.model_name,
        pretrained=args.pretrained,
    )
    print("[eval_msrvtt] searcher ready")

    if args.estimate:
        warmup_n = min(20, planned)
        if warmup_n >= 5:
            print(f"[eval_msrvtt] estimating runtime using first {warmup_n} queries ...")
            t_est0 = time.time()
            eval_msrvtt_video_retrieval(
                searcher=searcher,
                queries_jsonl=str(queries_path),
                manifest_jsonl=str(manifest_path),
                topk_segments=min(args.topk, 50),
                max_queries=warmup_n,
                log_every=warmup_n,
            )
            dt = time.time() - t_est0
            per_q = dt / warmup_n
            print(f"[eval_msrvtt] rough estimate: ~{per_q:.3f}s/query => ~{(per_q * planned) / 60:.1f} min for N={planned}")

    t0 = time.time()
    metrics, _, latency = eval_msrvtt_video_retrieval(
        searcher=searcher,
        queries_jsonl=str(queries_path),
        manifest_jsonl=str(manifest_path),
        topk_segments=args.topk,
        max_queries=max_q,
        log_every=50,
    )
    elapsed = time.time() - t0

    out_dir = cfg.paths.project_root / "outputs" / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.out.strip():
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = cfg.paths.project_root / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        out_path = out_dir / (
            f"baseline_{args.model_name.replace('/', '_').lower()}_"
            f"{args.pooling}_topk{args.topk}_{args.aggregation}_N{planned}.json"
        )

    protocol_name = "custom"
    query_name = args.queries.lower()
    manifest_name = args.manifest.lower()
    if "1ka" in query_name or "1ka" in manifest_name:
        protocol_name = "1k-A"
    elif "safe_dev" in query_name:
        protocol_name = "train9k-safe-dev"
    elif "train" in query_name:
        protocol_name = "train9k"

    payload = {
        "dataset": "MSR-VTT",
        "protocol": protocol_name,
        "manifest": args.manifest,
        "queries": args.queries,
        "pooling": args.pooling,
        "model_name": args.model_name,
        "pretrained": args.pretrained,
        "index": "faiss_flat_ip",
        "aggregation": args.aggregation,
        "topk_segments": args.topk,
        "queries_planned": planned,
        "elapsed_s": round(elapsed, 2),
        "metrics": {
            "R@1": metrics.r1,
            "R@5": metrics.r5,
            "R@10": metrics.r10,
            "MedR": metrics.medr,
            "MnR": metrics.mnr,
            "N": metrics.n,
        },
        "latency": latency,
        "time": datetime.now().isoformat(timespec="seconds"),
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote metrics: {out_path}")
    print(json.dumps(payload["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    os.environ.setdefault("PYTHONPATH", str(PROJECT_ROOT))
    main()
