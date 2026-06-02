from __future__ import annotations
import json
from pathlib import Path


def read_vid_list(p: Path) -> set[str]:
    return {ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()}


def main():
    root = Path(__file__).resolve().parents[1]
    ann = root / "data" / "annotations" / "msrvtt"
    manifests = root / "data" / "manifests"

    vid_list = ann / "val_list_jsfusion.txt"
    in_manifest = manifests / "msrvtt_fixed.jsonl"
    out_manifest = manifests / "msrvtt_fixed_1kA.jsonl"

    if not vid_list.exists():
        raise FileNotFoundError(f"Missing: {vid_list}")
    if not in_manifest.exists():
        raise FileNotFoundError(f"Missing: {in_manifest}")

    keep_vids = read_vid_list(vid_list)
    print("[OK] keep_vids =", len(keep_vids))

    kept = 0
    total = 0
    seen_vids = set()

    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    with open(in_manifest, "r", encoding="utf-8") as fin, open(out_manifest, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            total += 1
            row = json.loads(line)
            vid = row.get("video_id")
            if vid in keep_vids:
                fout.write(json.dumps(row, ensure_ascii=False) + "\n")
                kept += 1
                seen_vids.add(vid)

    print(f"[OK] kept segments = {kept}/{total}")
    print(f"[OK] unique videos in kept manifest = {len(seen_vids)} (should be 1000)")
    print(f"[DONE] wrote: {out_manifest}")


if __name__ == "__main__":
    main()