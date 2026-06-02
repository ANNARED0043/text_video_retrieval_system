from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.evaluation.evaluator_msrvtt import load_manifest_segment_to_video, load_queries_jsonl
from src.learning.teacher_supervision import TeacherSupervisionEntry, TeacherTarget, write_teacher_supervision
from src.llm.semantic_memory import derive_constraint_tags
from src.retrieval.searcher import FaissSearcher


def _model_suffix(model_name: str, pretrained: str) -> str:
    return f"{model_name}_{pretrained}".replace("/", "_")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build clean bootstrap teacher supervision from current ViT-H retrieval.")
    parser.add_argument("--manifest", type=str, default="msrvtt_fixed_1kA.jsonl")
    parser.add_argument("--queries", type=str, default="msrvtt_1kA_test_queries.jsonl")
    parser.add_argument("--pooling", type=str, default="mean")
    parser.add_argument("--model_name", type=str, default="ViT-H-14")
    parser.add_argument("--pretrained", type=str, default="laion2b_s32b_b79k")
    parser.add_argument("--topk", type=int, default=20)
    parser.add_argument("--max_queries", type=int, default=200)
    parser.add_argument("--out", type=str, required=True)
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

    seg2vid = load_manifest_segment_to_video(str(manifest_path))
    queries = load_queries_jsonl(str(queries_path))
    if args.max_queries > 0:
        queries = queries[: args.max_queries]

    searcher = FaissSearcher(str(index_dir), model_name=args.model_name, pretrained=args.pretrained)
    entries: list[TeacherSupervisionEntry] = []

    for qid, row in enumerate(tqdm(queries, desc="Bootstrap teacher supervision", dynamic_ncols=True)):
        query = row["query"]
        gt_video_id = row["gt_video_id"]
        results = searcher.search(query, topk=args.topk)
        targets: list[TeacherTarget] = []
        seen: set[str] = set()
        for seg_id, score in results:
            vid = seg2vid.get(seg_id)
            if not vid or vid in seen:
                continue
            seen.add(vid)
            targets.append(TeacherTarget(video_id=vid, score=float(score)))

        hard_negatives = [target.video_id for target in targets if target.video_id != gt_video_id][: min(10, len(targets))]
        terms = [token.strip(" ,.!?;:'\"()[]{}").lower() for token in query.split() if len(token.strip()) >= 4][:10]
        entries.append(
            TeacherSupervisionEntry(
                qid=qid,
                query=query,
                gt_video_id=gt_video_id,
                source="bootstrap_vith_retrieval",
                similarity_targets=targets,
                listwise_targets=targets,
                hard_negatives=hard_negatives,
                frame_relevance=[1.0 if gt_video_id else 0.0],
                prototype_terms=terms,
                constraint_tags=derive_constraint_tags(query),
                metadata={"model_name": args.model_name, "pretrained": args.pretrained},
            )
        )

    write_teacher_supervision(args.out, entries)
    print(f"[OK] wrote bootstrap teacher supervision: {args.out} ({len(entries)} rows)")


if __name__ == "__main__":
    main()
