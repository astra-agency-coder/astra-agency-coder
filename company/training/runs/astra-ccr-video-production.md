# Training run — astra-ccr — video-production

- conversation: 999b42cc-0e88-4126-9339-330c8e910b3b
- status: finished
- elapsed_s: 323.1

## Result
# Training Run Report — Creative · video-production

**Manager:** astra-ccr · **Date:** 2026-11-13 · **Nature:** training only (no customer contact / outreach / sales)

## Modules

| Module | Artifact | Check | Result |
|---|---|---|---|
| **V1** Study real videos | `dept-creative:knowledge/video/studies/*.md` (5 files) | 5 videos, each cited by URL; hook/structure/pacing/shot list/audio/CTA | **PASS** |
| **V2** Script | `knowledge/video/script-template.md` | 72 words ÷ 150 wpm ≈ 29s speech in a 45s slot; ~48 effective wpm (sparse, music-supported) | **PASS** |
| **V3** Voice & audio | `work/astra-ccr/video-project/audio/{voice,music_bed,final_mix}.wav` + `voiceover_mix.mp3` | real audio exists; **−14.4 LUFS / TP −1.4 dBTP** (target ≈ −14) | **PASS** |
| **V4** Edit & render | `.../out/astra-from-brief-to-render.mp4` + `subs/captions.{srt,vtt}` | `ffprobe`: H.264 1920×1080, 44.0s, AAC 48k; full decode OK; OCR confirms rendered text | **PASS** |
| **V5** Publish pack | `publish/{thumbnail_16x9.png, poster_16x9.png, thumbnail_9x16.png, ..._9x16.mp4, PUBLISH_PACK.md}` | sizes (1280×720 / 1920×1080 / 1080×1920 / video 1080×1920) all correct | **PASS** |

All artifacts committed and **pushed** to the department repo `astra-agency-coder/dept-creative` (verified via `git ls-tree origin/main`). Run log at `company/training/runs/astra-ccr-video-production.md` (committed + pushed to the company repo).

**V1 videos studied (real, cited):** Nutella 30s (`fH4j38FaLs8`), Cadbury 30s (`mBNBsZdMm-s`), Simply Business 40s (`5DX4-Ww-CZM`), Pepsi 31s (`7vKCq52wWUY`), Specsavers 60s (`OMQiJojeryw`) — metadata, auto-captions and YouTube retention heatmaps read via `yt-dlp`.

## What is now reusable
- 5 cited ad deconstructions + a cross-study synthesis of craft rules.
- A 45s five-beat script template with a word-count/duration rule.
- A **repeatable, code-driven pipeline** (`render_frames.py`, `build_audio.py`, `make_srt.py`, `make_graphics.py`) — swap text/VO and re-run. Documented in `knowledge/video/PIPELINE.md`.

## Open items / blockers (stated plainly)
1. **YouTube media download = HTTP 403** (muxed & progressive). This is access protection; I did **not** bypass it. Studies rely on metadata + auto-captions, so shot lists are marked *"inferred"*. The analysis is real but not frame-by-frame.
2. **Custom-hired specialists were not resolvable** by the `task` tool — it returned `Unknown agent 'astra-video-editor'; Available types: astra-cbdo, astra-ccr, …` (only preset manager types load). Hired `astra-video-editor` + `astra-graphic-designer`, then ran the work myself and retired both. **Recommendation:** register file-based agents with the runtime (or expose a working spawn path) so departments can actually delegate.
3. **VO is a robotic `espeak-ng` placeholder** — must be replaced with a human/neural voice (`audio/voice.wav` is a drop-in) before commercial use.

Nothing failed silently — all five modules produced a real, checked artifact.
