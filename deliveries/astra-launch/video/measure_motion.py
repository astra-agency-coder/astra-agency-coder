#!/usr/bin/env python3
"""Objective motion metric for the intro reel (Creative / astra-ccr).

QA defect D-V1 was "static slideshow, no motion". This measures the mean
absolute frame-to-frame difference (MAFD) of consecutive frames, which is
~0 for a still image held on screen and rises with real camera/overlay motion.

Method: sample the video at a fixed, deterministic cadence, decode each sample
to a small grayscale raster, and average |frame[n] - frame[n-1]| over 0..255.
Reported both globally and per-second so a dead static scene is obvious.

Run:  python3 measure_motion.py <video.mp4> [sample_fps]
"""
from __future__ import annotations

import subprocess
import sys

import numpy as np

GW, GH = 216, 384          # small grayscale raster (keeps the decode cheap)


def _frames(path: str, fps: float, start: float = 0.0, dur: float | None = None) -> np.ndarray:
    cmd = ["ffmpeg", "-v", "error"]
    if start:
        cmd += ["-ss", f"{start}"]
    cmd += ["-i", path]
    if dur is not None:
        cmd += ["-t", f"{dur}"]
    cmd += ["-vf", f"fps={fps},scale={GW}:{GH},format=gray",
            "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    n = len(out) // (GW * GH)
    return np.frombuffer(out[:n * GW * GH], dtype=np.uint8).reshape(n, GH, GW).astype(np.float32)


def mafd(path: str, fps: float = 10.0) -> dict:
    f = _frames(path, fps)
    if len(f) < 2:
        return {"mafd": 0.0, "samples": len(f), "per_second": []}
    d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))          # one value per pair
    per_sec: dict[int, list[float]] = {}
    for i, v in enumerate(d):
        per_sec.setdefault(int(i / fps), []).append(float(v))
    per_second = [round(float(np.mean(per_sec[s])), 3) for s in sorted(per_sec)]
    return {
        "mafd": float(d.mean()),
        "mafd_median": float(np.median(d)),
        "mafd_p90": float(np.percentile(d, 90)),
        "max": float(d.max()),
        "pairs": int(len(d)),
        # a "static pair" is two consecutive frames that are effectively identical
        "static_pair_frac": float((d < 0.02).mean()),
        "static_seconds": int(sum(1 for v in per_second if v < 0.05)),
        "samples": int(len(f)),
        "sample_fps": fps,
        "per_second": per_second,
    }


if __name__ == "__main__":
    p = sys.argv[1]
    fps = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
    m = mafd(p, fps)
    print(f"{p}  MAFD={m['mafd']:.3f}  median={m['mafd_median']:.3f}  "
          f"p90={m['mafd_p90']:.3f}  max={m['max']:.3f}  "
          f"static_pairs={m['static_pair_frac']*100:.1f}%  "
          f"no-motion_seconds={m['static_seconds']}/{len(m['per_second'])}  "
          f"samples={m['samples']}")
    print("per-second MAFD:", m["per_second"])
