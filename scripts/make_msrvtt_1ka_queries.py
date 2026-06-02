from __future__ import annotations
import json
from pathlib import Path


def read_vid_list(p: Path) -> set[str]:
    return {ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()}


def main():
    root = Path(__file__).resolve().parents[1]
    ann = root / "data" / "annotations" / "msrvtt"

    vid_list = ann / "val_list_jsfusion.txt"          # 1000 vids
    in_q = ann / "msrvtt_test_queries.jsonl"          # 50k+
    out_q = ann / "msrvtt_1kA_test_queries.jsonl"     # output

    if not vid_list.exists():
        raise FileNotFoundError(f"Missing: {vid_list}")
    if not in_q.exists():
        raise FileNotFoundError(f"Missing: {in_q}")

    keep_vids = read_vid_list(vid_list)
    print("[OK] keep_vids =", len(keep_vids))

    kept = 0
    total = 0
    seen = set()

    out_q.parent.mkdir(parents=True, exist_ok=True)
    with open(in_q, "r", encoding="utf-8") as fin, open(out_q, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            total += 1
            row = json.loads(line)
            vid = row.get("gt_video_id")
            if vid in keep_vids:
                fout.write(json.dumps({"query": row["query"], "gt_video_id": vid}, ensure_ascii=False) + "\n")
                kept += 1
                seen.add(vid)

    print(f"[OK] kept queries = {kept}/{total}")
    print(f"[OK] unique gt videos covered = {len(seen)} (should be 1000)")
    print(f"[DONE] wrote: {out_q}")


if __name__ == "__main__":
    main()