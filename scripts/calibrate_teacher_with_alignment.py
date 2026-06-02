from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.features.clip_encoder import encode_text, load_clip
from src.learning.teacher_supervision import (
    TeacherSupervisionEntry,
    TeacherTarget,
    load_teacher_supervision,
    write_teacher_supervision,
)
from src.llm.semantic_memory import extract_structured_prototypes
from src.utils.research_log import append_research_log


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _load_alignment_teacher(path_text: str) -> dict[str, dict[str, Any]]:
    if not path_text.strip():
        return {}
    rows = _read_jsonl(_resolve_path(path_text))
    return {str(row.get("video_id", "")): row for row in rows if row.get("video_id")}


def _load_multiview_features(path_text: str) -> dict[str, np.ndarray]:
    if not path_text.strip():
        return {}
    path = _resolve_path(path_text)
    if not path.exists():
        return {}
    payload = np.load(path, allow_pickle=True)
    video_ids = [str(item) for item in payload["video_ids"].tolist()]
    features = payload["features"].astype(np.float32)
    return {video_id: features[idx] for idx, video_id in enumerate(video_ids)}


def _normalize(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    raw = np.asarray(list(values.values()), dtype=np.float32)
    min_value = float(raw.min())
    max_value = float(raw.max())
    if max_value - min_value < 1e-8:
        return {key: 0.5 for key in values}
    return {
        key: float((value - min_value) / (max_value - min_value))
        for key, value in values.items()
    }


def _alignment_terms(payload: dict[str, Any]) -> dict[str, set[str]]:
    attrs = payload.get("visual_attributes", {}) if isinstance(payload, dict) else {}
    actions = {
        str(item.get("action", "")).lower()
        for item in payload.get("actions", [])
        if isinstance(item, dict) and item.get("action")
    }
    sequence = {
        str(item.get("action", "")).lower()
        for item in payload.get("action_sequence", [])
        if isinstance(item, dict) and item.get("action")
    }
    scene = set()
    object_terms = set()
    relation = set()
    if isinstance(attrs, dict):
        scene_value = str(attrs.get("scene", "")).lower().replace("_", " ")
        person_value = str(attrs.get("person_type", "")).lower().replace("_", " ")
        age_value = str(attrs.get("age_group", "")).lower().replace("_", " ")
        scene.update(scene_value.split())
        object_terms.update(person_value.split())
        object_terms.update(age_value.split())
        relation.update(person_value.split())
    return {
        "action": {term for term in actions.union(sequence) if len(term) >= 3},
        "object": {term for term in object_terms if len(term) >= 3},
        "scene": {term for term in scene if len(term) >= 3},
        "relation": {term for term in relation if len(term) >= 3},
    }


def _overlap_score(query_terms: list[str], video_terms: set[str]) -> float:
    query_set = {term.lower() for term in query_terms if term}
    if not query_set or not video_terms:
        return 0.0
    return float(len(query_set.intersection(video_terms))) / max(1, min(len(query_set), len(video_terms)))


def _sequence_score(query_actions: list[str], payload: dict[str, Any]) -> float:
    if not query_actions:
        return 0.0
    sequence = [
        str(item.get("action", "")).lower()
        for item in payload.get("action_sequence", [])
        if isinstance(item, dict) and item.get("action")
    ]
    if not sequence:
        return 0.0
    cursor = 0
    matched = 0
    for action in query_actions:
        for seq_idx in range(cursor, len(sequence)):
            if sequence[seq_idx] == action:
                matched += 1
                cursor = seq_idx + 1
                break
    return float(matched) / max(1, len(query_actions))


def _pseudo_caption(payload: dict[str, Any]) -> str:
    attrs = payload.get("visual_attributes", {}) if isinstance(payload, dict) else {}
    scene = str(attrs.get("scene", "unknown scene")).replace("_", " ")
    person = str(attrs.get("person_type", "person")).replace("_", " ")
    age = str(attrs.get("age_group", "")).replace("_", " ")
    actions = [
        str(item.get("action", "")).replace("_", " ")
        for item in payload.get("actions", [])[:3]
        if isinstance(item, dict) and item.get("action")
    ]
    action_text = ", ".join(actions) if actions else "uncertain action"
    subject = " ".join([age, person]).strip()
    return f"{subject} in {scene}; likely actions: {action_text}."


def _component_scores(
    structured: dict[str, list[str]],
    payload: dict[str, Any],
) -> dict[str, float]:
    terms = _alignment_terms(payload)
    action = _overlap_score(structured.get("action", []), terms["action"])
    object_score = _overlap_score(structured.get("object", []), terms["object"])
    scene = _overlap_score(structured.get("scene", []), terms["scene"])
    relation = _overlap_score(structured.get("relation", []), terms["relation"])
    sequence = _sequence_score(structured.get("action", []), payload)
    present_scores = [
        score
        for key, score in (
            ("action", action),
            ("object", object_score),
            ("scene", scene),
            ("relation", relation),
        )
        if structured.get(key)
    ]
    if present_scores:
        alignment = 0.85 * float(np.mean(present_scores)) + 0.15 * sequence
    else:
        alignment = 0.15 * sequence
    return {
        "action": round(action, 6),
        "object": round(object_score, 6),
        "scene": round(scene, 6),
        "relation": round(relation, 6),
        "sequence": round(sequence, 6),
        "alignment": round(float(alignment), 6),
    }


def _target_union(entry: TeacherSupervisionEntry) -> dict[str, float]:
    scores: dict[str, float] = {}
    for targets in (entry.similarity_targets, entry.listwise_targets):
        for target in targets:
            scores[target.video_id] = max(float(target.score), scores.get(target.video_id, -1e9))
    if entry.gt_video_id:
        scores.setdefault(entry.gt_video_id, max(scores.values()) if scores else 1.0)
    return scores


def calibrate_teacher(
    *,
    teacher_supervision: str,
    alignment_teacher: str,
    multiview_features: str,
    out: str,
    model_name: str,
    pretrained: str,
    base_weight: float,
    alignment_weight: float,
    multiview_weight: float,
    topk: int,
    component_metadata_topk: int,
) -> None:
    entries = load_teacher_supervision(_resolve_path(teacher_supervision))
    alignment_lookup = _load_alignment_teacher(alignment_teacher)
    use_multiview = multiview_weight > 0 and bool(multiview_features.strip())
    multiview_lookup = _load_multiview_features(multiview_features) if use_multiview else {}
    clip_bundle = load_clip(model_name=model_name, pretrained=pretrained) if use_multiview else None

    calibrated_entries: list[TeacherSupervisionEntry] = []
    coverage = {
        "queries": 0,
        "targets": 0,
        "targets_with_alignment": 0,
        "targets_with_multiview": 0,
        "gt_top1_after_calibration": 0,
    }
    for entry in tqdm(entries.values(), desc="Calibrate teacher with alignment", dynamic_ncols=True):
        coverage["queries"] += 1
        structured = extract_structured_prototypes(entry.query)
        base_scores = _target_union(entry)
        base_norm = _normalize(base_scores)
        query_vec = encode_text(clip_bundle, entry.query) if clip_bundle is not None else None

        alignment_scores: dict[str, float] = {}
        multiview_scores: dict[str, float] = {}
        component_meta: dict[str, dict[str, Any]] = {}
        for video_id, base_score in base_scores.items():
            coverage["targets"] += 1
            payload = alignment_lookup.get(video_id, {})
            components = _component_scores(structured, payload) if payload else {
                "action": 0.0,
                "object": 0.0,
                "scene": 0.0,
                "relation": 0.0,
                "sequence": 0.0,
                "alignment": 0.0,
            }
            alignment_scores[video_id] = float(components["alignment"])
            if payload:
                coverage["targets_with_alignment"] += 1

            views = multiview_lookup.get(video_id) if query_vec is not None else None
            if query_vec is not None and views is not None and views.ndim == 2:
                view_scores = views @ query_vec
                multiview_scores[video_id] = float(np.max(view_scores))
                coverage["targets_with_multiview"] += 1
            else:
                multiview_scores[video_id] = 0.0
            component_meta[video_id] = {
                **components,
                "base": round(float(base_score), 6),
                "pseudo_caption": _pseudo_caption(payload) if payload else "",
            }

        alignment_norm = _normalize(alignment_scores)
        multiview_norm = _normalize(multiview_scores)
        calibrated: list[TeacherTarget] = []
        for video_id in base_scores:
            score = (
                base_weight * base_norm.get(video_id, 0.0)
                + alignment_weight * alignment_norm.get(video_id, 0.0)
                + multiview_weight * multiview_norm.get(video_id, 0.0)
            )
            component_meta[video_id]["multiview"] = round(float(multiview_norm.get(video_id, 0.0)), 6)
            component_meta[video_id]["calibrated"] = round(float(score), 6)
            calibrated.append(TeacherTarget(video_id=video_id, score=float(score)))

        calibrated.sort(key=lambda item: item.score, reverse=True)
        if calibrated and calibrated[0].video_id == entry.gt_video_id:
            coverage["gt_top1_after_calibration"] += 1
        selected = calibrated[:topk]
        selected_video_ids = {target.video_id for target in calibrated[:component_metadata_topk]}
        metadata = dict(entry.metadata)
        metadata.update({
            "teacher_layer": "alignment_calibrated_v1",
            "query_components": structured,
            "calibration_weights": {
                "base": base_weight,
                "alignment": alignment_weight,
                "multiview": multiview_weight,
            },
            "component_alignment": {
                video_id: payload
                for video_id, payload in component_meta.items()
                if video_id in selected_video_ids
            },
        })
        calibrated_entries.append(
            TeacherSupervisionEntry(
                qid=entry.qid,
                query=entry.query,
                gt_video_id=entry.gt_video_id,
                source=f"{entry.source}+alignment_calibrated_v1",
                similarity_targets=selected,
                listwise_targets=selected,
                hard_negatives=[target.video_id for target in selected if target.video_id != entry.gt_video_id],
                frame_relevance=entry.frame_relevance,
                prototype_terms=entry.prototype_terms,
                structured_prototypes=structured,
                constraint_tags=entry.constraint_tags,
                metadata=metadata,
            )
        )

    out_path = _resolve_path(out)
    write_teacher_supervision(out_path, calibrated_entries)
    summary = {
        "out": str(out_path),
        "entries": len(calibrated_entries),
        "coverage": coverage,
        "weights": {
            "base": base_weight,
            "alignment": alignment_weight,
            "multiview": multiview_weight,
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    append_research_log(
        step="teacher_layer::alignment_calibrated_v1",
        summary=(
            "Teacher Layer v1 已将 listwise distillation 升级为 alignment distillation："
            "每个 query 拆为 action/object/scene/relation，并为候选视频写入局部对齐分数与伪 dense caption。"
        ),
        decisions=[
            f"Base teacher supervision: {teacher_supervision}",
            f"Alignment teacher: {alignment_teacher}",
            f"Multiview features: {multiview_features}",
            f"Calibration weights: base={base_weight}, alignment={alignment_weight}, multiview={multiview_weight}",
            "输出 teacher supervision 中保留 component_alignment，后续 student 通过 component_alignment_weight 学局部对齐。",
        ],
        citations=[
            "teachclip_cvpr2024",
            "mv_adapter_cvpr2024",
            "sentence_component_cvprw2024",
            "discovla_cvpr2025",
        ],
        artifacts=[str(out_path)],
        extra=summary,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate teacher supervision with component-level alignment.")
    parser.add_argument("--teacher_supervision", type=str, required=True)
    parser.add_argument("--alignment_teacher", type=str, required=True)
    parser.add_argument("--multiview_features", type=str, default="")
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--model_name", type=str, default="ViT-H-14")
    parser.add_argument("--pretrained", type=str, default="laion2b_s32b_b79k")
    parser.add_argument("--base_weight", type=float, default=0.55)
    parser.add_argument("--alignment_weight", type=float, default=0.25)
    parser.add_argument("--multiview_weight", type=float, default=0.20)
    parser.add_argument("--topk", type=int, default=20)
    parser.add_argument("--component_metadata_topk", type=int, default=30)
    args = parser.parse_args()

    calibrate_teacher(
        teacher_supervision=args.teacher_supervision,
        alignment_teacher=args.alignment_teacher,
        multiview_features=args.multiview_features,
        out=args.out,
        model_name=args.model_name,
        pretrained=args.pretrained,
        base_weight=args.base_weight,
        alignment_weight=args.alignment_weight,
        multiview_weight=args.multiview_weight,
        topk=args.topk,
        component_metadata_topk=args.component_metadata_topk,
    )


if __name__ == "__main__":
    main()
