from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _metric_triplet(payload: dict[str, Any]) -> dict[str, float]:
    metrics = payload.get("metrics", payload)
    return {
        "R@1": _safe_float(metrics.get("R@1")),
        "R@5": _safe_float(metrics.get("R@5")),
        "R@10": _safe_float(metrics.get("R@10")),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check the quick/full acceptance gate for a stage experiment.")
    parser.add_argument("--candidate_quick", type=str, required=True)
    parser.add_argument("--reference_quick", type=str, required=True)
    parser.add_argument("--candidate_full", type=str, default="")
    parser.add_argument("--reference_full", type=str, default="")
    parser.add_argument("--min_quick_r1", type=float, default=48.0)
    parser.add_argument("--min_r5_gain", type=float, default=1.0)
    parser.add_argument("--min_r10_gain", type=float, default=1.0)
    parser.add_argument("--out", type=str, default="")
    args = parser.parse_args()

    candidate_quick = _metric_triplet(_load_json(args.candidate_quick))
    reference_quick = _metric_triplet(_load_json(args.reference_quick))

    quick_delta = {
        key: round(candidate_quick[key] - reference_quick[key], 4)
        for key in ("R@1", "R@5", "R@10")
    }
    quick_pass = (
        candidate_quick["R@1"] > args.min_quick_r1
        and quick_delta["R@5"] >= args.min_r5_gain
        and quick_delta["R@10"] >= args.min_r10_gain
    )

    full_pass = None
    full_delta = {}
    if args.candidate_full and args.reference_full:
        candidate_full = _metric_triplet(_load_json(args.candidate_full))
        reference_full = _metric_triplet(_load_json(args.reference_full))
        full_delta = {
            key: round(candidate_full[key] - reference_full[key], 4)
            for key in ("R@1", "R@5", "R@10")
        }
        full_pass = all(delta > 0 for delta in full_delta.values())

    payload = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "quick_pass": quick_pass,
        "full_pass": full_pass,
        "candidate_quick": candidate_quick,
        "reference_quick": reference_quick,
        "quick_delta": quick_delta,
        "full_delta": full_delta,
        "policy": {
            "min_quick_r1": args.min_quick_r1,
            "min_r5_gain": args.min_r5_gain,
            "min_r10_gain": args.min_r10_gain,
        },
    }

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
