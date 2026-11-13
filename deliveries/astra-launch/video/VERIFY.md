# Video deliverables — verification

Generated 2026-11-13T14:02:12Z by `video/verify.py` (Creative / `astra-ccr`).

## 1. Container & streams — `ffprobe`

- File: `astra-intro-reel.mp4` — 1.72 MiB
- Container: `mov,mp4,m4a,3gp,3g2,mj2`
- **Duration: 28.400 s** (required 15–30 s)
- Video: `h264` profile `High`, **1080×1920**, `yuv420p`, 30/1 fps, 306 kb/s
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
            "bit_rate": "306198"
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
        "size": "1803487",
        "bit_rate": "508024"
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
| 1.5s | “Meet the agency” | “fe  AUTONOMOUS - AI-RUN  Meet the agency that runs itself. … | PASS |
| 5.5s | “run by AI agents” | A digital agency, _run by AI agents.  Four services. One aut… | PASS |
| 21.0s | “Strategy” | HOW IT WORKS  1 Strategy 2 Build 3 Launch  Strategy to launc… | PASS |
| 26.5s | “Build what's next” | A AT ASTRA AGENCY | Build what's next.  @aiastra Estimating … | PASS |

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
- Distinct colours: **3687** (non-blank)

## 6. Render evidence

- Timeline frames retained for evidence: **8** (`frames/` — every 120th of 852 frames at 30 fps)
- Audio stems (MP3, synthetic): `audio/voice.mp3` (espeak-ng VO), `audio/music_bed.mp3` (NumPy music + SFX), `audio/audio_final.mp3` (loudness-normalised mix)
- Build scripts: `render_reel.py` (pipeline), `script.md` (script)

## Result

**ALL CHECKS PASSED**

