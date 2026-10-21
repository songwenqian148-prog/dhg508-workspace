"""Encode the rendered PNG frames into an MP4.

Blender's in-process FFmpeg produced an empty container, so the turntable is
rendered as frames (`--frames-png`) and encoded here with the ffmpeg binary that
ships inside the `imageio-ffmpeg` wheel.

Usage:
    python code/encode_video.py
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FRAMES = ROOT / "artifacts" / "frames"
OUT = ROOT / "artifacts" / "video" / "turntable.mp4"


def main() -> int:
    try:
        import imageio_ffmpeg
    except ImportError:
        print("imageio-ffmpeg is missing: python -m pip install imageio-ffmpeg", file=sys.stderr)
        return 1

    frames = sorted(FRAMES.glob("frame_*.png"))
    frames = [f for f in frames if f.stat().st_size > 0]
    if len(frames) < 10:
        print(f"only {len(frames)} frames found in {FRAMES}", file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg, "-y",
        "-framerate", "10",
        "-i", str(FRAMES / "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        "-movflags", "+faststart",
        str(OUT),
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
