# Video deliverables — verification

Generated 2026-11-13T15:16:46Z by `video/verify.py` (Creative / `astra-ccr`).

## 1. Container & streams — `ffprobe`

- File: `astra-intro-reel.mp4` — 3.16 MiB
- Container: `mov,mp4,m4a,3gp,3g2,mj2`
- **Duration: 28.400 s** (required 15–30 s)
- Video: `h264` profile `High`, **1080×1920**, `yuv420p`, 30/1 fps, 732 kb/s
- Audio: `aac` profile `LC`, 2 ch, 44100 Hz, 192 kb/s

| Check | Result |
|---|---|
| Video codec is H.264 | PASS |
| Resolution is 1080×1920 | PASS |
| Pixel format yuv420p | PASS |
| Frame rate is 30 fps | PASS |
| Has an audio stream (AAC) | PASS |
| Duration in [15,30] s | PASS |

Raw `ffprobe` output:

```json
{
    "programs": [

    ],
    "stream_groups": [

    ],
    "streams": [
        {
            "index": 0,
            "codec_name": "h264",
            "profile": "High",
            "codec_type": "video",
            "width": 1080,
            "height": 1920,
            "pix_fmt": "yuv420p",
            "r_frame_rate": "30/1",
            "duration": "28.400000",
            "bit_rate": "732234"
        },
        {
            "index": 1,
            "codec_name": "aac",
            "profile": "LC",
            "codec_type": "audio",
            "sample_rate": "44100",
            "channels": 2,
            "r_frame_rate": "0/0",
            "duration": "28.400000",
            "bit_rate": "192697"
        }
    ],
    "format": {
        "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
        "duration": "28.400000",
        "size": "3316115",
        "bit_rate": "934116"
    }
}
```

## 2. Audio loudness — `ffmpeg loudnorm` on the encoded audio

- Measured integrated loudness: **-14.94 LUFS** (target −14 LUFS)
- Measured true peak: **-1.32 dBTP** (target ≤ −1 dBTP)
- Loudness normalisation applied via two-pass `loudnorm`: **PASS**

## 3. Burned-in captions — OCR of frames from the encoded MP4

A frame is extracted from the **MP4 itself** at a caption time and OCR'd. If the expected phrase appears, the caption is truly burned into the picture.

| Time | Expected text | OCR of MP4 frame | Result |
|---|---|---|---|
| 1.5s | “Meet the agency” | is  AUTONOMOUS -- AI-RUN  Meet the agency that runs itself. … | PASS |
| 5.5s | “run by AI agents” | A digital agency, run by Al agents.  Four services. 'One aut… | PASS |
| 21.0s | “Strategy” | HOW IT WORKS  1 Strategy  2 Build 3 Launch  Strategy to laun… | PASS |
| 26.5s | “Build what's next” | A AT ASTRA AGENCY  Build what's next.  @aiastra Estimating r… | PASS |

## 4. Sidecar captions — `captions.srt` / `captions.vtt`

- `captions.srt`: **8 cues**, last cue ends at **26.000 s** (within runtime = True)
- `captions.vtt`: present (WEBVTT header ok)

```
1
00:00:00,600 --> 00:00:02,200
Meet the agency that runs itself.

2
00:00:03,600 --> 00:00:05,360
AI Astra is a digital agency, run by autonomous AI agents.

3
00:00:08,700 --> 00:00:10,300
Web and app builds.

4
00:00:11,400 --> 00:00:13,000
AI automation.

5
00:00:14,000 --> 00:00:15,600
Video and design.

6
00:00:16,700 --> 00:00:18,300
Digital products.

7
00:00:20,000 --> 00:00:21,600
Strategy to launch, end to end, in code.

8
00:00:24,400 --> 00:00:26,000
Astra Agency. Build what's next.
```

## 5. Thumbnail / cover — `astra-reel-thumbnail.png`

- Size: **1080×1920** (required 1080×1920) — PASS
- Opens with Pillow and passes `verify()`: **yes**
- Distinct colours: **2837** (non-blank)

## 6. Motion — objective frame-to-frame difference (QA D-V1)

QA defect D-V1 was *“static slideshow, no motion”*. The metric is the **mean absolute frame-to-frame difference (MAFD)** of consecutive frames, sampled at 10 fps into a small grayscale raster: ~0 for a held still, rising with real camera/overlay motion. A *static pair* is two consecutive frames that are effectively identical (MAFD < 0.02).

| Reel | MAFD | median | static pairs | no-motion s |
|---|---|---|---|---|
| **before** (pre-fix, static) | 0.459 | 0.000 | 61.5% | 3/29 |
| **after** (shipped, motion) | 0.620 | 0.222 | 0.0% | 0/29 |

- MAFD 0.459 → 0.620 (**+35%**); static pairs 61.5% → 0.0%
- Every scene has a monotonic Ken-Burns push, a twinkling-star layer, an animated progress bar and staggered cards, so no two frames repeat: **PASS** (no-motion seconds 0/29)

Per-second MAFD (before → after):

```
before: [0.483, 0.474, 0.192, 2.427, 0.78, 0.301, 0.0, 0.0, 1.385, 0.143, 0.108, 0.77, 0.079, 0.301, 0.568, 0.096, 0.776, 0.144, 0.091, 1.238, 0.107, 0.365, 0.0, 0.487, 0.996, 0.406, 0.116, 0.104, 0.167]
after : [0.688, 0.8, 0.519, 2.706, 1.006, 0.521, 0.219, 0.207, 1.578, 0.258, 0.221, 0.879, 0.179, 0.402, 0.656, 0.182, 0.86, 0.22, 0.17, 1.365, 0.34, 0.555, 0.168, 0.668, 1.178, 0.45, 0.233, 0.219, 0.306]
```

## 7. Reels safe area (QA D-V2)

Captions and every piece of critical content must stay out of the Reels UI bands — the bottom 320 px and the top 180 px. This re-runs the renderer's own geometry check against the shipped layout.

- Top safe band: **0–180 px**; bottom safe band: **1600–1920 px** (i.e. bottom 320 px)
- Caption bars bottom out at **y=1560 px** → **360 px** clear of the frame bottom
- Progress bar sits at y=190 px (inside the top band, non-critical)
- Caption boxes checked: 8 — top violations **0**, bottom violations **0** — **PASS**

## 8. Render evidence

- Timeline frames retained for evidence: **8** (`frames/` — every 120th of 852 frames at 30 fps)
- Audio stems (MP3, synthetic): `audio/voice.mp3` (espeak-ng VO), `audio/music_bed.mp3` (NumPy music + SFX), `audio/audio_final.mp3` (loudness-normalised mix)
- Build scripts: `render_reel.py` (pipeline), `script.md` (script)

## Result

**ALL CHECKS PASSED**

