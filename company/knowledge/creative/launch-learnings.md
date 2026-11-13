# Creative — launch learnings (brand identity + intro Reel)

**Department:** Creative (`astra-ccr`) · **Date:** 2026-11-13 · **Task:** first operational task
**Full note:** dept-creative repo → `knowledge/launch-learnings.md`

## Summary
Shipped the AI ASTRA AGENCY visual identity (mark, lockups, `tokens.json`, brand
sheet) and a 1080×1920 Instagram Reels intro video (`astra-intro-reel.mp4`, 28.4 s,
H.264/AAC, burned-in + sidecar captions, cover thumbnail). All artefacts are real
files verified on disk; an independent reviewer re-measured the shipped files.

## Key learnings
1. Outline wordmarks to `<path>` — removes the font dependency; logos render anywhere.
2. Keep `tokens.json` as the single source of truth; every `sys` colour aliases a
   `ref` token (44 ref→sys aliases, all backed).
3. Measure audio loudness with two-pass `ffmpeg loudnorm`; ship the number
   (−14.94 LUFS / −1.32 dBTP), don't eyeball it.
4. Prove burned-in captions by OCR of the **encoded MP4**, not the render frames.
5. Reels safe areas: keep captions ≤ 2 lines, all text above the bottom ~320 px and
   below the top ~180 px (independent review found a 22 px descender intrusion).
6. Independent review pays off — it caught a dark-on-dark lockup (1.09:1) on the
   brand sheet that author-side checks missed.

## Known limitations (stated plainly)
- Voice is `espeak-ng` (robotic placeholder), not a human VO.
- Brand fonts are DejaVu substitutes pending the licensed faces.
- YouTube media download is 403-blocked; studies use metadata/captions only.
