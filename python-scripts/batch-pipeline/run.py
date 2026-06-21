"""Batch pipeline driver.

Usage:
    python run.py --video videos/B3_V04.json [--out-root <dir>]

Steps:
    1. Load per-video config JSON.
    2. Resolve all media paths against SAI_LIBRARY_ROOT.
    3. Flatten Whisper segment→word list.
    4. build_cut  -> ProRes A+B reels + caption_words.json
    5. captions.render -> alpha ProRes 4444 caption .mov
    6. verify.gate  -> QC dict
    7. package.deliver -> deliverable folder
"""
import argparse, json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import config, cut, captions, verify, package


def main():
    p = argparse.ArgumentParser(description="Batch pipeline driver")
    p.add_argument("--video",    required=True, type=Path, help="Per-video config JSON")
    p.add_argument("--out-root", type=Path, default=None,
                   help="Override output root (default: SAI_LIBRARY_ROOT/08_AI_EDITS/shorts)")
    args = p.parse_args()

    # --- 1. Load JSON ---------------------------------------------------------
    cfg = json.loads(args.video.read_text(encoding="utf-8"))
    batch_n = cfg["batch_n"]
    vid_n   = cfg["vid_n"]
    title   = cfg["title"]

    # --- 2. Resolve media paths -----------------------------------------------
    lib = config.library_root()
    synced_a   = lib / cfg["synced_a"]
    synced_b   = lib / cfg["synced_b"]
    lav_wav    = lib / cfg["lav_wav"]
    words_json = lib / cfg["words_json"]

    # Convert ranges: JSON null -> Python None
    ranges = [
        (r[0], r[1], r[2] if r[2] is not None else None, r[3] if r[3] is not None else None)
        for r in cfg["ranges"]
    ]

    # --- 3. Flatten Whisper segments -> words ---------------------------------
    data  = json.loads(words_json.read_text(encoding="utf-8"))
    words = [w for s in data["segments"] for w in s["words"]]

    # --- 4. Decide work + output roots ----------------------------------------
    out_root = args.out_root  # None means package uses live SAI_LIBRARY_ROOT path
    work_dir = (out_root or lib / "08_AI_EDITS" / "shorts") / "_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    vid_tag = f"B{batch_n}_V{vid_n:02d}"

    # --- 5. Cut ---------------------------------------------------------------
    print(f"\n=== CUT ({vid_tag}) ===")
    cut_res = cut.build_cut(synced_a, synced_b, lav_wav, words, ranges, work_dir, vid_tag)
    print(f"total_s: {cut_res['total_s']:.2f}s  |  {len(ranges)} segments")

    # --- 6. Captions ----------------------------------------------------------
    print(f"\n=== CAPTIONS ===")
    captions_mov = work_dir / f"{vid_tag}_captions.mov"
    captions.render(cut_res["caption_words"], cut_res["a"], captions_mov)

    # --- 7. Verify / gate -----------------------------------------------------
    print(f"\n=== VERIFY ===")
    gate = verify.gate(cut_res["a"], cut_res["b"], lav_wav, cut_res["synced_outs"])
    print(json.dumps(gate, indent=2, default=str))

    # --- 8. Compose _INFO.txt text --------------------------------------------
    info_text = (
        f"Title:    {title}\n"
        f"Lav cam:  {cfg.get('lav', 'B')}-cam\n"
        f"Audio:    B-cam (lav) audio on both angles\n"
        f"Cut len:  {cut_res['total_s']:.2f}s\n"
        f"Segments: {len(ranges)}\n"
    )
    info = {"text": info_text}

    # --- 9. Package -----------------------------------------------------------
    print(f"\n=== PACKAGE ===")
    pkg = package.deliver(
        batch_n, vid_n, title,
        cut_res["a"], cut_res["b"], captions_mov,
        info,
        out_root=out_root,
    )
    print(f"Package: {pkg}")

    # --- 10. Final gate result ------------------------------------------------
    if not gate["passed"]:
        print("\n" + "=" * 60)
        print("  FAILED — verify gate did not pass. Check details above.")
        print("=" * 60)
        sys.exit(1)
    else:
        print(f"\ngate: PASSED")


if __name__ == "__main__":
    main()
