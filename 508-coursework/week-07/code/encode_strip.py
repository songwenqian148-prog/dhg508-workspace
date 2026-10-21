"""Encode the field-strip frames into an MP4.

Blender's in-process FFmpeg writes an empty container on this machine, so the
frames are rendered as PNGs (`field_strip.py --frames`) and encoded here with the
ffmpeg binary that ships inside `imageio-ffmpeg`.

Usage:
    python code/encode_strip.py
    python code/encode_strip.py --frames artifacts/frames_strip --out artifacts/video/field_strip.mp4 --fps 30
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", default="artifacts/frames_strip")
    ap.add_argument("--out", default="artifacts/video/field_strip.mp4")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--pattern", default="strip_%04d.png")
    ap.add_argument("--crf", default="20")
    args = ap.parse_args()

    try:
        import imageio_ffmpeg
    except ImportError:
        print("imageio-ffmpeg is missing: python -m pip install imageio-ffmpeg", file=sys.stderr)
        return 1

    frames_dir = ROOT / args.frames
    out = ROOT / args.out
    frames = sorted(frames_dir.glob("strip_*.png"))
    frames = [f for f in frames if f.stat().st_size > 0]
    if len(frames) < 10:
        print(f"only {len(frames)} frames in {frames_dir}", file=sys.stderr)
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg, "-y",
        "-framerate", str(args.fps),
        "-i", str(frames_dir / args.pattern),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", args.crf,
        "-movflags", "+faststart",
        str(out),
    ]
    print(f"{len(frames)} frames -> {out.relative_to(ROOT)}")
    subprocess.run(cmd, check=True)
    print(f"wrote {out} ({out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
