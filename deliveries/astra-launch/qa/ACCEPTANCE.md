# QA — FROZEN ACCEPTANCE CRITERIA (round-2, adversarial)

**Frozen by:** `astra-cqo` (Quality) · **Date:** 2026-11-13T14:25Z
**Rule:** these criteria were written **before** any test was run and are not changed
afterwards to fit the result. A deliverable passes only when **every** criterion is
demonstrably met with raw evidence.

## VIDEO — `deliveries/astra-launch/video/astra-intro-reel.mp4`

| ID | Criterion | Method (must be independent of author) |
|----|-----------|----------------------------------------|
| V1 | Container/streams: H.264, 1080×1920, `yuv420p`, duration ∈ [15,30] s, ≥1 audio stream | `ffprobe -show_streams -show_format` |
| V2 | Captions **actually burned in** the picture | decode frames from the MP4 + **own** OCR (tesseract) — do NOT trust Creative's OCR |
| V3 | Audio: integrated loudness ≈ −14 LUFS; **true peak ≤ −1.0 dBTP** (no clipping) | `ffmpeg loudnorm`/`volumedetect` |
| V4 | Plays in a strict decoder; no corrupt frames | `ffmpeg -v error -i f -f null -` must be **silent**; full decode to NULL, check exit code + stderr |

## WEBSITE — `deliveries/astra-launch/website/` @ public URL

| ID | Criterion | Method |
|----|-----------|--------|
| W1 | Public URL returns HTTP 200 | `curl` the public host, repeated; note stability |
| W2 | Public bytes byte-identical to source file | `md5sum`/`cmp` source vs fetched |
| W3 | HTML valid; no duplicate `id`s; every in-page anchor resolves; every `<img>` has `alt`; heading order sane | own parser (html5lib + ElementTree) |
| W4 | Renders with JS disabled and makes **no external requests** (no CDN/tracker) | static analysis of HTML/CSS/JS refs |
| W5 | Robust to edges: very long text, missing asset, 320 px width | reasoning + CSS/asset audit |

## BRAND — `deliveries/astra-launch/brand/`

| ID | Criterion | Method |
|----|-----------|--------|
| B1 | Every `.svg` parses as XML **and** renders to a non-blank raster | `ElementTree` + `cairosvg` |
| B2 | `astra-brand-sheet.png` opens and is non-blank | Pillow open + `verify()` + distinct colours |
| B3 | Declared WCAG contrast ratios are **true** | re-implement WCAG relative-luminance from scratch; recompute ≥2 pairs |

## Deliverable of this QA task
`deliveries/astra-launch/qa/VERDICT.md` — PASS/FAIL per deliverable + raw evidence, plus a
knowledge note pushed to the Quality department repo.
