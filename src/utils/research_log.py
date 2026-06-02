from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_MD_PATH = PROJECT_ROOT / "RESEARCH_LOG.md"
LOG_JSONL_PATH = PROJECT_ROOT / "RESEARCH_LOG.jsonl"

THEORY_REFERENCES: dict[str, dict[str, str]] = {
    "viclip_iclr2024": {
        "title": "ViCLIP / InternVid",
        "venue": "ICLR 2024",
        "url": "https://openreview.net/forum?id=MLBdiWu4Fw",
        "note": "Use a strong video-text teacher while keeping the student retrieval path cheap.",
    },
    "teachclip_cvpr2024": {
        "title": "Holistic Features are almost Sufficient for Text-to-Video Retrieval",
        "venue": "CVPR 2024",
        "url": "https://openaccess.thecvf.com/content/CVPR2024/html/Tian_Holistic_Features_are_almost_Sufficient_for_Text-to-Video_Retrieval_CVPR_2024_paper.html",
        "note": "Distill stronger supervision into a cheap retrieval student and improve within a candidate-limited setup.",
    },
    "mv_adapter_cvpr2024": {
        "title": "MV-Adapter: Multimodal Video Transfer Learning for Video Text Retrieval",
        "venue": "CVPR 2024",
        "url": "https://openaccess.thecvf.com/content/CVPR2024/html/Jin_MV-Adapter_Multimodal_Video_Transfer_Learning_for_Video_Text_Retrieval_CVPR_2024_paper.html",
        "note": "Parameter-efficient adaptation should account for video, language, and alignment transfer gaps.",
    },
    "sentence_component_cvprw2024": {
        "title": "Leveraging Generative Language Models for Weakly Supervised Sentence Component Analysis in Video-Language Joint Learning",
        "venue": "CVPRW 2024",
        "url": "https://openaccess.thecvf.com/content/CVPR2024W/MULA/html/Ibn_Abdul_Hakim_Leveraging_Generative_Language_Models_for_Weakly_Supervised_Sentence_Component_Analysis_CVPRW_2024_paper.html",
        "note": "Query component awareness can improve fine-grained retrieval without jumping to a heavy online LLM pipeline.",
    },
    "fine_grained_accv2024": {
        "title": "Beyond Coarse-Grained Matching in Video-Text Retrieval",
        "venue": "ACCV 2024",
        "url": "https://openaccess.thecvf.com/content/ACCV2024/html/Chen_Beyond_Coarse-Grained_Matching_in_Video-Text_Retrieval_ACCV_2024_paper.html",
        "note": "Validation should stress subtle semantics instead of relying only on coarse benchmark wins.",
    },
    "discovla_cvpr2025": {
        "title": "DiscoVLA: Discrepancy Reduction in Vision, Language, and Alignment for Parameter-Efficient Video-Text Retrieval",
        "venue": "CVPR 2025",
        "url": "https://openaccess.thecvf.com/content/CVPR2025/html/Shen_DiscoVLA_Discrepancy_Reduction_in_Vision_Language_and_Alignment_for_Parameter-Efficient_CVPR_2025_paper.html",
        "note": "Language-side and alignment-side adaptation matter in addition to video-side transfer.",
    },
    "tokenbinder_wacv2025": {
        "title": "TokenBinder: Text-Video Retrieval with One-to-Many Alignment Paradigm",
        "venue": "WACV 2025",
        "url": "https://openaccess.thecvf.com/content/WACV2025/papers/Zhang_TokenBinder_Text-Video_Retrieval_with_One-to-Many_Alignment_Paradigm_WACV_2025_paper.pdf",
        "note": "One-to-many candidate comparison is useful for distinguishing near-neighbor videos and improving top-1 retrieval.",
    },
    "fluxvit_iccv2025": {
        "title": "Make Your Training Flexible: Towards Deployment-Efficient Video Models",
        "venue": "ICCV 2025",
        "url": "https://github.com/OpenGVLab/FluxViT",
        "note": "Dynamic token and view selection motivates stronger multiview feature selection under fixed compute.",
    },
    "mama_arxiv2026": {
        "title": "Video Understanding: Through A Temporal Lens",
        "venue": "arXiv 2026",
        "url": "https://researchtrend.ai/papers/2602.00683",
        "note": "Noise-robust contrastive learning and LVLM-augmented annotations motivate cautious replay and teacher filtering.",
    },
}


def _ensure_log_files() -> None:
    if not LOG_MD_PATH.exists():
        header = [
            "# Research Log",
            "",
            "This log records key experiment steps, leakage-prevention decisions, and theory support used in this repository.",
            "",
            "## Core Plan",
            "",
            "1. Use a train/dev/test-safe protocol and stop tuning on the 1kA test split.",
            "2. Keep the retrieval path lightweight and improve with teacher-guided, candidate-limited adaptation.",
            "3. Prefer parameter-efficient text-side updates before heavier frame-level or MLLM expansion.",
            "",
            "## Core References",
            "",
        ]
        for ref in THEORY_REFERENCES.values():
            header.append(f"- {ref['title']} ({ref['venue']}): {ref['url']}")
            header.append(f"  Reason: {ref['note']}")
        LOG_MD_PATH.write_text("\n".join(header) + "\n", encoding="utf-8")

    if not LOG_JSONL_PATH.exists():
        LOG_JSONL_PATH.write_text("", encoding="utf-8")


def append_research_log(
    *,
    step: str,
    summary: str,
    decisions: list[str] | None = None,
    citations: list[str] | None = None,
    artifacts: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    _ensure_log_files()
    timestamp = datetime.now().isoformat(timespec="seconds")
    decisions = decisions or []
    citations = citations or []
    artifacts = artifacts or []
    extra = extra or {}

    md_lines = [
        "",
        f"## {timestamp} | {step}",
        "",
        summary,
        "",
    ]
    if decisions:
        md_lines.append("Decisions:")
        for item in decisions:
            md_lines.append(f"- {item}")
        md_lines.append("")
    if citations:
        md_lines.append("Theory Support:")
        for key in citations:
            ref = THEORY_REFERENCES.get(key)
            if ref is None:
                md_lines.append(f"- {key}")
            else:
                md_lines.append(f"- {ref['title']} ({ref['venue']}): {ref['url']}")
                md_lines.append(f"  Reason: {ref['note']}")
        md_lines.append("")
    if artifacts:
        md_lines.append("Artifacts:")
        for item in artifacts:
            md_lines.append(f"- {item}")
        md_lines.append("")

    with LOG_MD_PATH.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(md_lines))

    payload = {
        "time": timestamp,
        "step": step,
        "summary": summary,
        "decisions": decisions,
        "citations": citations,
        "artifacts": artifacts,
        "extra": extra,
    }
    with LOG_JSONL_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
