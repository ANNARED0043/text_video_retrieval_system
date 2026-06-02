from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.evaluation.evaluator_msrvtt import load_queries_jsonl
from src.features.viclip_encoder import encode_text_viclip, encode_video_viclip, load_viclip
from src.learning.teacher_supervision import (
    TeacherSupervisionEntry,
    TeacherTarget,
    load_teacher_supervision,
    write_teacher_supervision,
)
from src.llm.semantic_memory import derive_constraint_tags, extract_query_tokens, extract_structured_prototypes
from src.retrieval.searcher import FaissSearcher


def _read_manifest_rows(path: Path) -> tuple[dict[str, dict], dict[str, str]]:
    video_rows: dict[str, dict] = {}
    seg2vid: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            video_rows[row["video_id"]] = row
            seg2vid[row["segment_id"]] = row["video_id"]
    return video_rows, seg2vid


def _cache_path(cache_dir: Path, video_id: str) -> Path:
    return cache_dir / f"{video_id}.npy"


def _load_or_compute_video_feature(bundle, video_id: str, video_path: str, cache_dir: Path) -> np.ndarray:
    cache_path = _cache_path(cache_dir, video_id)
    if cache_path.exists():
        try:
            return np.load(cache_path).astype(np.float32)
        except Exception:
            try:
                cache_path.unlink(missing_ok=True)
            except Exception:
                pass
    feat = encode_video_viclip(bundle, video_path)
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        np.save(cache_path, feat.astype(np.float32))
    except Exception:
        pass
    return feat


def _teacher_uncertainty_from_targets(targets: list[TeacherTarget]) -> dict[str, float]:
    if not targets:
        return {
            "teacher_top1_top2_gap": 0.0,
            "teacher_entropy": 0.0,
            "uncertainty_score": 0.5,
        }
    scores = np.asarray([float(target.score) for target in targets[:10]], dtype=np.float32)
    if scores.size == 0:
        return {
            "teacher_top1_top2_gap": 0.0,
            "teacher_entropy": 0.0,
            "uncertainty_score": 0.5,
        }
    top1 = float(scores[0])
    top2 = float(scores[1]) if scores.size > 1 else float(scores[0])
    gap = max(0.0, top1 - top2)
    shifted = scores - float(scores.max())
    probs = np.exp(shifted)
    probs = probs / max(float(probs.sum()), 1e-8)
    entropy = float(-(probs * np.log(probs + 1e-8)).sum())
    entropy_norm = entropy / max(float(np.log(len(probs))) if len(probs) > 1 else 1.0, 1e-8)
    gap_confidence = float(np.clip(gap / max(abs(top1), 1e-6), 0.0, 1.0))
    uncertainty = float(np.clip(0.5 * (1.0 - gap_confidence) + 0.5 * entropy_norm, 0.0, 1.0))
    return {
        "teacher_top1_top2_gap": gap,
        "teacher_entropy": entropy_norm,
        "uncertainty_score": uncertainty,
    }


def _gt_rank_in_targets(targets: list[TeacherTarget], gt_video_id: str) -> int | None:
    for rank, target in enumerate(targets, start=1):
        if target.video_id == gt_video_id:
            return rank
    return None


def _finalize_teacher_targets(
    full_targets: list[TeacherTarget],
    gt_video_id: str,
    teacher_topk: int,
    force_keep_gt: bool,
) -> tuple[list[TeacherTarget], dict[str, int | bool | None]]:
    ranked_full = sorted(full_targets, key=lambda item: item.score, reverse=True)
    gt_rank_full = _gt_rank_in_targets(ranked_full, gt_video_id)
    selected = ranked_full[:teacher_topk]
    gt_rank_saved = _gt_rank_in_targets(selected, gt_video_id)
    gt_forced = False

    if force_keep_gt and gt_rank_full is not None and gt_rank_saved is None:
        gt_target = next((target for target in ranked_full if target.video_id == gt_video_id), None)
        if gt_target is not None:
            if selected:
                selected = selected[:-1] + [gt_target]
            else:
                selected = [gt_target]
            selected = sorted(selected, key=lambda item: item.score, reverse=True)
            gt_rank_saved = _gt_rank_in_targets(selected, gt_video_id)
            gt_forced = True

    return selected, {
        "gt_rank_full": gt_rank_full,
        "gt_rank_saved": gt_rank_saved,
        "gt_forced_into_teacher": gt_forced,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build true ViCLIP teacher supervision on top student-retrieved candidates.")
    parser.add_argument("--manifest", type=str, default="msrvtt_fixed.jsonl")
    parser.add_argument("--queries", type=str, default="msrvtt_train_9k_queries.jsonl")
    parser.add_argument("--pooling", type=str, default="mean")
    parser.add_argument("--student_model_name", type=str, default="ViT-H-14")
    parser.add_argument("--student_pretrained", type=str, default="laion2b_s32b_b79k")
    parser.add_argument("--student_topk", type=int, default=50)
    parser.add_argument("--teacher_topk", type=int, default=20)
    parser.add_argument("--force_keep_gt_in_teacher", action="store_true")
    parser.add_argument("--max_queries", type=int, default=200)
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--resume_from", type=str, default="")
    parser.add_argument("--video_cache_dir", type=str, default="data/cache/viclip/video_features")
    parser.add_argument("--checkpoint_every", type=int, default=250)
    args = parser.parse_args()

    cfg = load_config()
    manifest_path = cfg.paths.manifests_dir / args.manifest
    queries_path = cfg.paths.data_dir / "annotations" / "msrvtt" / args.queries
    index_dir = (
        cfg.paths.data_dir
        / "indexes"
        / args.manifest.replace(".jsonl", "")
        / args.pooling
        / f"{args.student_model_name}_{args.student_pretrained}".replace("/", "_")
        / "flat_ip"
    )

    queries = load_queries_jsonl(str(queries_path))
    if args.max_queries > 0:
        queries = queries[: args.max_queries]
    resume_path = Path(args.resume_from) if args.resume_from.strip() else Path(args.out)

    video_rows, seg2vid = _read_manifest_rows(manifest_path)
    searcher = FaissSearcher(
        str(index_dir),
        model_name=args.student_model_name,
        pretrained=args.student_pretrained,
        device="cpu",
    )
    viclip = load_viclip(device="cpu")
    cache_dir = PROJECT_ROOT / args.video_cache_dir

    existing_entries = load_teacher_supervision(resume_path) if resume_path.exists() else {}
    entries: list[TeacherSupervisionEntry] = list(existing_entries.values())
    completed_qids = {str(entry.qid) for entry in entries}
    tmp_out = Path(f"{args.out}.tmp")
    start_time = time.time()
    cache_hits = 0
    cache_misses = 0
    gt_in_full_count = 0
    gt_in_saved_count = 0
    gt_top1_count = 0
    gt_forced_count = 0
    total_queries = len(queries)
    progress = tqdm(queries, desc="Build ViCLIP teacher supervision", dynamic_ncols=True)
    for qid, row in enumerate(progress):
        row_qid = str(row.get("qid", qid))
        if row_qid in completed_qids:
            progress.set_postfix(rows=len(entries), cache_hit=cache_hits, cache_miss=cache_misses, resumed=len(completed_qids))
            continue

        query = row["query"]
        gt_video_id = row["gt_video_id"]
        seg_results = searcher.search(query, topk=args.student_topk)
        candidate_video_ids: list[str] = []
        seen: set[str] = set()
        for seg_id, _score in seg_results:
            video_id = seg2vid.get(seg_id)
            if not video_id or video_id in seen:
                continue
            seen.add(video_id)
            candidate_video_ids.append(video_id)

        if gt_video_id not in seen and gt_video_id in video_rows:
            candidate_video_ids.append(gt_video_id)

        if not candidate_video_ids:
            continue

        text_feat = encode_text_viclip(viclip, query)
        teacher_targets: list[TeacherTarget] = []
        for video_id in candidate_video_ids:
            video_row = video_rows.get(video_id)
            if video_row is None:
                continue
            cache_path = _cache_path(cache_dir, video_id)
            if cache_path.exists():
                cache_hits += 1
            else:
                cache_misses += 1
            vid_feat = _load_or_compute_video_feature(viclip, video_id, video_row["video_path"], cache_dir)
            score = float(np.dot(text_feat, vid_feat))
            teacher_targets.append(TeacherTarget(video_id=video_id, score=score))

        teacher_targets, coverage_meta = _finalize_teacher_targets(
            full_targets=teacher_targets,
            gt_video_id=gt_video_id,
            teacher_topk=args.teacher_topk,
            force_keep_gt=args.force_keep_gt_in_teacher,
        )
        if not teacher_targets:
            continue
        uncertainty_stats = _teacher_uncertainty_from_targets(teacher_targets)
        if coverage_meta["gt_rank_full"] is not None:
            gt_in_full_count += 1
        if coverage_meta["gt_rank_saved"] is not None:
            gt_in_saved_count += 1
            if int(coverage_meta["gt_rank_saved"]) == 1:
                gt_top1_count += 1
        if coverage_meta["gt_forced_into_teacher"]:
            gt_forced_count += 1

        hard_negatives = [item.video_id for item in teacher_targets if item.video_id != gt_video_id][:10]
        prototype_terms = extract_query_tokens(query)[:10]
        structured_prototypes = extract_structured_prototypes(query)
        entries.append(
            TeacherSupervisionEntry(
                qid=row.get("qid", qid),
                query=query,
                gt_video_id=gt_video_id,
                source="viclip_rerank_teacher",
                similarity_targets=teacher_targets,
                listwise_targets=teacher_targets,
                hard_negatives=hard_negatives,
                frame_relevance=[1.0 if gt_video_id else 0.0],
                prototype_terms=prototype_terms,
                structured_prototypes=structured_prototypes,
                constraint_tags=derive_constraint_tags(query),
                metadata={
                    "teacher_model": "OpenGVLab/ViCLIP-L-14-hf",
                    "student_candidate_topk": args.student_topk,
                    "teacher_topk": args.teacher_topk,
                    **coverage_meta,
                    **uncertainty_stats,
                },
            )
        )
        completed_qids.add(row_qid)
        processed = qid + 1
        progress.set_postfix(
            rows=len(entries),
            cache_hit=cache_hits,
            cache_miss=cache_misses,
            resumed=len(existing_entries),
        )
        if args.checkpoint_every > 0 and processed % args.checkpoint_every == 0:
            write_teacher_supervision(str(tmp_out), entries)
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0.0
            remaining = total_queries - processed
            eta_sec = remaining / rate if rate > 0 else 0.0
            print(
                f"[progress] {processed}/{total_queries} "
                f"({processed / total_queries:.2%}) "
                f"rows={len(entries)} rate={rate:.2f} q/s "
                f"eta_min={eta_sec / 60:.1f} "
                f"cache_hit={cache_hits} cache_miss={cache_misses} "
                f"resumed={len(existing_entries)}",
                flush=True,
            )

    entries.sort(key=lambda item: int(item.qid) if str(item.qid).isdigit() else str(item.qid))
    write_teacher_supervision(args.out, entries)
    if tmp_out.exists():
        tmp_out.unlink()
    if total_queries > 0:
        print(
            json.dumps(
                {
                    "teacher_coverage": {
                        "queries": total_queries,
                        "gt_in_full_targets": gt_in_full_count,
                        "gt_in_saved_targets": gt_in_saved_count,
                        "teacher_top1_is_gt": gt_top1_count,
                        "gt_forced_into_teacher": gt_forced_count,
                        "gt_in_full_rate": round(gt_in_full_count / total_queries, 4),
                        "gt_in_saved_rate": round(gt_in_saved_count / total_queries, 4),
                        "teacher_top1_is_gt_rate": round(gt_top1_count / total_queries, 4),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    print(f"[OK] wrote ViCLIP teacher supervision: {args.out} ({len(entries)} rows)")


if __name__ == "__main__":
    main()
