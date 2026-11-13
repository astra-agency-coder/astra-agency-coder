# QA Evidence — VIDEO deliverable (adversarial, independent)

- Verifier: `qa-edge-breaker` (Quality dept), independent of the author (`astra-ccr`).
- Target: `deliveries/astra-launch/video/astra-intro-reel.mp4`
- Date: 2026-11-13
- Method: every value below was **recomputed from the raw MP4**. The author's
  `VERIFY.md` and `REVIEW-independent.md` were **not** used as inputs (they were
  read only *after* my measurements, purely to characterize discrepancies).
- Read-only guarantee: no file under `deliveries/` was modified. All scratch
  artifacts were written to `/tmp/qa_video/`. This evidence file is the only
  file created under `deliveries/`.
- Tools (measured): ffmpeg/ffprobe 7.1.5, tesseract 5.5.0, Python 3 + Pillow 11.3.0 + numpy 2.5.4.

## Verdict summary

| ID | Criterion | Result |
|----|-----------|--------|
| V1 | codec H.264, exactly 1080x1920, yuv420p, dur 15–30 s, >=1 audio stream | **PASS** |
| V2 | captions actually burned into picture (my own OCR on MP4 frames) | **PASS** (with timing caveat at 5.5 s — see below) |
| V3 | integrated ~ -14 LUFS; true peak <= -1.0 dBTP | **PASS** (I: -14.9 LUFS, TP: -1.32 dBTP) |
| V4 | strict decode: empty stderr + exit 0; full frame decode clean | **PASS** |

**All four frozen criteria PASS.** No blocker. Anomalies (all non-blocking for
V1–V4) are listed at the end.

---

## V1 — Container & streams (ffprobe)

Command:

```
ffprobe -v error -show_format -show_streams -of json astra-intro-reel.mp4
```

Raw output (trimmed to the fields that matter; full JSON was inspected):

```json
{
  "streams": [
    { "index": 0, "codec_name": "h264", "codec_long_name": "H.264 / AVC",
      "profile": "High", "codec_type": "video", "codec_tag_string": "avc1",
      "width": 1080, "height": 1920, "coded_width": 1080, "coded_height": 1920,
      "pix_fmt": "yuv420p", "level": 40, "field_order": "progressive",
      "r_frame_rate": "30/1", "avg_frame_rate": "30/1",
      "start_time": "0.000000", "duration": "28.400000",
      "bit_rate": "306198", "nb_frames": "852" },
    { "index": 1, "codec_name": "aac", "profile": "LC", "codec_type": "audio",
      "sample_fmt": "fltp", "sample_rate": "44100", "channels": 2,
      "channel_layout": "stereo", "start_time": "0.000000",
      "duration": "28.400000", "bit_rate": "192697", "nb_frames": "1225" }
  ],
  "format": { "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
              "start_time": "0.000000", "duration": "28.400000",
              "size": "1803487", "bit_rate": "508024" }
}
```

Findings:
- codec = **h264** (profile High, tag `avc1`) → PASS
- resolution = **1080 x 1920** (coded 1080x1920) → PASS
- pix_fmt = **yuv420p** → PASS
- duration = **28.400000 s** ∈ [15, 30] → PASS
- audio streams = **1** (aac LC, stereo, 44100 Hz) → PASS

**V1 = PASS.**

---

## V2 — Burned-in captions verified by my own OCR

I did **not** reuse the author's OCR. I decoded frames from the MP4 and ran my
own `tesseract`.

### 2a. Full-frame OCR at the exact times named in the task (1.5, 5.5, 21.0, 26.5 s)

```
ffmpeg -v error -ss <t> -i astra-intro-reel.mp4 -frames:v 1 -y /tmp/qa_video/frames/t_<t>.png
tesseract t_<t>.png stdout --psm 6
```

```
===== t=1.5 =====
AUTONOMOUS - AI-RUN .
_ Meet the agency that runs |
itself.
===== t=5.5 =====
A digital agency, —
_run by AI agents.
| Four services. One autonomous team. |
===== t=21.0 =====
HOW IT WORKS
1 Strategy
2 Build.
3 Launch
Strategy to launch, end to
end, in code.
===== t=26.5 =====
A AT ASTRA AGENCY |
Build what's next. |
@aiastra |
```

All four show burned-in text.

### 2b. Caption-band-only OCR at every SRT cue midpoint (decisive test)

The caption band was located by differencing a caption-on frame (20.8 s) vs a
caption-off frame (22.0 s): the changed rows are **1469–1556** of 1920. I then
cropped rows 1430–1600 and OCR'd each cue at its midpoint.

```
CUE 1 @ 1.4s   EXPECTED: 'Meet the agency that runs itself.'
               OCR(band): 'Meet the agency that runs itself.'
CUE 2 @ 4.48s  EXPECTED: 'AI Astra is a digital agency, run by autonomous AI agents.'
               OCR(band): '| Al Astra is a digital agency, run by autonomous Al anantke -'
CUE 3 @ 9.5s   EXPECTED: 'Web and app builds.'
               OCR(band): '_ Web and app builds.'
CUE 4 @ 12.2s  EXPECTED: 'AI automation.'
               OCR(band): 'Al automation.'
CUE 5 @ 14.8s  EXPECTED: 'Video and design.'
               OCR(band): '_. Video and design.'
CUE 6 @ 17.5s  EXPECTED: 'Digital products.'
               OCR(band): '_ a Digital products.'
CUE 7 @ 20.8s  EXPECTED: 'Strategy to launch, end to end, in code.'
               OCR(band): '_ Strategy to launch, end to end, in code.'
CUE 8 @ 25.2s  EXPECTED: "Astra Agency. Build what's next."
               OCR(band): "Astra Agency. Build what's next."
```

All 8 captions are genuinely burned into the picture. Cue 2's trailing
"AI agents" OCR'd as "Al anantke" (tesseract noise on the small bold font) but
the phrase is unambiguously present ("Al Astra is a digital agency, run by
autonomous ...").

### 2c. Caption on/off timeline vs SRT (0.2 s resolution)

I sampled the video at 5 fps, measured bright pixels in the caption band, and
reconstructed when a caption is on screen:

```
caption-present intervals (measured):
   0.6 -> 2.2     3.6 -> 5.4     8.8 -> 10.4    11.4 -> 13.0
  14.0 -> 15.6   16.8 -> 18.4   20.0 -> 21.6    24.4 -> 26.0
SRT windows (declared):
   0.6 -> 2.2     3.6 -> 5.36    8.7 -> 10.3    11.4 -> 13.0
  14.0 -> 15.6   16.7 -> 18.3   20.0 -> 21.6    24.4 -> 26.0
```

The burned-in captions match the SRT sidecar within one sample (0.2 s).

**V2 = PASS.** Caveat: see Anomaly A1 about the task's suggested 5.5 s probe.

---

## V3 — Audio loudness & true peak

### 3a. loudnorm (single pass, measured input)

```
ffmpeg -hide_banner -i astra-intro-reel.mp4 -af loudnorm=print_format=json -f null -
```

Raw:

```json
{
    "input_i" : "-14.94",
    "input_tp" : "-1.32",
    "input_lra" : "3.80",
    "input_thresh" : "-25.91",
    "output_i" : "-24.39",
    "output_tp" : "-10.64",
    "output_lra" : "3.20",
    "output_thresh" : "-35.30",
    "normalization_type" : "dynamic",
    "target_offset" : "0.39"
}
```

- Integrated loudness **input_i = -14.94 LUFS** (target ≈ -14 LUFS) → PASS
- True peak **input_tp = -1.32 dBTP** (<= -1.0 dBTP) → PASS

### 3b. ebur128 (independent cross-check, peak=true)

```
ffmpeg -hide_banner -i astra-intro-reel.mp4 -af ebur128=peak=true -f null -
```

Raw:

```
  Integrated loudness:
    I:         -14.8 LUFS
    Threshold: -25.7 LUFS
  Loudness range:
    LRA:         3.9 LU
    LRA low:   -17.5 LUFS
    LRA high:  -13.6 LUFS
  True peak:
    Peak:       -1.3 dBFS
```

### 3c. volumedetect + astats

```
ffmpeg -hide_banner -i astra-intro-reel.mp4 -af volumedetect -f null -
  mean_volume: -18.8 dB
  max_volume:  -1.3 dB
  histogram_1db: 172
  histogram_2db: 7021

ffmpeg -hide_banner -i astra-intro-reel.mp4 -af astats=metadata=1 -f null -
  Peak level dB: -1.344092   (ch1)
  Peak level dB: -1.343717   (ch2)
  RMS level dB:  -18.753756
  Flat factor:   0.000000    (no clipping / flat-topped samples)
```

Three independent meters agree: integrated ≈ **-14.8…-14.94 LUFS**, true/sample
peak ≈ **-1.32 dBTP / -1.3 dBFS**. Flat factor 0 confirms no clipped samples.

**V3 = PASS.** (Note: `render.log` recorded an earlier pre-encode `input_tp`
of `-0.45`, which would have failed; the value that is actually in the shipped
MP4 is -1.32 dBTP, so the shipped file passes.)

---

## V4 — Strict-decode corruption scan

### 4a. Required command, stderr captured to file

```
ffmpeg -v error -i astra-intro-reel.mp4 -f null - 2>/tmp/qa_video/v4_stderr.txt
EXIT_CODE=0
stderr bytes: 0
stderr content: (empty)
```

- exit code **0** → PASS
- stderr **empty (0 bytes)** → PASS

### 4b. Full decode of all frames to NULL

```
ffmpeg -v error -i astra-intro-reel.mp4 -map 0:v -f null -
EXIT_CODE=0
stderr: (empty)

ffprobe -v error -count_frames -select_streams v:0 \
        -show_entries stream=nb_read_frames ... astra-intro-reel.mp4
852
```

`nb_frames` (852) == `nb_read_frames` (852). No decode errors printed.

**V4 = PASS.**

---

## Anomalies / secondary findings (non-blocking for V1–V4)

**A1 — Timing caveat on the task's suggested 5.5 s probe (MEDIUM for QA method,
not a deliverable defect).**
Caption cue 2 ("AI Astra is a digital agency…") is declared `3.600 → 5.360 s`.
At **exactly 5.5 s the caption band is empty** (0 bright pixels), i.e. the probe
lands **0.14 s after** the cue ends:

```
t=5.40: caption-band bright(>=200) px = 0
t=5.50: caption-band bright(>=200) px = 0
t=5.60: caption-band bright(>=200) px = 0
```

At 5.5 s the OCR of the full frame returns only the *slide* text ("A digital
agency, run by AI agents. / Four services. One autonomous team.") which is the
persistent scene graphic, **not** the animated caption. The caption phrase is
verifiably burned in at the cue's own window (e.g. 4.48 s, see 2b). Conclusion:
the caption *is* burned in; the 5.5 s probe time is simply mistimed. Any verifier
that naively OCRs only 5.5 s and demands the cue-2 phrase could produce a false
FAIL.

**A2 — Static "freeze" segments (MEDIUM craft issue, not a V-criterion).**
`freezedetect` (n=-60dB, d=2 s) reports two frozen stretches:

```
freeze_start: 5.366667   freeze_duration: 3.133333   freeze_end: 8.5
freeze_start: 21.866667  freeze_duration: 2.133333   freeze_end: 24.0
```

Pixel-diff confirms consecutive frames are essentially identical inside these
windows (max diff 8–19/255, mean diff < 0.003). The deliverable is effectively a
5-scene **static slideshow with hard cuts** (~5.3 s of fully frozen picture). For
a social "reel" this is a noticeable lack of motion, but it is not part of the
frozen V1–V4 criteria.

**A3 — Audio/video duration: consistent.**
Both streams report `duration = 28.400000 s`; no mismatch. First audio packet
PTS is `-0.023220` (typical AAC encoder priming delay, harmless).

**A4 — Constant frame rate, monotonic timestamps.**
All 852 frame deltas ∈ {0.033333, 0.033334 s} (i.e. 30 fps CFR); PTS strictly
increasing, no negative/zero deltas, no gaps. Not VFR. First PTS 0.000000,
last 28.366667.

**A5 — No black frames, no silent audio.**
`blackdetect` (d=0.1, pix_th=0.10) → no output. `silencedetect` (n=-50dB,
d=1.0) → no output. Audio is stereo with real content (mean -18.8 dB).

**A6 — Safe-area bands (Instagram Reels overlays).**
Independent 852-frame scan at 180x320:
- top 180 px: max bright pixels = **0** across all frames (clean)
- bottom 320 px: max **24** bright px, present on **53 frames** (~1.8 s)

This independently reproduces the author's note that the 3-line cue-2 caption
grazes the reserved bottom band by ~22 px. Cosmetic/UI risk only; not a V-criterion.

---

## Honest limitations of this test

- Loudness/true-peak are measured with ffmpeg's `loudnorm`/`ebur128`/`astats`.
  `input_tp` is ffmpeg's true-peak estimator; I cross-checked with `ebur128`
  sample peak (-1.3 dBFS) and `astats` (-1.344 dBFS). All agree and all are
  below -1.0, so the verdict is robust, but this is not a certified ITU-R
  BS.1770-4 hardware meter.
- OCR is a heuristic; tesseract mis-reads the small bold caption font
  occasionally (e.g. "AI agents" → "Al anantke"). I compensated by OCR'ing the
  cropped caption band and by an independent pixel-brightness timeline; the
  burned-in claim is supported by both.
- "Captions burned in" is verified at cue midpoints and by a 5 fps presence
  timeline. Sub-200 ms per-cue onset/offset precision was not attempted.
- Freeze/black/silence thresholds are ffmpeg defaults chosen by me; different
  thresholds could classify the static scenes differently (but the segments are
  visually frozen, confirmed by pixel diff).
- I read the author's VERIFY.md/REVIEW-independent.md only after measuring, to
  characterize discrepancies; no author value was used as an input.

## Reproduction steps (copy/paste)

```
cd /workspace/project/deliveries/astra-launch/video/
ffprobe -v error -show_format -show_streams -of json astra-intro-reel.mp4
ffmpeg -v error -i astra-intro-reel.mp4 -f null - 2>/tmp/qa_video/v4_stderr.txt ; echo $? ; wc -c </tmp/qa_video/v4_stderr.txt
ffmpeg -hide_banner -i astra-intro-reel.mp4 -af loudnorm=print_format=json -f null -
ffmpeg -hide_banner -i astra-intro-reel.mp4 -af ebur128=peak=true -f null -
ffmpeg -v error -ss 4.48 -i astra-intro-reel.mp4 -frames:v 1 -y /tmp/qa_video/cue2.png
# crop rows 1430-1600, upscale, then:  tesseract <png> stdout --psm 6
```
