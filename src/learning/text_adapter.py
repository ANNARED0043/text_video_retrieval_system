from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from tqdm import tqdm

from src.config import load_config
from src.features.clip_encoder import load_clip, encode_text
from src.learning.teacher_supervision import TeacherSupervisionEntry, entry_for_query
from src.llm.semantic_memory import extract_structured_prototypes


def _normalize(vecs: np.ndarray) -> np.ndarray:
    denom = np.linalg.norm(vecs, axis=-1, keepdims=True) + 1e-12
    return (vecs / denom).astype(np.float32)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _candidate_manifest_stems(manifest_name: str) -> list[str]:
    stem = manifest_name.replace(".jsonl", "")
    candidates = [stem]
    for marker in ("_safe_dev", "_safe_train", "_1kA"):
        if marker in stem:
            candidates.append(stem.replace(marker, ""))
    uniq: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        if item and item not in seen:
            uniq.append(item)
            seen.add(item)
    return uniq


def _resolve_feature_dir(manifest_name: str, pooling_mode: str, model_name: str, pretrained: str) -> Path:
    cfg = load_config()
    model_suffix = f"{model_name}_{pretrained}".replace("/", "_")
    candidates: list[Path] = []
    for manifest_stem in _candidate_manifest_stems(manifest_name):
        candidates.extend([
            cfg.paths.data_dir / "features" / manifest_stem / pooling_mode / model_suffix,
            cfg.paths.data_dir / "features" / manifest_stem / pooling_mode / model_suffix.lower(),
            cfg.paths.data_dir / "features" / manifest_stem / model_suffix / pooling_mode,
            cfg.paths.data_dir / "features" / manifest_stem / model_suffix.lower() / pooling_mode,
            cfg.paths.data_dir / "features" / manifest_stem / pooling_mode,
        ])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


@dataclass
class AdapterTrainingConfig:
    manifest_name: str
    query_file: str
    pooling_mode: str = "mean"
    model_name: str = "ViT-H-14"
    pretrained: str = "laion2b_s32b_b79k"
    device: str = "cuda"
    hard_negatives: int = 12
    prototype_weight: float = 0.0
    similarity_teacher_weight: float = 0.0
    frame_teacher_weight: float = 0.0
    rerank_teacher_weight: float = 0.0
    late_interaction_weight: float = 0.0
    residual_scale: float = 0.35
    adapter_mode: str = "gated"
    lr: float = 1e-3
    weight_decay: float = 1e-4
    epochs: int = 2
    batch_size: int = 32
    eval_batch_size: int = 8
    max_train_queries: int = 0
    hard_negative_mode: str = "teacher_hybrid"
    teacher_temperature: float = 0.07
    prototype_teacher_weight: float = 0.08
    distill_candidate_topk: int = 24
    false_negative_margin: float = 0.02
    uncertainty_aware_temperature: bool = False
    teacher_temperature_min: float = 0.05
    teacher_temperature_max: float = 0.11
    structured_prototype_weight: float = 0.0
    video_aggregation_weight: float = 0.0
    teacher_reliability_gating: bool = False
    teacher_max_gt_rank: int = 5
    teacher_min_margin: float = 0.01
    teacher_max_uncertainty: float = 0.95
    memory_augmented_weight: float = 0.0
    teacher_first_candidates: bool = False
    teacher_pairwise_weight: float = 0.0
    cross_modal_video_weight: float = 0.0
    alignment_teacher_weight: float = 0.0
    multiview_features: str = ""
    multiview_weight: float = 0.0
    multiview_pooling: str = "max"
    multiview_temperature: float = 0.07
    video_temporal_adapter_weight: float = 0.0
    component_alignment_weight: float = 0.0
    query_aware_fusion: bool = False
    component_view_weight: float = 0.0


@dataclass
class RetrievalLearningDataset:
    config: AdapterTrainingConfig
    clip_bundle: Any
    video_ids: list[str]
    video_matrix: np.ndarray
    video_max_matrix: np.ndarray
    video_multiview_matrix: np.ndarray | None
    video_id_to_index: dict[str, int]
    queries: list[dict[str, Any]]

    @classmethod
    def build(cls, config: AdapterTrainingConfig) -> "RetrievalLearningDataset":
        cfg = load_config()
        manifest_path = cfg.paths.manifests_dir / config.manifest_name
        query_path = cfg.paths.data_dir / "annotations" / "msrvtt" / config.query_file
        feature_dir = _resolve_feature_dir(
            manifest_name=config.manifest_name,
            pooling_mode=config.pooling_mode,
            model_name=config.model_name,
            pretrained=config.pretrained,
        )

        segment_rows = _read_jsonl(manifest_path)
        video_to_vecs: dict[str, list[np.ndarray]] = {}
        for row in segment_rows:
            segment_id = row["segment_id"]
            feature_path = feature_dir / f"{segment_id}.npy"
            if feature_path.exists():
                try:
                    vec = np.load(feature_path).astype(np.float32)
                except Exception:
                    vec = None
                if vec is not None and vec.ndim == 1:
                    video_to_vecs.setdefault(row["video_id"], []).append(vec)
                continue

            legacy_paths = sorted(feature_dir.glob(f"{row['video_id']}_*.npy"))
            for legacy_path in legacy_paths:
                try:
                    vec = np.load(legacy_path).astype(np.float32)
                except Exception:
                    continue
                if vec.ndim == 1:
                    video_to_vecs.setdefault(row["video_id"], []).append(vec)

        video_ids = sorted(video_to_vecs.keys())
        video_mean_vectors: list[np.ndarray] = []
        video_max_vectors: list[np.ndarray] = []
        for video_id in video_ids:
            seg_matrix = _normalize(np.stack(video_to_vecs[video_id], axis=0))
            video_mean_vectors.append(seg_matrix.mean(axis=0))
            video_max_vectors.append(seg_matrix.max(axis=0))
        video_matrix = _normalize(np.stack(video_mean_vectors, axis=0).astype(np.float32))
        video_max_matrix = _normalize(np.stack(video_max_vectors, axis=0).astype(np.float32))
        video_id_to_index = {video_id: idx for idx, video_id in enumerate(video_ids)}
        video_multiview_matrix = None
        if config.multiview_features.strip():
            multiview_path = Path(config.multiview_features)
            if not multiview_path.is_absolute():
                multiview_path = cfg.paths.project_root / multiview_path
            if multiview_path.exists():
                payload = np.load(multiview_path, allow_pickle=True)
                mv_video_ids = [str(item) for item in payload["video_ids"].tolist()]
                mv_features = payload["features"].astype(np.float32)
                view_count = int(mv_features.shape[1]) if mv_features.ndim == 3 else 3
                mv_lookup = {video_id: mv_features[idx] for idx, video_id in enumerate(mv_video_ids)}
                aligned_views: list[np.ndarray] = []
                for video_id, mean_vec in zip(video_ids, video_matrix):
                    views = mv_lookup.get(video_id)
                    if views is None or views.ndim != 2 or views.shape[-1] != mean_vec.shape[-1]:
                        views = np.repeat(mean_vec[None, :], view_count, axis=0)
                    elif views.shape[0] != view_count:
                        views = views[:view_count] if views.shape[0] > view_count else np.concatenate(
                            [views, np.repeat(mean_vec[None, :], view_count - views.shape[0], axis=0)],
                            axis=0,
                        )
                    aligned_views.append(views.astype(np.float32))
                stacked_views = np.stack(aligned_views, axis=0).astype(np.float32)
                flat = stacked_views.reshape(-1, stacked_views.shape[-1])
                video_multiview_matrix = _normalize(flat).reshape(stacked_views.shape)

        queries = _read_jsonl(query_path)
        for idx, row in enumerate(queries):
            row.setdefault("qid", idx)
        if config.max_train_queries > 0:
            queries = queries[: config.max_train_queries]

        clip_bundle = load_clip(model_name=config.model_name, pretrained=config.pretrained, device=config.device)
        return cls(
            config=config,
            clip_bundle=clip_bundle,
            video_ids=video_ids,
            video_matrix=video_matrix,
            video_max_matrix=video_max_matrix,
            video_multiview_matrix=video_multiview_matrix,
            video_id_to_index=video_id_to_index,
            queries=queries,
        )

    def encode_queries(self, query_rows: list[dict[str, Any]]) -> np.ndarray:
        feats = []
        for row in tqdm(query_rows, desc="Encode queries", dynamic_ncols=True, leave=False):
            feats.append(encode_text(self.clip_bundle, row["query"]))
        return _normalize(np.stack(feats, axis=0))


class TextResidualAdapter(nn.Module):
    def __init__(
        self,
        dim: int,
        residual_scale: float = 0.35,
        mode: str = "gated",
        video_aggregation_weight: float = 0.0,
    ) -> None:
        super().__init__()
        self.mode = mode
        self.proj = nn.Linear(dim, dim)
        nn.init.eye_(self.proj.weight)
        nn.init.zeros_(self.proj.bias)
        self.gate = nn.Linear(dim, 1)
        nn.init.zeros_(self.gate.weight)
        nn.init.constant_(self.gate.bias, -2.0)
        self.residual_scale = residual_scale
        self.video_gate = nn.Linear(dim, 1)
        nn.init.zeros_(self.video_gate.weight)
        nn.init.zeros_(self.video_gate.bias)
        self.video_aggregation_weight = video_aggregation_weight
        self.video_proj = nn.Linear(dim, dim)
        nn.init.eye_(self.video_proj.weight)
        nn.init.zeros_(self.video_proj.bias)
        self.video_query_proj = nn.Linear(dim, dim)
        nn.init.zeros_(self.video_query_proj.weight)
        nn.init.zeros_(self.video_query_proj.bias)
        self.temporal_view_proj = nn.Linear(dim, dim)
        nn.init.eye_(self.temporal_view_proj.weight)
        nn.init.zeros_(self.temporal_view_proj.bias)
        self.temporal_context_proj = nn.Linear(dim, dim)
        nn.init.eye_(self.temporal_context_proj.weight)
        nn.init.zeros_(self.temporal_context_proj.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        delta = self.proj(x)
        if self.mode == "gated":
            gate = torch.sigmoid(self.gate(x))
            y = x + self.residual_scale * gate * delta
        else:
            y = x + self.residual_scale * delta
        return F.normalize(y, dim=-1)

    def score_video(
        self,
        query_repr: torch.Tensor,
        mean_video: torch.Tensor,
        max_video: torch.Tensor | None = None,
        cross_modal_video_weight: float = 0.0,
    ) -> torch.Tensor:
        mean_scores = query_repr @ mean_video.T
        scores = mean_scores
        if max_video is not None and self.video_aggregation_weight > 0:
            max_scores = query_repr @ max_video.T
            gate = torch.sigmoid(self.video_gate(query_repr)) * self.video_aggregation_weight
            scores = (1.0 - gate) * mean_scores + gate * max_scores
        if cross_modal_video_weight > 0:
            q_context = torch.tanh(self.video_query_proj(query_repr))
            video_delta = torch.tanh(self.video_proj(mean_video))
            adapted_video = F.normalize(
                mean_video.unsqueeze(0) + cross_modal_video_weight * q_context.unsqueeze(1) * video_delta.unsqueeze(0),
                dim=-1,
            )
            cross_scores = torch.sum(query_repr.unsqueeze(1) * adapted_video, dim=-1)
            scores = scores + cross_modal_video_weight * cross_scores
        return scores

    def score_multiview(
        self,
        query_repr: torch.Tensor,
        multiview_video: torch.Tensor | None,
        pooling: str = "max",
        temperature: float = 0.07,
        temporal_adapter_weight: float = 0.0,
    ) -> torch.Tensor | None:
        if multiview_video is None:
            return None
        view_tokens = multiview_video
        if temporal_adapter_weight > 0:
            # BT-Adapter inspired lightweight temporal branch over view tokens.
            # Backbone features stay frozen; only this tiny branch learns how
            # adjacent/global video views should adjust each other.
            temporal_context = view_tokens.mean(dim=1, keepdim=True)
            temporal_delta = torch.tanh(
                self.temporal_view_proj(view_tokens)
                - self.temporal_context_proj(temporal_context)
            )
            view_tokens = F.normalize(
                view_tokens + temporal_adapter_weight * temporal_delta,
                dim=-1,
            )
        view_scores = torch.einsum("bd,nvd->bnv", query_repr, view_tokens)
        if pooling == "attention":
            # X-Pool style: let each query softly select the most relevant
            # video views instead of using a query-agnostic fixed fusion.
            weights = F.softmax(view_scores / max(float(temperature), 1e-4), dim=-1)
            return (weights * view_scores).sum(dim=-1)
        return view_scores.max(dim=-1).values


def _query_terms(text: str) -> list[str]:
    return [token.strip(" ,.!?;:'\"()[]{}").lower() for token in text.split() if token.strip()]


def _query_fusion_scale(query: str) -> float:
    """Increase local evidence weight for component-rich queries."""
    structured = extract_structured_prototypes(query)
    action_count = len(structured.get("action", []))
    object_count = len(structured.get("object", []))
    scene_count = len(structured.get("scene", []))
    relation_count = len(structured.get("relation", []))
    terms = set(_query_terms(query))
    relation_terms = {
        "with", "between", "beside", "behind", "front", "near", "next",
        "holding", "wearing", "showing", "talking", "playing", "using",
    }
    attribute_terms = {
        "man", "woman", "girl", "boy", "child", "old", "young", "blonde",
        "black", "white", "red", "blue", "glasses", "shirt", "hat",
    }
    relation_hit = bool(terms.intersection(relation_terms))
    attribute_hit = bool(terms.intersection(attribute_terms))
    token_bonus = 0.10 if len(terms) >= 7 else 0.0
    # Query-type gate: local video evidence is most useful for action,
    # relation, and person-attribute queries; simple scene queries stay
    # closer to the stable global representation.
    scale = 0.78 + token_bonus
    scale += 0.20 * min(action_count, 2)
    scale += 0.12 * min(object_count, 2)
    scale += 0.08 * min(scene_count, 2)
    scale += 0.28 * min(relation_count, 2)
    if relation_hit:
        scale += 0.22
    if attribute_hit:
        scale += 0.20
    return float(np.clip(scale, 0.65, 1.95))


def _component_prompts(query: str) -> list[str]:
    structured = extract_structured_prototypes(query)
    prompts: list[str] = []
    templates = {
        "action": "a video moment showing the action of {term}",
        "object": "a video frame containing {term}",
        "scene": "a video scene in or around {term}",
        "relation": "a video frame showing the relation {term}",
    }
    for group_name, values in structured.items():
        template = templates.get(group_name, "a video frame about {term}")
        for value in values[:3]:
            value = str(value).strip().lower()
            if value:
                prompts.append(template.format(term=value))
    if not prompts:
        terms = _query_terms(query)
        if 0 < len(terms) <= 6:
            prompts.append(f"a video frame matching: {query}")
    seen: set[str] = set()
    unique_prompts: list[str] = []
    for prompt in prompts:
        if prompt not in seen:
            unique_prompts.append(prompt)
            seen.add(prompt)
    return unique_prompts[:8]


def _component_view_scores(
    *,
    clip_bundle: Any,
    query_text: str,
    multiview_video: torch.Tensor | None,
    device: str,
    cache: dict[str, torch.Tensor],
) -> torch.Tensor | None:
    if multiview_video is None:
        return None
    prompts = _component_prompts(query_text)
    if not prompts:
        return None
    cache_key = "\n".join(prompts)
    if cache_key in cache:
        component_tensor = cache[cache_key]
    else:
        feats = [encode_text(clip_bundle, prompt) for prompt in prompts]
        component_tensor = torch.tensor(
            _normalize(np.stack(feats, axis=0)),
            dtype=torch.float32,
            device=device,
        )
        cache[cache_key] = component_tensor
    view_scores = torch.einsum("cd,nvd->cnv", component_tensor, multiview_video)
    return view_scores.max(dim=-1).values.mean(dim=0)


def _prototype_bonus(query_text: str, prototype_memory: dict[str, Any]) -> float:
    terms = set(_query_terms(query_text))
    prototypes = prototype_memory.get("prototypes", {}) if isinstance(prototype_memory, dict) else {}
    if not prototypes:
        return 0.0
    matches = 0
    for name in prototypes.keys():
        tail = str(name).split("::")[-1].lower()
        if tail in terms:
            matches += 1
    return float(matches)


def _constraint_bonus(query_text: str, constraint_memory: dict[str, Any]) -> float:
    terms = set(_query_terms(query_text))
    bonus = 0.0
    for group_name in (
        "prefer_dense_categories",
        "prefer_expand_categories",
        "prefer_conservative_rewrite_categories",
        "prefer_strong_rewrite_categories",
    ):
        values = constraint_memory.get(group_name, []) if isinstance(constraint_memory, dict) else []
        if any(str(value).lower() in terms for value in values):
            bonus += 1.0
    return bonus


def _memory_augmented_bonus(
    query_text: str,
    video_ids: list[str],
    semantic_memory: dict[str, Any],
) -> np.ndarray:
    if not semantic_memory:
        return np.zeros(len(video_ids), dtype=np.float32)
    stage3_memory = semantic_memory.get("stage3_memory", {})
    if not isinstance(stage3_memory, dict):
        return np.zeros(len(video_ids), dtype=np.float32)
    prototype_video_memory = stage3_memory.get("prototype_video_memory", {})
    if not isinstance(prototype_video_memory, dict) or not prototype_video_memory:
        return np.zeros(len(video_ids), dtype=np.float32)

    structured = extract_structured_prototypes(query_text)
    key_scores: list[dict[str, float]] = []
    for group_name, values in structured.items():
        for value in values:
            payload = prototype_video_memory.get(f"{group_name}::{value}", {})
            if isinstance(payload, dict) and payload:
                key_scores.append({str(k): float(v) for k, v in payload.items()})

    if not key_scores:
        return np.zeros(len(video_ids), dtype=np.float32)

    accum: dict[str, float] = {}
    for payload in key_scores:
        local_max = max(payload.values()) if payload else 0.0
        norm = local_max if local_max > 1e-8 else 1.0
        for video_id, score in payload.items():
            accum[video_id] = accum.get(video_id, 0.0) + (score / norm)

    if not accum:
        return np.zeros(len(video_ids), dtype=np.float32)

    denom = max(float(len(key_scores)), 1.0)
    return np.asarray([float(accum.get(video_id, 0.0)) / denom for video_id in video_ids], dtype=np.float32)


def _alignment_terms(payload: dict[str, Any]) -> set[str]:
    terms: set[str] = set()
    attrs = payload.get("visual_attributes", {}) if isinstance(payload, dict) else {}
    if isinstance(attrs, dict):
        for key in ("age_group", "person_type", "scene"):
            value = attrs.get(key)
            if value:
                terms.update(str(value).lower().replace("_", " ").split())
    for item in payload.get("actions", []) if isinstance(payload, dict) else []:
        if isinstance(item, dict) and item.get("action"):
            terms.add(str(item["action"]).lower())
    for item in payload.get("action_sequence", []) if isinstance(payload, dict) else []:
        if isinstance(item, dict) and item.get("action"):
            terms.add(str(item["action"]).lower())
    return {term for term in terms if len(term) >= 3}


def _component_alignment_scores(
    teacher_entry: TeacherSupervisionEntry | None,
    candidate_video_ids: list[str],
) -> np.ndarray:
    if teacher_entry is None or not isinstance(teacher_entry.metadata, dict):
        return np.zeros(len(candidate_video_ids), dtype=np.float32)
    component_payload = teacher_entry.metadata.get("component_alignment", {})
    if not isinstance(component_payload, dict):
        return np.zeros(len(candidate_video_ids), dtype=np.float32)

    scores: list[float] = []
    for video_id in candidate_video_ids:
        item = component_payload.get(video_id, {})
        if not isinstance(item, dict):
            scores.append(0.0)
            continue
        value = item.get("alignment", item.get("calibrated", 0.0))
        try:
            scores.append(float(value))
        except Exception:
            scores.append(0.0)
    if not any(score > 0 for score in scores):
        return np.zeros(len(candidate_video_ids), dtype=np.float32)
    return np.asarray(scores, dtype=np.float32)


def _ordered_action_score(query_text: str, payload: dict[str, Any]) -> float:
    query_actions = extract_structured_prototypes(query_text).get("action", [])
    if not query_actions or not isinstance(payload, dict):
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


def _alignment_bonus(
    query_text: str,
    video_ids: list[str],
    alignment_teacher: dict[str, Any] | None,
) -> np.ndarray:
    if not alignment_teacher:
        return np.zeros(len(video_ids), dtype=np.float32)
    query_terms = set(extract_structured_prototypes(query_text).get("action", []))
    query_terms.update(extract_structured_prototypes(query_text).get("object", []))
    query_terms.update(extract_structured_prototypes(query_text).get("scene", []))
    query_terms.update(_query_terms(query_text))
    if not query_terms:
        return np.zeros(len(video_ids), dtype=np.float32)
    bonuses: list[float] = []
    for video_id in video_ids:
        payload = alignment_teacher.get(video_id, {})
        terms = _alignment_terms(payload) if isinstance(payload, dict) else set()
        if not terms:
            bonuses.append(0.0)
            continue
        overlap = len(query_terms.intersection(terms))
        term_score = float(overlap) / max(1, min(len(query_terms), len(terms)))
        sequence_score = _ordered_action_score(query_text, payload)
        bonuses.append(float(0.75 * term_score + 0.25 * sequence_score))
    return np.asarray(bonuses, dtype=np.float32)


def _teacher_score_lookup(teacher_entry: TeacherSupervisionEntry | None) -> dict[str, float]:
    if teacher_entry is None:
        return {}
    scores: dict[str, float] = {}
    for collection in (teacher_entry.similarity_targets, teacher_entry.listwise_targets):
        for target in collection:
            if target.video_id not in scores or target.score > scores[target.video_id]:
                scores[target.video_id] = float(target.score)
    return scores


def _teacher_positive_score(
    teacher_entry: TeacherSupervisionEntry | None,
    gt_video_id: str,
) -> float | None:
    if teacher_entry is None:
        return None
    teacher_lookup = _teacher_score_lookup(teacher_entry)
    gt_score = teacher_lookup.get(gt_video_id)
    if gt_score is not None:
        return float(gt_score)
    if teacher_lookup:
        return float(max(teacher_lookup.values()))
    return None


def _teacher_uncertainty(teacher_entry: TeacherSupervisionEntry | None) -> float:
    if teacher_entry is None:
        return 0.5
    metadata = teacher_entry.metadata if isinstance(teacher_entry.metadata, dict) else {}
    cached = metadata.get("uncertainty_score")
    if cached is not None:
        try:
            return float(np.clip(float(cached), 0.0, 1.0))
        except Exception:
            pass

    targets = teacher_entry.listwise_targets or teacher_entry.similarity_targets
    if not targets:
        return 0.5
    scores = np.asarray([float(target.score) for target in targets[:10]], dtype=np.float32)
    if scores.size == 0:
        return 0.5
    if scores.size == 1:
        return 0.5

    top1 = float(scores[0])
    top2 = float(scores[1])
    gap = max(0.0, top1 - top2)
    scale = max(abs(top1), 1e-6)
    gap_confidence = float(np.clip(gap / scale, 0.0, 1.0))
    gap_uncertainty = 1.0 - gap_confidence

    shifted = scores - float(scores.max())
    probs = np.exp(shifted)
    probs = probs / max(float(probs.sum()), 1e-8)
    entropy = float(-(probs * np.log(probs + 1e-8)).sum())
    entropy_norm = entropy / max(float(np.log(len(probs))), 1e-8)
    return float(np.clip(0.5 * gap_uncertainty + 0.5 * entropy_norm, 0.0, 1.0))


def _teacher_gt_rank(
    teacher_entry: TeacherSupervisionEntry | None,
    gt_video_id: str,
) -> int | None:
    if teacher_entry is None:
        return None
    targets = teacher_entry.listwise_targets or teacher_entry.similarity_targets
    for rank, target in enumerate(targets, start=1):
        if target.video_id == gt_video_id:
            return rank
    return None


def _teacher_margin(teacher_entry: TeacherSupervisionEntry | None) -> float:
    if teacher_entry is None:
        return 0.0
    targets = teacher_entry.listwise_targets or teacher_entry.similarity_targets
    if len(targets) < 2:
        return 0.0
    return max(0.0, float(targets[0].score) - float(targets[1].score))


def _teacher_reliability(
    config: AdapterTrainingConfig,
    teacher_entry: TeacherSupervisionEntry | None,
    gt_video_id: str,
) -> float:
    if teacher_entry is None:
        return 0.0
    gt_rank = _teacher_gt_rank(teacher_entry, gt_video_id)
    if gt_rank is None:
        return 0.0
    uncertainty = _teacher_uncertainty(teacher_entry)
    margin = _teacher_margin(teacher_entry)
    if not config.teacher_reliability_gating:
        return 1.0
    if gt_rank > config.teacher_max_gt_rank:
        return 0.0
    if uncertainty > config.teacher_max_uncertainty:
        return 0.0
    if margin < config.teacher_min_margin:
        return 0.0
    rank_score = 1.0 - min(max((gt_rank - 1) / max(config.teacher_max_gt_rank - 1, 1), 0.0), 1.0)
    uncertainty_score = 1.0 - min(max(uncertainty / max(config.teacher_max_uncertainty, 1e-6), 0.0), 1.0)
    margin_score = min(max(margin / max(config.teacher_min_margin, 1e-6), 0.0), 2.0) / 2.0
    return float(np.clip((rank_score + uncertainty_score + margin_score) / 3.0, 0.0, 1.0))


def _resolve_teacher_temperature(
    config: AdapterTrainingConfig,
    teacher_entry: TeacherSupervisionEntry | None,
) -> float:
    if not config.uncertainty_aware_temperature:
        return float(config.teacher_temperature)
    uncertainty = _teacher_uncertainty(teacher_entry)
    tau = config.teacher_temperature_min + uncertainty * (config.teacher_temperature_max - config.teacher_temperature_min)
    return float(np.clip(tau, config.teacher_temperature_min, config.teacher_temperature_max))


def _prototype_term_bonus(query_text: str, teacher_entry: TeacherSupervisionEntry | None) -> float:
    if teacher_entry is None or not teacher_entry.prototype_terms:
        return 0.0
    query_terms = set(_query_terms(query_text))
    teacher_terms = {term.lower() for term in teacher_entry.prototype_terms if term}
    if not teacher_terms:
        return 0.0
    overlap = len(query_terms.intersection(teacher_terms))
    return float(overlap) / max(1, len(teacher_terms))


def _structured_prototype_bonus(query_text: str, teacher_entry: TeacherSupervisionEntry | None) -> float:
    query_structured = extract_structured_prototypes(query_text)
    teacher_structured = {}
    if teacher_entry is not None and isinstance(teacher_entry.structured_prototypes, dict):
        teacher_structured = teacher_entry.structured_prototypes
    if not teacher_structured:
        return 0.0

    overlaps: list[float] = []
    for group_name in ("action", "object", "scene", "relation"):
        query_terms = set(query_structured.get(group_name, []))
        teacher_terms = {str(term).lower() for term in teacher_structured.get(group_name, []) if term}
        if not query_terms or not teacher_terms:
            continue
        overlaps.append(float(len(query_terms.intersection(teacher_terms))) / max(1, len(teacher_terms)))
    if not overlaps:
        return 0.0
    return float(sum(overlaps) / len(overlaps))


def _append_unique(indices: list[int], seen: set[int], candidate: int, gt_index: int) -> None:
    if candidate == gt_index or candidate in seen:
        return
    indices.append(candidate)
    seen.add(candidate)


def _teacher_ranked_indices(
    teacher_entry: TeacherSupervisionEntry | None,
    video_id_to_index: dict[str, int],
    gt_index: int,
) -> list[int]:
    ranked: list[int] = []
    seen: set[int] = set()
    if teacher_entry is None:
        return ranked
    for targets in (teacher_entry.listwise_targets, teacher_entry.similarity_targets):
        for target in targets:
            idx = video_id_to_index.get(target.video_id)
            if idx is None:
                continue
            _append_unique(ranked, seen, int(idx), gt_index)
    return ranked


def _teacher_negative_indices(
    teacher_entry: TeacherSupervisionEntry | None,
    video_id_to_index: dict[str, int],
    gt_index: int,
) -> list[int]:
    if teacher_entry is None:
        return []
    negatives: list[int] = []
    seen: set[int] = set()
    for video_id in teacher_entry.hard_negatives:
        idx = video_id_to_index.get(video_id)
        if idx is not None:
            _append_unique(negatives, seen, int(idx), gt_index)
    for target in teacher_entry.listwise_targets:
        idx = video_id_to_index.get(target.video_id)
        if idx is not None:
            _append_unique(negatives, seen, int(idx), gt_index)
    for target in teacher_entry.similarity_targets:
        idx = video_id_to_index.get(target.video_id)
        if idx is not None:
            _append_unique(negatives, seen, int(idx), gt_index)
    return negatives


def _teacher_pairwise_preferences(
    teacher_entry: TeacherSupervisionEntry | None,
) -> list[tuple[str, str, float, float]]:
    if teacher_entry is None or not isinstance(teacher_entry.metadata, dict):
        return []
    raw_items = teacher_entry.metadata.get("pairwise_preferences", [])
    preferences: list[tuple[str, str, float, float]] = []
    if not isinstance(raw_items, list):
        return preferences
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        positive = str(item.get("positive", "") or item.get("better", ""))
        negative = str(item.get("negative", "") or item.get("worse", ""))
        if not positive or not negative:
            continue
        try:
            margin = float(item.get("margin", 0.03))
        except Exception:
            margin = 0.03
        try:
            weight = float(item.get("weight", 1.0))
        except Exception:
            weight = 1.0
        preferences.append((positive, negative, max(margin, 0.0), max(weight, 0.0)))
    return preferences


def mine_hard_negative_indices(
    query_vec: np.ndarray,
    video_matrix: np.ndarray,
    gt_index: int,
    topk: int,
    *,
    teacher_entry: TeacherSupervisionEntry | None = None,
    video_id_to_index: dict[str, int] | None = None,
    mode: str = "teacher_hybrid",
    false_negative_margin: float = 0.02,
) -> list[int]:
    scores = video_matrix @ query_vec
    ranked = np.argsort(-scores)
    if mode == "topk":
        hard: list[int] = []
        for idx in ranked:
            if int(idx) == int(gt_index):
                continue
            hard.append(int(idx))
            if len(hard) >= topk:
                break
        return hard

    hard: list[int] = []
    seen: set[int] = set()
    teacher_indices = _teacher_negative_indices(teacher_entry, video_id_to_index or {}, gt_index)
    teacher_lookup = _teacher_score_lookup(teacher_entry)
    gt_video_id = None
    for video_id, idx in (video_id_to_index or {}).items():
        if int(idx) == int(gt_index):
            gt_video_id = video_id
            break
    positive_teacher_score = _teacher_positive_score(teacher_entry, gt_video_id or "")
    positive_student_score = float(scores[int(gt_index)])

    def _is_false_negative(candidate_idx: int) -> bool:
        candidate_score = float(scores[int(candidate_idx)])
        if candidate_score >= positive_student_score - false_negative_margin:
            return True
        if gt_video_id and teacher_lookup:
            candidate_video_id = None
            for video_id, idx in (video_id_to_index or {}).items():
                if int(idx) == int(candidate_idx):
                    candidate_video_id = video_id
                    break
            if candidate_video_id:
                teacher_score = teacher_lookup.get(candidate_video_id)
                if teacher_score is not None and positive_teacher_score is not None:
                    if float(teacher_score) >= float(positive_teacher_score) - false_negative_margin:
                        return True
        return False

    teacher_quota = min(max(2, topk // 3), len(teacher_indices)) if teacher_indices else 0
    for idx in teacher_indices[:teacher_quota]:
        if _is_false_negative(idx):
            continue
        _append_unique(hard, seen, idx, gt_index)

    ranked_wo_gt = [int(idx) for idx in ranked if int(idx) != int(gt_index)]
    near_bucket = ranked_wo_gt[: min(len(ranked_wo_gt), max(4, topk))]
    mid_bucket = ranked_wo_gt[min(len(ranked_wo_gt), 5): min(len(ranked_wo_gt), 30)]
    far_bucket = ranked_wo_gt[min(len(ranked_wo_gt), 30): min(len(ranked_wo_gt), 120)]

    for idx in near_bucket:
        if len(hard) >= topk:
            break
        if _is_false_negative(idx):
            continue
        _append_unique(hard, seen, idx, gt_index)

    if len(hard) < topk and mid_bucket:
        step = max(1, len(mid_bucket) // max(1, topk - len(hard)))
        for idx in mid_bucket[::step]:
            if len(hard) >= topk:
                break
            if _is_false_negative(idx):
                continue
            _append_unique(hard, seen, idx, gt_index)

    if len(hard) < topk and far_bucket:
        step = max(1, len(far_bucket) // max(1, topk - len(hard)))
        for idx in far_bucket[::step]:
            if len(hard) >= topk:
                break
            if _is_false_negative(idx):
                continue
            _append_unique(hard, seen, idx, gt_index)

    for idx in teacher_indices[teacher_quota:]:
        if len(hard) >= topk:
            break
        if _is_false_negative(idx):
            continue
        _append_unique(hard, seen, idx, gt_index)

    for idx in ranked_wo_gt:
        if len(hard) >= topk:
            break
        if _is_false_negative(idx):
            continue
        _append_unique(hard, seen, idx, gt_index)

    return hard[:topk]


def _build_candidate_indices(
    gt_index: int,
    hard_indices: list[int],
    teacher_entry: TeacherSupervisionEntry | None,
    video_id_to_index: dict[str, int],
    candidate_topk: int,
    teacher_first: bool = False,
) -> list[int]:
    ordered: list[int] = [int(gt_index)]
    seen: set[int] = {int(gt_index)}
    teacher_ranked = _teacher_ranked_indices(teacher_entry, video_id_to_index, gt_index)
    if teacher_first:
        for idx in teacher_ranked:
            if int(idx) in seen:
                continue
            ordered.append(int(idx))
            seen.add(int(idx))
            if len(ordered) >= candidate_topk:
                return ordered
    for idx in hard_indices:
        if int(idx) not in seen:
            ordered.append(int(idx))
            seen.add(int(idx))
            if len(ordered) >= candidate_topk:
                return ordered
    if teacher_entry is not None:
        for idx in teacher_ranked:
            if int(idx) in seen:
                continue
            ordered.append(int(idx))
            seen.add(int(idx))
            if len(ordered) >= candidate_topk:
                return ordered
    return ordered[:candidate_topk]


def train_one_round(
    dataset: RetrievalLearningDataset,
    train_rows: list[dict[str, Any]],
    teacher_entries: dict[str, TeacherSupervisionEntry],
    prototype_memory: dict[str, Any],
    constraint_memory: dict[str, Any],
    alignment_teacher: dict[str, Any] | None = None,
    init_state_dict: dict[str, Any] | None = None,
) -> tuple[TextResidualAdapter, dict[str, float]]:
    device = dataset.config.device if torch.cuda.is_available() else "cpu"
    train_text = dataset.encode_queries(train_rows)
    video_matrix_np = dataset.video_matrix
    video_max_matrix_np = dataset.video_max_matrix
    video_matrix = torch.tensor(video_matrix_np, dtype=torch.float32, device=device)
    video_max_matrix = torch.tensor(video_max_matrix_np, dtype=torch.float32, device=device)
    video_multiview = (
        torch.tensor(dataset.video_multiview_matrix, dtype=torch.float32, device=device)
        if dataset.video_multiview_matrix is not None else None
    )

    adapter = TextResidualAdapter(
        dim=train_text.shape[1],
        residual_scale=dataset.config.residual_scale,
        mode=dataset.config.adapter_mode,
        video_aggregation_weight=dataset.config.video_aggregation_weight,
    ).to(device)
    if init_state_dict:
        adapter.load_state_dict(init_state_dict, strict=False)
    optimizer = torch.optim.AdamW(adapter.parameters(), lr=dataset.config.lr, weight_decay=dataset.config.weight_decay)

    running_losses: list[float] = []
    component_text_cache: dict[str, torch.Tensor] = {}
    for epoch in range(dataset.config.epochs):
        progress = tqdm(range(0, len(train_rows), dataset.config.batch_size), desc=f"Train adapter epoch {epoch + 1}/{dataset.config.epochs}", dynamic_ncols=True)
        for start in progress:
            batch_rows = train_rows[start:start + dataset.config.batch_size]
            batch_np = train_text[start:start + dataset.config.batch_size]
            batch_tensor = torch.tensor(batch_np, dtype=torch.float32, device=device)
            adapted = adapter(batch_tensor)

            losses: list[torch.Tensor] = []
            for local_idx, row in enumerate(batch_rows):
                gt_video_id = row["gt_video_id"]
                if gt_video_id not in dataset.video_id_to_index:
                    continue
                gt_index = dataset.video_id_to_index[gt_video_id]
                teacher_entry = entry_for_query(teacher_entries, row.get("qid", start + local_idx))
                teacher_reliability = _teacher_reliability(dataset.config, teacher_entry, gt_video_id)
                hard_indices = mine_hard_negative_indices(
                    batch_np[local_idx],
                    video_matrix_np,
                    gt_index,
                    dataset.config.hard_negatives,
                    teacher_entry=teacher_entry,
                    video_id_to_index=dataset.video_id_to_index,
                    mode=dataset.config.hard_negative_mode,
                    false_negative_margin=dataset.config.false_negative_margin,
                )
                candidate_indices = _build_candidate_indices(
                    gt_index=gt_index,
                    hard_indices=hard_indices,
                    teacher_entry=teacher_entry,
                    video_id_to_index=dataset.video_id_to_index,
                    candidate_topk=max(dataset.config.distill_candidate_topk, 1 + len(hard_indices)),
                    teacher_first=dataset.config.teacher_first_candidates,
                )
                candidate_matrix = video_matrix[candidate_indices]
                candidate_max_matrix = video_max_matrix[candidate_indices]
                candidate_multiview = video_multiview[candidate_indices] if video_multiview is not None else None
                logits = adapter.score_video(
                    adapted[local_idx : local_idx + 1],
                    candidate_matrix,
                    candidate_max_matrix,
                    cross_modal_video_weight=dataset.config.cross_modal_video_weight,
                )
                if dataset.config.multiview_weight > 0 and candidate_multiview is not None:
                    multiview_scores = adapter.score_multiview(
                        adapted[local_idx : local_idx + 1],
                        candidate_multiview,
                        pooling=dataset.config.multiview_pooling,
                        temperature=dataset.config.multiview_temperature,
                        temporal_adapter_weight=dataset.config.video_temporal_adapter_weight,
                    )
                    if multiview_scores is not None:
                        mv_weight = dataset.config.multiview_weight
                        if dataset.config.query_aware_fusion:
                            mv_weight *= _query_fusion_scale(row["query"])
                        logits = logits + mv_weight * multiview_scores
                if dataset.config.component_view_weight > 0 and candidate_multiview is not None:
                    component_scores = _component_view_scores(
                        clip_bundle=dataset.clip_bundle,
                        query_text=row["query"],
                        multiview_video=candidate_multiview,
                        device=device,
                        cache=component_text_cache,
                    )
                    if component_scores is not None:
                        cv_weight = dataset.config.component_view_weight
                        if dataset.config.query_aware_fusion:
                            cv_weight *= _query_fusion_scale(row["query"])
                        logits = logits + cv_weight * component_scores.unsqueeze(0)
                if dataset.config.memory_augmented_weight > 0:
                    candidate_video_ids = [dataset.video_ids[idx] for idx in candidate_indices]
                    memory_bonus = _memory_augmented_bonus(row["query"], candidate_video_ids, prototype_memory)
                    if np.any(memory_bonus):
                        logits = logits + dataset.config.memory_augmented_weight * torch.tensor(
                            memory_bonus,
                            dtype=torch.float32,
                            device=device,
                        ).unsqueeze(0)
                if dataset.config.alignment_teacher_weight > 0 and alignment_teacher:
                    candidate_video_ids = [dataset.video_ids[idx] for idx in candidate_indices]
                    alignment_bonus = _alignment_bonus(row["query"], candidate_video_ids, alignment_teacher)
                    if np.any(alignment_bonus):
                        alignment_weight = dataset.config.alignment_teacher_weight
                        if dataset.config.query_aware_fusion:
                            alignment_weight *= _query_fusion_scale(row["query"])
                        logits = logits + alignment_weight * torch.tensor(
                            alignment_bonus,
                            dtype=torch.float32,
                            device=device,
                        ).unsqueeze(0)
                loss = F.cross_entropy(logits, torch.zeros(1, dtype=torch.long, device=device))

                candidate_video_ids = [dataset.video_ids[idx] for idx in candidate_indices]
                if (
                    dataset.config.component_alignment_weight > 0
                    and teacher_reliability > 0
                    and teacher_entry is not None
                ):
                    component_scores = _component_alignment_scores(teacher_entry, candidate_video_ids)
                    if np.any(component_scores > 0):
                        component_tensor = torch.tensor(component_scores, device=device, dtype=torch.float32)
                        component_dist = F.softmax(
                            component_tensor / max(dataset.config.teacher_temperature, 1e-4),
                            dim=-1,
                        )
                        component_log_probs = F.log_softmax(logits.squeeze(0), dim=-1)
                        loss = loss + (
                            dataset.config.component_alignment_weight * teacher_reliability
                        ) * F.kl_div(component_log_probs, component_dist, reduction="batchmean")

                if teacher_entry and teacher_entry.similarity_targets and dataset.config.similarity_teacher_weight > 0 and teacher_reliability > 0:
                    teacher_scores = []
                    student_positions = []
                    teacher_lookup = _teacher_score_lookup(teacher_entry)
                    positive_teacher_score = _teacher_positive_score(teacher_entry, gt_video_id)
                    for position, idx_candidate in enumerate(candidate_indices):
                        video_id = dataset.video_ids[idx_candidate]
                        match = teacher_lookup.get(video_id)
                        if match is None and video_id == gt_video_id and positive_teacher_score is not None:
                            match = float(positive_teacher_score)
                        if match is None:
                            continue
                        teacher_scores.append(float(match))
                        student_positions.append(position)
                    if teacher_scores:
                        teacher_temperature = _resolve_teacher_temperature(dataset.config, teacher_entry)
                        teacher_tensor = torch.tensor(teacher_scores, device=device, dtype=torch.float32)
                        teacher_dist = F.softmax(teacher_tensor / max(teacher_temperature, 1e-4), dim=-1)
                        student_logits = logits.squeeze(0)[student_positions]
                        student_log_probs = F.log_softmax(student_logits, dim=-1)
                        loss = loss + (dataset.config.similarity_teacher_weight * teacher_reliability) * F.kl_div(student_log_probs, teacher_dist, reduction="batchmean")

                if teacher_entry and teacher_entry.listwise_targets and dataset.config.rerank_teacher_weight > 0 and teacher_reliability > 0:
                    listwise_positions: list[int] = []
                    listwise_weights: list[float] = []
                    candidate_index_map = {idx: pos for pos, idx in enumerate(candidate_indices)}
                    for rank, target in enumerate(teacher_entry.listwise_targets, start=1):
                        idx = dataset.video_id_to_index.get(target.video_id)
                        if idx is None or idx not in candidate_index_map:
                            continue
                        listwise_positions.append(candidate_index_map[idx])
                        listwise_weights.append(1.0 / float(rank))
                    if listwise_positions:
                        weight_tensor = torch.tensor(listwise_weights, device=device, dtype=torch.float32)
                        weight_tensor = weight_tensor / weight_tensor.sum().clamp_min(1e-6)
                        listwise_logits = logits.squeeze(0)[listwise_positions]
                        listwise_log_probs = F.log_softmax(listwise_logits, dim=-1)
                        loss = loss + (dataset.config.rerank_teacher_weight * teacher_reliability) * (-(weight_tensor * listwise_log_probs).sum())
                        if dataset.config.teacher_pairwise_weight > 0 and len(listwise_positions) >= 2:
                            pair_losses: list[torch.Tensor] = []
                            max_pairs = min(len(listwise_positions) - 1, 4)
                            for pair_idx in range(max_pairs):
                                margin = 0.01 * float(max_pairs - pair_idx)
                                pair_losses.append(
                                    F.relu(margin - (listwise_logits[pair_idx] - listwise_logits[pair_idx + 1]))
                                )
                            if pair_losses:
                                loss = loss + (dataset.config.teacher_pairwise_weight * teacher_reliability) * torch.stack(pair_losses).mean()

                if dataset.config.teacher_pairwise_weight > 0 and len(candidate_indices) > 1:
                    explicit_preferences = _teacher_pairwise_preferences(teacher_entry)
                    candidate_position = {
                        dataset.video_ids[idx]: pos
                        for pos, idx in enumerate(candidate_indices)
                    }
                    preference_losses: list[torch.Tensor] = []
                    for positive_id, negative_id, margin, pair_weight in explicit_preferences[:8]:
                        pos_idx = candidate_position.get(positive_id)
                        neg_idx = candidate_position.get(negative_id)
                        if pos_idx is None or neg_idx is None:
                            continue
                        preference_losses.append(
                            float(pair_weight) *
                            F.relu(
                                float(margin)
                                - logits.squeeze(0)[pos_idx]
                                + logits.squeeze(0)[neg_idx]
                            )
                        )
                    if preference_losses:
                        loss = loss + (
                            dataset.config.teacher_pairwise_weight * max(teacher_reliability, 0.5)
                        ) * torch.stack(preference_losses).mean()

                    gt_position = 0
                    gt_logit = logits.squeeze(0)[gt_position]
                    negative_logits = logits.squeeze(0)[1: min(len(candidate_indices), 1 + dataset.config.hard_negatives)]
                    if negative_logits.numel() > 0:
                        pairwise_margin = max(float(dataset.config.false_negative_margin), 0.03)
                        hard_pairwise_loss = F.relu(pairwise_margin - gt_logit + negative_logits).mean()
                        loss = loss + (
                            dataset.config.teacher_pairwise_weight * max(teacher_reliability, 0.5)
                        ) * hard_pairwise_loss

                proto_bonus = _prototype_bonus(row["query"], prototype_memory)
                if proto_bonus > 0 and dataset.config.prototype_weight > 0:
                    loss = loss - dataset.config.prototype_weight * loss.new_tensor(proto_bonus * 0.05)

                prototype_teacher_bonus = _prototype_term_bonus(row["query"], teacher_entry)
                if prototype_teacher_bonus > 0 and dataset.config.prototype_teacher_weight > 0 and teacher_reliability > 0:
                    loss = loss - (dataset.config.prototype_teacher_weight * teacher_reliability) * loss.new_tensor(prototype_teacher_bonus * 0.08)

                structured_prototype_bonus = _structured_prototype_bonus(row["query"], teacher_entry)
                if structured_prototype_bonus > 0 and dataset.config.structured_prototype_weight > 0 and teacher_reliability > 0:
                    loss = loss - (dataset.config.structured_prototype_weight * teacher_reliability) * loss.new_tensor(structured_prototype_bonus * 0.12)

                constraint_bonus = _constraint_bonus(row["query"], constraint_memory)
                if constraint_bonus > 0 and dataset.config.frame_teacher_weight > 0:
                    loss = loss - dataset.config.frame_teacher_weight * loss.new_tensor(constraint_bonus * 0.03)

                if dataset.config.late_interaction_weight > 0 and hard_indices:
                    hard_matrix = video_matrix[hard_indices[: min(3, len(hard_indices))]]
                    hard_max_matrix = video_max_matrix[hard_indices[: min(3, len(hard_indices))]]
                    margin_scores = adapter.score_video(
                        adapted[local_idx : local_idx + 1],
                        hard_matrix,
                        hard_max_matrix,
                        cross_modal_video_weight=dataset.config.cross_modal_video_weight,
                    )
                    loss = loss + dataset.config.late_interaction_weight * margin_scores.mean() * 0.02

                losses.append(loss)

            if not losses:
                continue
            batch_loss = torch.stack(losses).mean()
            optimizer.zero_grad(set_to_none=True)
            batch_loss.backward()
            optimizer.step()
            running_losses.append(float(batch_loss.item()))
            progress.set_postfix({"loss": f"{np.mean(running_losses[-10:]):.4f}"})

    stats = {
        "train_loss": round(float(np.mean(running_losses)), 6) if running_losses else 0.0,
        "epochs": dataset.config.epochs,
        "train_queries": len(train_rows),
    }
    return adapter, stats


@torch.no_grad()
def evaluate_adapter(
    dataset: RetrievalLearningDataset,
    eval_rows: list[dict[str, Any]],
    adapter: TextResidualAdapter | None = None,
    semantic_memory: dict[str, Any] | None = None,
    alignment_teacher: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from src.evaluation.metrics import compute_metrics

    device = dataset.config.device if torch.cuda.is_available() else "cpu"
    query_matrix_np = dataset.encode_queries(eval_rows)
    video_tensor = torch.tensor(dataset.video_matrix, dtype=torch.float32, device=device)
    video_max_tensor = torch.tensor(dataset.video_max_matrix, dtype=torch.float32, device=device)
    video_multiview = (
        torch.tensor(dataset.video_multiview_matrix, dtype=torch.float32, device=device)
        if dataset.video_multiview_matrix is not None else None
    )
    if adapter is not None:
        adapter = adapter.to(device)
        adapter.eval()

    ranks: list[int] = []
    batch_size = max(1, int(dataset.config.eval_batch_size))
    component_cache: dict[str, torch.Tensor] = {}
    for start in range(0, len(eval_rows), batch_size):
        end = min(start + batch_size, len(eval_rows))
        batch_rows = eval_rows[start:end]
        query_tensor = torch.tensor(query_matrix_np[start:end], dtype=torch.float32, device=device)
        if adapter is not None:
            query_tensor = adapter(query_tensor)
            scores = adapter.score_video(
                query_tensor,
                video_tensor,
                video_max_tensor,
                cross_modal_video_weight=dataset.config.cross_modal_video_weight,
            )
            if dataset.config.multiview_weight > 0 and video_multiview is not None:
                multiview_scores = adapter.score_multiview(
                    query_tensor,
                video_multiview,
                pooling=dataset.config.multiview_pooling,
                temperature=dataset.config.multiview_temperature,
                temporal_adapter_weight=dataset.config.video_temporal_adapter_weight,
            )
                if multiview_scores is not None:
                    if dataset.config.query_aware_fusion:
                        weights = torch.tensor(
                            [_query_fusion_scale(row["query"]) for row in batch_rows],
                            dtype=torch.float32,
                            device=device,
                        ).unsqueeze(1)
                        scores = scores + dataset.config.multiview_weight * weights * multiview_scores
                    else:
                        scores = scores + dataset.config.multiview_weight * multiview_scores
        else:
            query_tensor = F.normalize(query_tensor, dim=-1)
            scores = query_tensor @ video_tensor.T
            if dataset.config.multiview_weight > 0 and video_multiview is not None:
                raw_view_scores = torch.einsum("bd,nvd->bnv", query_tensor, video_multiview)
                if dataset.config.multiview_pooling == "attention":
                    weights = F.softmax(
                        raw_view_scores / max(float(dataset.config.multiview_temperature), 1e-4),
                        dim=-1,
                    )
                    view_scores = (weights * raw_view_scores).sum(dim=-1)
                else:
                    view_scores = raw_view_scores.max(dim=-1).values
                if dataset.config.query_aware_fusion:
                    weights = torch.tensor(
                        [_query_fusion_scale(row["query"]) for row in batch_rows],
                        dtype=torch.float32,
                        device=device,
                    ).unsqueeze(1)
                    scores = scores + dataset.config.multiview_weight * weights * view_scores
                else:
                    scores = scores + dataset.config.multiview_weight * view_scores

        scores = scores.clone()
        if dataset.config.component_view_weight > 0 and video_multiview is not None:
            for local_idx, row in enumerate(batch_rows):
                component_scores = _component_view_scores(
                    clip_bundle=dataset.clip_bundle,
                    query_text=row["query"],
                    multiview_video=video_multiview,
                    device=device,
                    cache=component_cache,
                )
                if component_scores is not None:
                    cv_weight = dataset.config.component_view_weight
                    if dataset.config.query_aware_fusion:
                        cv_weight *= _query_fusion_scale(row["query"])
                    scores[local_idx] = scores[local_idx] + cv_weight * component_scores

        if semantic_memory and dataset.config.memory_augmented_weight > 0:
            for local_idx, row in enumerate(batch_rows):
                memory_bonus = _memory_augmented_bonus(row["query"], dataset.video_ids, semantic_memory)
                if np.any(memory_bonus):
                    scores[local_idx] = scores[local_idx] + dataset.config.memory_augmented_weight * torch.tensor(
                        memory_bonus,
                        dtype=torch.float32,
                        device=device,
                    )
        if alignment_teacher and dataset.config.alignment_teacher_weight > 0:
            for local_idx, row in enumerate(batch_rows):
                alignment_bonus = _alignment_bonus(row["query"], dataset.video_ids, alignment_teacher)
                if np.any(alignment_bonus):
                    alignment_weight = dataset.config.alignment_teacher_weight
                    if dataset.config.query_aware_fusion:
                        alignment_weight *= _query_fusion_scale(row["query"])
                    scores[local_idx] = scores[local_idx] + alignment_weight * torch.tensor(
                        alignment_bonus,
                        dtype=torch.float32,
                        device=device,
                    )

        scores_matrix = scores.detach().cpu().numpy()
        for local_idx, row in enumerate(batch_rows):
            gt_video_id = row["gt_video_id"]
            if gt_video_id not in dataset.video_id_to_index:
                ranks.append(len(dataset.video_ids) + 1)
                continue
            gt_index = dataset.video_id_to_index[gt_video_id]
            row_scores = scores_matrix[local_idx]
            ordering = np.argsort(-row_scores)
            rank = int(np.where(ordering == gt_index)[0][0]) + 1
            ranks.append(rank)

        if device.startswith("cuda"):
            torch.cuda.empty_cache()
    metrics = compute_metrics(ranks)
    return {
        "N": metrics.n,
        "R@1": metrics.r1,
        "R@5": metrics.r5,
        "R@10": metrics.r10,
        "MnR": metrics.mnr,
        "MedR": metrics.medr,
        "ranks": ranks,
    }
