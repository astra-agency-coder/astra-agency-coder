# Independent Review — astra-intro-reel.mp4

- **Reviewer:** astra-brand-designer (Creative), acting as independent video/design reviewer
- **Date:** 2026-11-13 (14:11 local)
- **Subject:** `deliveries/astra-launch/video/` — `astra-intro-reel.mp4`, `astra-reel-thumbnail.png`, `captions.srt`, `captions.vtt`, `script.md`, `audio/*.mp3`
- **Independence:** I did not author or render this deliverable. No input file was modified; only this review was written.
- **Method:** every number below comes from a command I ran against the shipped artifacts:
  - `ffprobe -show_format -show_streams` on the MP4 and each audio stem
  - `ffmpeg -ss <t> -frames:v 1` to extract frames at 1.5 / 5.5 / 10 / 15 / 21 / 26.5 s, plus 10 extra probe times
  - `tesseract` (psm 11 and psm 6, plain + TSV word boxes) for OCR
  - `python3` + Pillow + NumPy for pixel/row profiling, WCAG contrast, and full-video motion analysis (all 852 frames decoded at 30 fps)
  - `ffmpeg volumedetect` / `loudnorm` for audio levels
  - `md5sum` + raw-PCM decode to prove the audio stems are distinct

---

## Findings

### 1. Container & streams — SPEC MET (no issue)
Exact `ffprobe` values on `astra-intro-reel.mp4`:

| Property | Measured | Required | Verdict |
|---|---|---|---|
| Video codec | `h264` (profile High, `avc1`) | h264 | PASS |
| Resolution | **1080 × 1920** | 1080×1920 | PASS |
| Pixel format | `yuv420p` | yuv420p | PASS |
| Frame rate | `30/1` fps (852 frames) | — | PASS |
| Duration | **28.400000 s** | 15–30 s | PASS |
| Audio stream | `aac`, profile LC, stereo, 44100 Hz | aac present | PASS |
| Video bitrate | 306,198 b/s (container total 508,024 b/s) | — | OK |
| Audio bitrate | 192,697 b/s | — | PASS |

**SEVERITY: none.** The technical spec is exactly as declared.

### 2. Extracted frames non-blank, burned-in captions present — PASS
Frames pulled from the encoded MP4 at the requested times; each is non-blank and OCR finds the expected burned-in text:

| Time | Mean / Std / Unique colours | OCR of MP4 frame |
|---|---|---|
| 1.5 s | 40.86 / 38.09 / 9346 | `AUTONOMOUS · AI-RUN`, `Meet the agency that runs itself.` |
| 5.5 s | 43.04 / 35.93 / 11643 | `A digital agency, run by AI agents.`, `Four services. One autonomous team.` |
| 10 s | 39.26 / 27.74 / 7845 | `WHAT WE BUILD`, `Web & app build`, `Web and app builds.` |
| 15 s | 40.88 / 34.63 / 9473 | `WHAT WE BUILD`, `AI automation`, `Video & design`, `Video and design.` |
| 21 s | 41.98 / 32.13 / 10041 | `HOW IT WORKS`, `1 Strategy 2 Build 3 Launch`, `Strategy to launch, end to end, in code.` |
| 26.5 s | 45.44 / 30.73 / 13959 | `AI ASTRA AGENCY`, `Build what's next.`, `@aiastra` |

**SEVERITY: none.** No blank frames; captions are genuinely burned into the picture.

### 3. Safe areas — one MEDIUM, one LOW
Instagram Reels overlays the top ~180 px and bottom ~320 px. I profiled **all 852 frames** (downscaled 180×320):

- **Top 180 px:** max bright(>180) pixels = **0** across all frames; overall max pixel value in that band = 58 (faint starfield texture only). OCR of the top band finds no words. Clean.
- **Bottom 320 px (y ≥ 1600):** 53 frames contain bright caption pixels. The offending item is the 3-line caption of the WHO beat ("AI Astra is a digital agency, run by autonomous AI agents."), active ≈ 3.6–5.33 s. Its caption bar spans **y = 1440 → 1648**, and the lowest text descender reaches **y = 1622** — i.e. **22 px into the reserved bottom-320 band** (x = 415–660).
  - **SEVERITY: MEDIUM.** A caption's last line grazes the Reels UI/caption zone on 53 frames (~1.8 s of runtime). It is only 22 px, but it is exactly the region Reels covers, so the bottom line can be partially obscured.
- **Side margins:** bright pixels in the left/right 40 px = **0** on every sampled frame. Text x-range never exceeds 81–994. Clean.
- `VERIFY.md` states "nothing critical in the bottom ~320 px". That claim is **slightly overstated** — the 22 px descender intrusion contradicts it.
  - **SEVERITY: LOW.**

### 4. Legibility / contrast — PASS
WCAG contrast ratios measured on the actual pixels (luminance method):

| Element | Text RGB | Background RGB | Contrast | Verdict |
|---|---|---|---|---|
| Caption text on dark bar (10 s) | (244,242,252) | (9,15,23) | **17.4 : 1** | Excellent |
| Headline text on bg (10 s) | (255,253,255) | (26,25,26) | **17.35 : 1** | Excellent |
| Thumbnail tagline | (201,176,240) | (13,43,56) | **7.72 : 1** | Good |

All well above the 4.5:1 (normal text) and 3:1 (large text) thresholds.

**SEVERITY: none.**

### 5. Thumbnail — PASS on spec, LOW on safe area
`astra-reel-thumbnail.png`: Pillow `verify()` OK, format PNG, **exactly 1080 × 1920**, non-blank (3687 distinct colours, mean 50.49 / std 51.82). OCR reads the lockup clearly: `AI ASTRA AGENCY`, `Build what's next.`, and the four services `WEB & APP · AI AUTOMATION · VIDEO & DESIGN · DIGITAL PRODUCTS`. Title/legibility is good.

- Top-180 band: 0 bright pixels. Side 40 px margins: 0 bright pixels.
- **Bottom 320 band:** the services row sits at **y = 1628–1653**, inside the reserved band.
  - **SEVERITY: LOW.** A cover/thumbnail is also shown in the feed grid (where the bottom band does not apply), so the risk is limited; but if this PNG is used as the Reels cover frame, the services line sits in the UI zone.

### 6. Audio honesty — HONEST (PASS)
- Three stems exist: `voice.mp3`, `music_bed.mp3`, `audio_final.mp3` (each 28.447 s, CBR 192 kb/s).
- They are **distinct**, not copies: md5 of the raw decoded PCM differs (voice `7ad06cac…`, music `1db8d368…`, final `a524564d…`). Identical file sizes are a CBR coincidence.
- Synthesis is declared **plainly and repeatedly**: `script.md` ("Voice synthetic (`espeak-ng`)", "Music is synthetic … not licensed music and must not be represented as such"), `VERIFY.md` §6, and the render source `render_reel.py` (`subprocess.run(["espeak-ng", ...])` at line 126; music/SFX built with `numpy` sine/`rng.normal`). `espeak-ng` is installed on the box.
- Independent spectral check is consistent with synthetic speech over synthetic music: voice centroid ≈ **1878 Hz**, energy modulation CV **1.19** (speech-like); music centroid ≈ **3048 Hz**, flatter envelope (CV 0.87).
- Measured MP4 audio loudness: integrated **−14.94 LUFS**, true peak **−1.32 dBTP** — matches `VERIFY.md` exactly and is on-target for social delivery.

**SEVERITY: none.** No overstatement found; the synthetic-voice and unlicensed-music limitations are stated honestly.

### 7. Craft / coherence — one MEDIUM
- The reel is a coherent 5-beat 28 s intro (hook → who → offer → how → CTA) and **does state what the company offers**: web & app build, AI automation, video & design, digital products — all four appear as on-screen cards and in the burned-in captions. The tagline "Build what's next." and the handle `@aiastra` land at the end. Content requirement is met.
- **Motion:** I decoded all 852 frames. **696 / 851 frame transitions (81.8 %) are near-static** (mean abs diff < 0.15/255). At full 1080×1920 resolution inside a "static" window (6.5 s), only **1–11 pixels** change between consecutive frames — the picture is genuinely frozen, not just slow. Motion occurs only at the cut points (~0.57, 3.4–3.6, 5.3, 8.5–8.7, 16.7, 19.6–20.0, 21.6, 24.0 s).
  - **SEVERITY: MEDIUM.** The deliverable is effectively a **5-scene static slideshow with hard cuts** — no text animation, no animated starfield/particles, no transitions, no motion graphics. For an Instagram Reel this is a noticeable craft weakness (reels reward motion) and the render source confirms a static-frame pipeline.
- **Pacing:** the OFFER beat holds a single frozen layout for ~8.6–19.4 s (three near-identical static service states). Longest static run ≈ 2.4 s, but they chain back-to-back, so the middle of the reel feels still.
  - **SEVERITY: LOW** (sub-issue of the motion finding).

---

## What passes
- Exact technical spec: h264 / 1080×1920 / yuv420p / 30 fps / 28.400 s / AAC-LC stereo 44.1 kHz. ✔
- All extracted frames non-blank; burned-in captions verified present by OCR at every requested time. ✔
- Caption and headline contrast excellent (17.4:1 and 17.35:1); thumbnail tagline 7.72:1. ✔
- Top safe band and both side margins completely clean (0 bright pixels in all 852 frames). ✔
- Thumbnail exactly 1080×1920, opens, non-blank, title legible. ✔
- Audio stems genuinely distinct and correctly declared synthetic (espeak-ng VO + NumPy music); loudness −14.94 LUFS / −1.32 dBTP matches the declaration. ✔
- Sidecar `captions.srt` (8 cues) and `captions.vtt` present and consistent with the burned-in text. ✔
- Coherent, complete 15–30 s intro that names all four services and lands the tagline. ✔

## Summary table

| # | Check | Measured result | Severity |
|---|---|---|---|
| 1 | Container/stream spec | h264, 1080×1920, yuv420p, 30 fps, 28.400 s, AAC-LC stereo | none |
| 2 | Frames + burned-in captions | 6/6 frames non-blank; OCR reads expected captions | none |
| 3a | Top 180 px safe band | 0 bright px across all 852 frames | none |
| 3b | Side 40 px margins | 0 bright px | none |
| 3c | Bottom 320 px safe band | caption descender reaches y=1622 (**22 px intrusion**), 53 frames (~1.8 s) | **MEDIUM** |
| 3d | `VERIFY.md` safe-area claim | "nothing critical in bottom 320px" — contradicted by 3c | LOW |
| 4 | Legibility / contrast | captions 17.4:1; headline 17.35:1; thumb tagline 7.72:1 | none |
| 5 | Thumbnail | 1080×1920, opens, non-blank; services row y=1628–1653 in bottom band | LOW |
| 6 | Audio honesty | stems distinct; synthetic (espeak-ng/NumPy) declared plainly; −14.94 LUFS / −1.32 dBTP | none |
| 7a | Motion / craft | 81.8 % of transitions near-static (full-res: 1–11 px change) — slideshow-style | **MEDIUM** |
| 7b | Pacing | OFFER beat static ~8.6–19.4 s | LOW |

**Highest-severity items:** two MEDIUMs, tied —
1. the WHO-beat caption intrudes 22 px into the Reels bottom safe band (~1.8 s), and
2. the video is 81.8 % static frames (a 5-scene slideshow with hard cuts), which undercuts it as a motion reel.

**No HIGH-severity issues. Nothing is blank, broken, mis-specified, or dishonestly described.**
