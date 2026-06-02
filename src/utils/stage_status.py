from __future__ import annotations

from pathlib import Path

from src.utils.research_log import append_research_log


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRENT_STAGE_PATH = PROJECT_ROOT / "CURRENT_STAGE.md"

STAGE_DEFINITIONS = {
    "stage1": {
        "title": "Stage 1: System Optimization",
        "responsibilities": [
            "baseline retrieval",
            "query rewrite",
            "candidate rerank",
        ],
    },
    "stage2": {
        "title": "Stage 2: Representation Enhancement",
        "responsibilities": [
            "teacher-student distillation",
            "hard negative mining",
            "prototype-aware learning",
            "teacher soft labels",
        ],
    },
    "stage3": {
        "title": "Stage 3: Continual Learning and Memory",
        "responsibilities": [
            "prototype memory",
            "hard negative memory",
            "constraint memory",
            "acceptance-gated continual learning",
        ],
    },
}


def write_current_stage(stage_key: str = "stage1", note: str = "") -> None:
    stage = STAGE_DEFINITIONS[stage_key]
    lines = [
        "# Current Stage",
        "",
        f"Current stage: {stage['title']}",
        "",
        "Responsibilities:",
    ]
    for item in stage["responsibilities"]:
        lines.append(f"- {item}")
    if note:
        lines.extend(["", f"Note: {note}"])
    CURRENT_STAGE_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def announce_stage(stage_key: str, note: str = "", log_step: str = "") -> str:
    stage = STAGE_DEFINITIONS[stage_key]
    write_current_stage(stage_key, note)
    message = (
        f"[CURRENT STAGE] {stage['title']} | "
        f"Responsibilities: {', '.join(stage['responsibilities'])}"
    )
    if note:
        message = f"{message} | Note: {note}"
    print(message, flush=True)
    if log_step:
        append_research_log(
            step=log_step,
            summary=f"Entered {stage['title']}.",
            decisions=[
                f"Current responsibilities: {', '.join(stage['responsibilities'])}",
                note or "No extra stage note.",
            ],
        )
    return message
