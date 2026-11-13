#!/usr/bin/env python3
"""AI ASTRA AGENCY — intro Reel renderer (Creative / astra-ccr).

End-to-end, code-driven pipeline that produces the deliverables in this folder:

    astra-intro-reel.mp4        1080x1920, H.264/AAC, ~28 s, captions burned in
    astra-reel-thumbnail.png    1080x1920 cover image
    captions.srt / captions.vtt sidecar captions
    audio/*.wav                 synthetic VO, music bed, final loudness-normalised mix
    frames/*.png                the rendered timeline (for reproducibility)

Audio is SYNTHETIC: voice via `espeak-ng`, music/SFX generated in NumPy.
Nothing here is licensed material — see script.md "Limitations".

Run:  python3 render_reel.py            (full render)
      python3 render_reel.py --audio    (audio only, skip frame render)
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
BRAND = HERE.parent / "brand"
T = json.loads((BRAND / "tokens.json").read_text())
REF = T["color"]["ref"]
L, D = T["color"]["sys_resolved"]["light"], T["color"]["sys_resolved"]["dark"]

W, H, FPS = 1080, 1920, 30
DUR = 28.4
SR = 44100
FONT = "/usr/share/fonts/truetype/dejavu/"

OUT = HERE / "astra-intro-reel.mp4"
THUMB = HERE / "astra-reel-thumbnail.png"
FRAMES = HERE / "frames"
AUDIO = HERE / "audio"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def hx(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def fnt(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT + name, size)


def ease(t: float) -> float:
    """Smoothstep 0..1."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def seg(t: float, a: float, b: float) -> float:
    """Progress of t within [a,b] clamped to 0..1."""
    return max(0.0, min(1.0, (t - a) / (b - a))) if b > a else 0.0


# --------------------------------------------------------------------------- #
# audio (synthetic)
# --------------------------------------------------------------------------- #
VO_LINES = [
    (0.6,  "Meet the agency that runs itself."),
    (3.6,  "AI Astra is a digital agency, run by autonomous AI agents."),
    (8.7,  "Web and app builds."),
    (11.4, "AI automation."),
    (14.0, "Video and design."),
    (16.7, "Digital products."),
    (20.0, "Strategy to launch, end to end, in code."),
    (24.4, "Astra Agency. Build what's next."),
]


def _resample(x: np.ndarray, src: int, dst: int) -> np.ndarray:
    if src == dst:
        return x
    n = int(len(x) * dst / src)
    idx = np.linspace(0, len(x) - 1, n)
    return np.interp(idx, np.arange(len(x)), x).astype(np.float32)


def read_wav_mono(p: Path) -> np.ndarray:
    with wave.open(str(p)) as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    if ch == 2:
        a = a.reshape(-1, 2).mean(axis=1)
    return _resample(a, sr, SR)


def write_wav(p: Path, x: np.ndarray, sr: int = SR) -> None:
    x = np.clip(x, -1, 1)
    s = (x * 32767).astype("<i2")
    stereo = np.repeat(s[:, None], 2, axis=1)
    with wave.open(str(p), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(stereo.tobytes())


def build_audio() -> dict:
    AUDIO.mkdir(exist_ok=True)
    N = int(DUR * SR)
    t = np.arange(N) / SR

    # ---- voiceover: one espeak-ng line per beat -------------------------- #
    voice = np.zeros(N, np.float32)
    vo_windows: list[tuple[float, float]] = []
    for i, (start, text) in enumerate(VO_LINES):
        raw = AUDIO / f"line{i:02d}_raw.wav"
        subprocess.run(["espeak-ng", "-v", "en-GB", "-s", "158", "-p", "42",
                        "-a", "180", "-w", str(raw), text], check=True)
        y = read_wav_mono(raw)
        s = int(start * SR)
        e = min(N, s + len(y))
        voice[s:e] += y[:e - s]
        vo_windows.append((start, (s + len(y)) / SR))
    peak = np.max(np.abs(voice)) + 1e-9
    voice = voice / peak * 0.9

    # ---- music bed: cosmic pad + bells ----------------------------- #    #
    music = np.zeros(N, np.float32)
    # chord progression (root, 3rd, 5th) — a slow, hopeful loop
    chords = [
        (0.0,  6.0,  [174.61, 220.00, 261.63]),   # F
        (5.0,  10.0, [196.00, 246.94, 293.66]),   # G
        (10.0, 15.0, [130.81, 164.81, 196.00]),   # C
        (15.0, 20.0, [146.83, 174.61, 220.00]),   # Dm
        (20.0, 24.0, [174.61, 220.00, 261.63]),   # F
        (24.0, DUR,  [130.81, 164.81, 196.00]),   # C
    ]
    for st, en, freqs in chords:
        s, e = int(st * SR), min(N, int(en * SR))
        seg_t = t[s:e] - t[s]
        seg = np.zeros(e - s, np.float32)
        for k, f in enumerate(freqs):
            for d, amp in ((0.0, 1.0), (0.35, 0.4), (-0.35, 0.4)):  # gentle detune
                seg += amp * np.sin(2 * np.pi * (f + d) * seg_t + k)
        fade = min(1.0, (e - s) / SR / 1.2)
        env = np.minimum(1.0, np.minimum(seg_t / 1.0, (seg_t[-1] - seg_t) / 1.2 + 1e-6))
        env = np.clip(env, 0, 1)
        music[s:e] += seg * env / (3 * len(freqs) * 1.7)
    # bell arpeggio (F major pentatonic-ish, rising = optimism)
    melo = [523.25, 587.33, 698.46, 783.99, 880.00, 1046.50]
    for i, f in enumerate(melo):
        st = 1.0 + i * 3.2
        s, e = int(st * SR), min(N, int((st + 1.6) * SR))
        if e <= s:
            continue
        seg_t = t[s:e] - t[s]
        music[s:e] += np.sin(2 * np.pi * f * seg_t) * np.exp(-3.0 * seg_t) * 0.09

    # duck music under the voice
    duck = np.ones(N, np.float32)
    for a, b in vo_windows:
        s, e = int(a * SR), min(N, int(b * SR))
        duck[s:e] = 0.40
    win = int(0.25 * SR)
    duck = np.convolve(duck, np.ones(win) / win, mode="same")

    # ---- SFX ------------------------------------------------------------- #
    rng = np.random.default_rng(23)
    sfx = np.zeros(N, np.float32)
    # whoosh at the open
    s, e = 0, int(0.8 * SR)
    sfx[s:e] += rng.normal(0, 1, e - s).astype(np.float32) * np.hanning(e - s) * 0.16
    # soft ticks on each service-card reveal
    for st in (8.7, 11.4, 14.0, 16.7):
        s = int(st * SR)
        e = s + int(0.06 * SR)
        seg_t = t[s:e] - t[s]
        sfx[s:e] += np.sin(2 * np.pi * 1760 * seg_t) * np.exp(-55 * seg_t) * 0.09
    # logo chime at the CTA
    s = int(24.3 * SR)
    e = min(N, s + int(0.9 * SR))
    seg_t = t[s:e] - t[s]
    chime = sum(np.sin(2 * np.pi * f * seg_t) for f in (523.25, 659.25, 783.99))
    sfx[s:e] += chime * np.exp(-4.0 * seg_t) * 0.06

    bed = (music * duck + sfx).astype(np.float32)
    write_wav(AUDIO / "voice.wav", voice)
    write_wav(AUDIO / "music_bed.wav", bed)

    mix = (voice * 0.92 + bed * 0.55).astype(np.float32)
    mix /= (np.max(np.abs(mix)) + 1e-9)
    write_wav(AUDIO / "mix_raw.wav", mix * 0.95)

    # ---- two-pass loudness normalisation to -14 LUFS / TP -1 dBTP ------- #
    r1 = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(AUDIO / "mix_raw.wav"),
         "-af", "loudnorm=I=-14:TP=-2:LRA=11:print_format=json",
         "-f", "null", "-"], capture_output=True, text=True)
    js = r1.stderr[r1.stderr.rfind("{"):r1.stderr.rfind("}") + 1]
    m = json.loads(js)
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-i", str(AUDIO / "mix_raw.wav"),
         "-af", (f"loudnorm=I=-14:TP=-2:LRA=11:linear=true:"
                 f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                 f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
                 f"offset={m['target_offset']}"),
         "-ar", str(SR), str(AUDIO / "audio_final.wav")], check=True)

    info = {
        "vo_lines": len(VO_LINES),
        "vo_windows": [(round(a, 2), round(b, 2)) for a, b in vo_windows],
        "loudnorm_measured": {k: m[k] for k in
                              ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")},
    }
    (AUDIO / "audio_report.json").write_text(json.dumps(info, indent=2) + "\n")
    return info


# --------------------------------------------------------------------------- #
# frames
# --------------------------------------------------------------------------- #
_MARK_L = Image.open(BRAND / "logo-mark-on-dark-1024.png").convert("RGBA").resize((520, 520), Image.LANCZOS)
_LOCK = Image.open(BRAND / "logo-lockup-dark-transparent-2000x300.png").convert("RGBA")


def starfield() -> Image.Image:
    rng = np.random.default_rng(5)
    img = Image.new("RGB", (W, H), hx(REF["neutral-6"]))
    glow = Image.new("RGB", (W, H), hx(REF["neutral-6"]))
    gd = ImageDraw.Draw(glow, "RGBA")
    for i in range(70, 0, -1):
        r = i * 16
        gd.ellipse([W * 0.5 - r, H * 0.34 - r, W * 0.5 + r, H * 0.34 + r],
                   fill=hx(REF["violet-30"]) + (int(1.6 * i),))
    for i in range(50, 0, -1):
        r = i * 20
        gd.ellipse([W * 0.15 - r, H * 0.86 - r, W * 0.15 + r, H * 0.86 + r],
                   fill=hx(REF["cyan-20"]) + (int(1.1 * i),))
    img = Image.blend(img, glow, 0.5)
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(600):
        x, y = int(rng.integers(W)), int(rng.integers(H))
        s = int(rng.choice([1, 1, 1, 2, 2, 3]))
        d.ellipse([x, y, x + s, y + s], fill=(255, 255, 255, int(rng.integers(25, 130))))
    d.ellipse([W * 0.5 - 360, H * 0.34 - 360, W * 0.5 + 360, H * 0.34 + 360],
              outline=hx(REF["violet-60"]) + (60,), width=2)
    return img


BASE = starfield()
BLACK = Image.new("RGB", (W, H), (0, 0, 0))


def _vignette() -> Image.Image:
    vg = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vg)
    vd.ellipse([-W * 0.4, -H * 0.15, W * 1.4, H * 1.15], fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(160))
    return vg.point(lambda v: 120 + v * 135 // 255)


def _glow() -> Image.Image:
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gl)
    gd.ellipse([W / 2 - 540, 820 - 540, W / 2 + 540, 820 + 540],
               fill=hx(REF["violet-40"]) + (95,))
    return gl.filter(ImageFilter.GaussianBlur(90))


VIGNETTE = _vignette()
GLOW = _glow()


def caption_bar(d: ImageDraw.ImageDraw, text: str) -> None:
    f = fnt("DejaVuSans-Bold.ttf", 44)
    words = text.split()
    # wrap to <= 26 chars per line, max 3 lines
    lines, cur = [], ""
    for word in words:
        if len(cur) + len(word) + 1 <= 26:
            cur = (cur + " " + word).strip()
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    lines = lines[:3]
    tw = max(d.textlength(s, font=f) for s in lines)
    lh = 56
    bw, bh = tw + 72, lh * len(lines) + 40
    x0, y0 = (W - bw) / 2, 1440
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=28, fill=(10, 9, 16, 190))
    for i, s in enumerate(lines):
        w = d.textlength(s, font=f)
        d.text(((W - w) / 2, y0 + 20 + i * lh), s, font=f, fill=hx(REF["neutral-95"]))


def draw_frame(t: float) -> Image.Image:
    img = BASE.copy()
    d = ImageDraw.Draw(img, "RGBA")

    # ---- scene 1: HOOK (0.6–3.2) ---------------------------------------- #
    if t < 3.4:
        p = ease(seg(t, 0.5, 1.6))
        scale = 0.85 + 0.15 * p
        mk = _MARK_L.resize((int(520 * scale),) * 2, Image.LANCZOS)
        mk.putalpha(mk.getchannel("A").point(lambda v: int(v * p)))
        img.paste(mk, ((W - mk.width) // 2, 560), mk)
        kp = ease(seg(t, 1.6, 2.4))
        kf = fnt("DejaVuSans-Bold.ttf", 40)
        ks = "AUTONOMOUS  ·  AI-RUN"
        kw = d.textlength(ks, font=kf)
        d.text(((W - kw) / 2, 1160), ks, font=kf,
               fill=hx(REF["cyan-80"]) + (int(255 * kp),))

    # ---- scene 2: WHO (3.6–8.2) ----------------------------------------- #
    if 3.4 <= t < 8.5:
        p = ease(seg(t, 3.6, 4.4))
        q = ease(seg(t, 4.2, 5.0))
        yoff = int(40 * (1 - p))
        hf = fnt("DejaVuSerif-Bold.ttf", 96)
        l1, l2 = "A digital agency,", "run by AI agents."
        for i, s in enumerate((l1, l2)):
            w = d.textlength(s, font=hf)
            d.text(((W - w) / 2, 760 + i * 120 + yoff), s, font=hf,
                   fill=hx(REF["neutral-95"]) + (int(255 * q),))
        sub = "Four services. One autonomous team."
        sf = fnt("DejaVuSans.ttf", 40)
        sw = d.textlength(sub, font=sf)
        d.text(((W - sw) / 2, 1080), sub, font=sf,
               fill=hx(REF["violet-80"]) + (int(255 * ease(seg(t, 5.0, 5.8))),))

    # ---- scene 3: OFFER (8.6–19.4) — four service cards ------------------ #
    services = [("Web & app build", "web"), ("AI automation", "ai"),
                ("Video & design", "video"), ("Digital products", "product")]
    card_times = [(8.6, 11.3), (11.3, 13.9), (13.9, 16.6), (16.6, 19.4)]
    if 8.4 <= t < 19.6:
        d.text((90, 300), "WHAT WE BUILD", font=fnt("DejaVuSans-Bold.ttf", 40),
               fill=hx(REF["cyan-80"]))
        for i, ((name, _), (a, b)) in enumerate(zip(services, card_times)):
            if t < a:
                continue
            p = ease(seg(t, a, a + 0.55))
            y = 470 + i * 250
            xoff = int(160 * (1 - p))
            alpha = int(255 * p)
            d.rounded_rectangle([90 + xoff, y, W - 90 + xoff, y + 200], radius=28,
                                fill=hx(REF["neutral-12"]) + (alpha,),
                                outline=hx(REF["violet-60"]) + (alpha,), width=3)
            d.rounded_rectangle([130 + xoff, y + 46, 238 + xoff, y + 154], radius=20,
                                fill=hx(REF["violet-40"]) + (alpha,))
            d.text((160 + xoff, y + 66), str(i + 1), font=fnt("DejaVuSans-Bold.ttf", 62),
                   fill=hx(REF["neutral-100"]) + (alpha,))
            d.text((290 + xoff, y + 72), name, font=fnt("DejaVuSerif-Bold.ttf", 58),
                   fill=hx(REF["neutral-95"]) + (alpha,))

    # ---- scene 4: HOW (20.0–23.8) --------------------------------------- #
    if 19.8 <= t < 24.0:
        p = ease(seg(t, 20.0, 20.7))
        d.text((90, 560), "HOW IT WORKS", font=fnt("DejaVuSans-Bold.ttf", 40),
               fill=hx(REF["cyan-80"]) + (int(255 * p),))
        steps = ["Strategy", "Build", "Launch"]
        for i, s in enumerate(steps):
            pa = ease(seg(t, 20.4 + i * 0.5, 21.0 + i * 0.5))
            y = 700 + i * 220
            d.rounded_rectangle([120, y, W - 120, y + 160], radius=24,
                                fill=hx(REF["violet-30"]) + (int(220 * pa),))
            d.text((170, y + 40), f"{i + 1}", font=fnt("DejaVuSans-Bold.ttf", 70),
                   fill=hx(REF["cyan-80"]) + (int(255 * pa),))
            d.text((300, y + 46), s, font=fnt("DejaVuSerif-Bold.ttf", 66),
                   fill=hx(REF["neutral-95"]) + (int(255 * pa),))

    # ---- scene 5: CTA (24.4–28.0) --------------------------------------- #
    if t >= 24.1:
        p = ease(seg(t, 24.3, 25.2))
        pulse = 0.5 + 0.5 * math.sin((t - 24.3) * 2.4)
        gl = GLOW.copy()
        gl.putalpha(gl.getchannel("A").point(lambda v: int(v * p * (0.7 + 0.3 * pulse))))
        img = Image.alpha_composite(img.convert("RGBA"), gl).convert("RGB")
        d = ImageDraw.Draw(img, "RGBA")
        lk = _LOCK.resize((int(920 * (0.9 + 0.1 * p)), int(138 * (0.9 + 0.1 * p))), Image.LANCZOS)
        lk.putalpha(lk.getchannel("A").point(lambda v: int(v * p)))
        img.paste(lk, ((W - lk.width) // 2, 720), lk)
        tag = "Build what's next."
        tf = fnt("DejaVuSerif-Bold.ttf", 70)
        tw = d.textlength(tag, font=tf)
        d.text(((W - tw) / 2, 960), tag, font=tf,
               fill=hx(REF["neutral-95"]) + (int(255 * ease(seg(t, 25.0, 25.8))),))
        hd = "@aiastra"
        hf2 = fnt("DejaVuSans-Bold.ttf", 44)
        hw = d.textlength(hd, font=hf2)
        d.text(((W - hw) / 2, 1090), hd, font=hf2,
               fill=hx(REF["cyan-80"]) + (int(255 * ease(seg(t, 25.4, 26.2))),))

    # ---- captions -------------------------------------------------------- #
    for start, text in VO_LINES:
        # show the caption for ~ the VO duration, minimum 1.6 s
        dur = max(1.6, 0.06 * len(text.split()) + 1.1)
        if start <= t < start + dur:
            caption_bar(d, text)
            break

    # subtle vignette to focus the centre (mask precomputed)
    img = Image.composite(img, BLACK, VIGNETTE)
    return img


def render_frames() -> None:
    """Stream rendered frames straight into ffmpeg (no PNG round-trip)."""
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir()
    n = int(DUR * FPS)
    proc = subprocess.Popen([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "-",
        "-i", str(AUDIO / "audio_final.wav"),
        "-c:v", "libx264", "-profile:v", "high", "-level", "4.0",
        "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
        "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-shortest", str(OUT)], stdin=subprocess.PIPE)
    for i in range(n):
        fr = draw_frame(i / FPS)
        proc.stdin.write(fr.tobytes())
        if i % 120 == 0:
            # keep a few key frames on disk as render evidence
            fr.save(FRAMES / f"f{i:05d}.png")
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise SystemExit(f"ffmpeg failed: {proc.returncode}")
    print(f"streamed {n} frames -> {OUT.name}")


# --------------------------------------------------------------------------- #
# captions + thumbnail
# --------------------------------------------------------------------------- #
def ts(s: float) -> str:
    h = int(s // 3600); m = int((s % 3600) // 60); sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")


def write_captions() -> None:
    subs = []
    for start, text in VO_LINES:
        dur = max(1.6, 0.06 * len(text.split()) + 1.1)
        subs.append((start, min(start + dur, DUR), text))
    srt = []
    vtt = ["WEBVTT", ""]
    for i, (a, b, txt) in enumerate(subs, 1):
        srt.append(f"{i}\n{ts(a)} --> {ts(b)}\n{txt}\n")
        vtt.append(f"{i}\n{ts(a)} --> {ts(b)}\n{txt}\n")
    (HERE / "captions.srt").write_text("\n".join(srt), encoding="utf-8")
    (HERE / "captions.vtt").write_text("\n".join(vtt), encoding="utf-8")
    print("wrote captions.srt captions.vtt")


def make_thumbnail() -> None:
    img = starfield()
    d = ImageDraw.Draw(img, "RGBA")
    # top pill
    pf = fnt("DejaVuSans-Bold.ttf", 40)
    ps = "AUTONOMOUS  ·  AI-RUN  ·  DIGITAL AGENCY"
    pw = d.textlength(ps, font=pf)
    d.rounded_rectangle([(W - pw) / 2 - 40, 220, (W + pw) / 2 + 40, 320], radius=50,
                        fill=hx(REF["violet-40"]) + (230,))
    d.text(((W - pw) / 2, 245), ps, font=pf, fill=hx(REF["neutral-100"]))
    # mark
    mk = _MARK_L.resize((560, 560), Image.LANCZOS)
    img.paste(mk, ((W - 560) // 2, 470), mk)
    # headline
    hf = fnt("DejaVuSerif-Bold.ttf", 108)
    for i, s in enumerate(("AI ASTRA", "AGENCY")):
        w = d.textlength(s, font=hf)
        d.text(((W - w) / 2, 1080 + i * 128), s, font=hf, fill=hx(REF["neutral-95"]))
    tf = fnt("DejaVuSerif-Bold.ttf", 62)
    tag = "Build what's next."
    tw = d.textlength(tag, font=tf)
    d.text(((W - tw) / 2, 1400), tag, font=tf, fill=hx(REF["violet-80"]))
    # services row
    sf = fnt("DejaVuSans-Bold.ttf", 36)
    svc = "WEB & APP  ·  AI AUTOMATION  ·  VIDEO & DESIGN  ·  DIGITAL PRODUCTS"
    # wrap into two lines
    line1, line2 = "WEB & APP  ·  AI AUTOMATION", "VIDEO & DESIGN  ·  DIGITAL PRODUCTS"
    for i, s in enumerate((line1, line2)):
        w = d.textlength(s, font=sf)
        d.text(((W - w) / 2, 1560 + i * 60), s, font=sf, fill=hx(REF["cyan-80"]))
    img.save(THUMB)
    print("wrote", THUMB.name)


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", action="store_true", help="audio only")
    args = ap.parse_args()
    info = build_audio()
    print("audio:", json.dumps(info, indent=2))
    write_captions()
    make_thumbnail()
    if not args.audio:
        render_frames()
    return 0


if __name__ == "__main__":
    sys.exit(main())
