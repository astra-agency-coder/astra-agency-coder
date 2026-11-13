# Curriculum — Video production (intensive)

Objective: produce competent short videos, learning from real examples online,
covering scripting, voice/audio, editing and rendering.

## Module V1 — Study real videos
- Using the browser, watch/analyze 5 short videos (ads, explainers, product demos).
  For each: hook, structure, pacing, shot list, audio design, call to action.
  Write to `knowledge/video/studies/<video>.md`, citing the URL.

## Module V2 — Script
- Write a 30–60s script: hook (0–3s), problem, solution, proof, CTA.
- Check: word count fits the duration at a natural speaking rate (~150 wpm).

## Module V3 — Voice & audio design
- Produce a voice track. Where TTS is available, synthesize it; otherwise write a
  precise narration + timing sheet. Design the audio: music bed, SFX, levels.
- Check: an actual audio file (wav/mp3) exists, loudness noted (target ≈ -14 LUFS).

## Module V4 — Edit & render (real tools)
- Use `ffmpeg` to assemble a video from generated frames/clips + the audio:
  title card, timed subtitles, transitions, end card. Export H.264 MP4.
- Check: a real `.mp4` exists; `ffprobe` shows expected duration/resolution.

## Module V5 — Publish pack
- Thumbnail, title, description, caption/hashtags, aspect variants (16:9, 9:16).
- Check: files exist; each variant has correct dimensions.

## Acceptance
One finished MP4, its audio, subtitles, thumbnail and publish pack are in the
department repo, all produced with real tools. No file = not done.
