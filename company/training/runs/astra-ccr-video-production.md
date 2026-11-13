# Training Run — Creative — video-production

- **Manager:** astra-ccr (Chief Creative Officer — Creative)
- **Curriculum:** `company/training/curricula/video-production.md`
- **Date:** 2026-11-13
- **Nature:** intensive training run. No customer contact, no outreach, no sales.

## Environment (verified)
- `ffmpeg` / `ffprobe` present; Pillow 13.0.0 present.
- Installed during the run: `espeak-ng` (apt), `numpy` (pip), `yt-dlp` (pip), `gtts`/`pyttsx3` (pip).
- `tesseract` present (used to OCR-verify rendered text).

## Module results

| Module | Artifact | Check | Result |
|---|---|---|---|
| V1 Study real videos | `knowledge/video/studies/*.md` (5 files) | 5 videos, each cited by URL, hook/structure/pacing/shot list/audio/CTA | **PASS** |
| V2 Script | `knowledge/video/script-template.md` | word count vs duration (72 words ÷ 150 wpm ≈ 29s speech in a 45s slot) | **PASS** |
| V3 Voice & audio | `work/astra-ccr/video-project/audio/{voice,music_bed,final_mix}.wav`, `voiceover_mix.mp3` | real audio files; loudness −14.4 LUFS / TP −1.4 dBTP | **PASS** |
| V4 Edit & render | `work/astra-ccr/video-project/out/astra-from-brief-to-render.mp4` + `subs/captions.{srt,vtt}` | `ffprobe`: 1920×1080, 44.0s, h264+aac | **PASS** |
| V5 Publish pack | `publish/{thumbnail_16x9.png,poster_16x9.png,thumbnail_9x16.png}`, `publish/astra-from-brief-to-render_9x16.mp4`, `publish/PUBLISH_PACK.md` | correct dimensions (1280×720 / 1920×1080 / 1080×1920), 1080×1920 video | **PASS** |

All artifacts saved to the department repo `astra-agency-coder/dept-creative`
under `knowledge/` and `work/astra-ccr/video-project/`.

## Real commands run (evidence)

### V1 — study (metadata + captions, NOT scraping media)
```bash
python3 -m yt_dlp --skip-download --print "%(id)s|%(title)s|%(duration)s|%(view_count)s" <url>
python3 -m yt_dlp --write-auto-subs --sub-langs en --skip-download <url>   # captions OK
# media download 403 Forbidden (YouTube protection) — NOT bypassed, per policy
```
Videos studied (real, cited):
- Nutella "Always Better Together" 30s — youtube.com/watch?v=fH4j38FaLs8
- Cadbury "Yours Always | Birthday" 30s — youtube.com/watch?v=mBNBsZdMm-s
- Simply Business "Simply the Best" 40s — youtube.com/watch?v=5DX4-Ww-CZM
- Pepsi "The Choice" 31s — youtube.com/watch?v=7vKCq52wWUY
- Specsavers 2024 60s — youtube.com/watch?v=OMQiJojeryw
Real retention heatmaps were read from yt-dlp metadata JSON (100 points each).

### V3 — voice + audio
```bash
espeak-ng -v en-GB -s 150 -p 45 -w audio/lineNN.wav "<line>"   # 8 lines
python3 build_audio.py                                          # music bed + SFX + ducking
ffmpeg -i audio/mix_raw.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 ... audio/final_mix.wav
# verified: Input Integrated -14.4 LUFS, Input True Peak -1.4 dBTP
```

### V4 — render
```bash
python3 render_frames.py     # 660 PNGs @ 15fps, 1920x1080, animated text + crossfades + burned subs
ffmpeg -framerate 15 -i frames/f%05d.png -i audio/final_mix.wav \
  -c:v libx264 -pix_fmt yuv420p -crf 20 -c:a aac -b:a 192k -shortest \
  out/astra-from-brief-to-render.mp4
# ffprobe: h264 1920x1080 r_frame_rate=15/1, aac 48000 2ch, duration=44.000000
# OCR of extracted frames confirmed the rendered text is correct
```

### V5 — publish pack
```bash
ffmpeg -i out/...mp4 -filter_complex "[0:v]scale=1080:1920:...boxblur...[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay" publish/..._9x16.mp4
python3 make_graphics.py     # thumbnail/poster/vertical card via Pillow
# verified sizes: (1280,720) (1920,1080) (1080,1920)
```

## FAILED / blockers (honest record)
1. **YouTube media download = HTTP 403.** yt-dlp could fetch metadata and
   auto-captions but not the video data; both muxed and progressive formats were
   403. This is YouTube's access protection. Per policy I did **not** attempt to
   bypass it. Consequence: the V1 studies use metadata + auto-caption text +
   published retention heatmaps rather than direct frame-by-frame inspection, and
   shot lists are marked "inferred (reconstructed from captions)".
2. **Custom-hired agents are not usable as `task` subagent types.** Hired
   `astra-video-editor` and `astra-graphic-designer`, but the `task` tool rejected
   them: `Unknown agent 'astra-video-editor'. Available types: astra-cbdo,
   astra-ccr, ...` (only the pre-registered manager types work). I executed the
   V4/V5 specialist work myself instead. **Recommendation to CEO:** either
   register specialists with the runtime's `register_agent()` or provide a spawn
   path that resolves file-based agents.
3. **TTS is a synthesised placeholder** (`espeak-ng`, robotic). A human/neural VO
   is required before any commercial use; the pipeline accepts a drop-in
   replacement of `audio/voice.wav`.

## Reusable assets for the department
- `knowledge/video/studies/*.md` — 5 cited ad deconstructions + cross-study synthesis.
- `knowledge/video/script-template.md` — 45s five-beat script template + word-count rule.
- `work/astra-ccr/video-project/` — a **repeatable pipeline**: `render_frames.py`
  (animated frame renderer), `build_audio.py` (generated music bed + ducking),
  `make_srt.py`, `make_graphics.py`. Swap the text/VO and re-run to make a new video.
