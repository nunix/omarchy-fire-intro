# Generate a "Hackers"-style burning OMARCHY boot intro -> intro.mp4
# Run: uv run --with numpy --with pillow make-intro.py
import subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

TEXT = "OMARCHY"
FONT = "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Bold.ttf"
OUT_W, OUT_H = 1728, 1116
SCALE = 3
W, H = OUT_W // SCALE, OUT_H // SCALE
FPS, DUR = 30, 8.0
IGNITE, TEXT_FIRE, TEXT_SHOW, DOUSE, FADE_OUT = 0.3, 1.5, 2.0, 6.3, 7.0

rng = np.random.default_rng(1995)

# Classic Doom fire palette (37 steps, black -> red -> orange -> yellow -> white)
PAL = np.array([
    (7,7,7),(31,7,7),(47,15,7),(71,15,7),(87,23,7),(103,31,7),(119,31,7),(143,39,7),
    (159,47,7),(175,63,7),(191,71,7),(199,71,7),(223,79,7),(223,87,7),(223,87,7),(215,95,7),
    (215,103,15),(207,111,15),(207,119,15),(207,127,15),(207,135,23),(199,135,23),(199,143,23),
    (199,151,31),(191,159,31),(191,159,31),(191,167,39),(191,167,39),(191,175,47),(183,175,47),
    (183,183,47),(183,183,55),(207,207,111),(223,223,159),(239,239,199),(255,255,255),(255,255,255),
], dtype=np.uint8)
MAX = len(PAL) - 1

def font_for(width, draw):
    size = 10
    while True:
        f = ImageFont.truetype(FONT, size)
        if draw.textbbox((0, 0), TEXT, font=f)[2] > width:
            return ImageFont.truetype(FONT, size - 1)
        size += 1

def text_layer(w, h, width_ratio):
    img = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(img)
    f = font_for(int(w * width_ratio), d)
    x0, y0, x1, y1 = d.textbbox((0, 0), TEXT, font=f)
    d.text(((w - (x1 - x0)) / 2 - x0, (h - (y1 - y0)) / 2 - y0 + h * 0.05), TEXT, font=f, fill=255)
    return img

# Heat sources: the letters themselves, at fire resolution
src_mask = np.array(text_layer(W, H, 0.72)) > 128

# Crisp overlay text: molten gradient fill + orange glow, at output resolution
mask = text_layer(OUT_W, OUT_H, 0.72)
grad = np.zeros((OUT_H, OUT_W, 3), np.uint8)
ys = np.linspace(0, 1, OUT_H)[:, None]
grad[..., 0] = 255
# white-hot -> yellow -> red, concentrated over the text band
k = ((ys - 0.40) / 0.25).clip(0, 1)
grad[..., 1] = (255 - 200 * k).astype(np.uint8)
grad[..., 2] = (230 - 230 * np.sqrt(k)).astype(np.uint8)
glow = mask.filter(ImageFilter.GaussianBlur(18))
overlay = Image.new("RGBA", (OUT_W, OUT_H), (255, 90, 0, 0))
overlay.putalpha(glow.point(lambda v: int(v * 0.9)))
fill = Image.fromarray(grad).convert("RGBA")
fill.putalpha(mask)
overlay.alpha_composite(fill)
overlay.save("/tmp/omarchy-text.png")

# --- Fire simulation (demoscene style: average cells below, subtract scrolling cooling noise) ---
def blur(a, k):
    for axis in (0, 1):
        a = sum(np.roll(a, d, axis=axis) for d in range(-k, k + 1)) / (2 * k + 1)
    return a

cool = blur(rng.random((H * 2, W)), 3)
cool = (cool - cool.min()) / (cool.max() - cool.min())
cool = (cool ** 2 * 1.3).astype(np.float32)  # sparse hot tongues, strong gaps
fire = np.zeros((H, W), np.float32)
scroll = 0

def step(f):
    global scroll
    scroll = (scroll + 2) % H
    b1 = f[1:-1]
    avg = (np.roll(b1, 1, 1) + b1 + np.roll(b1, -1, 1) + f[2:]) / 4
    c = np.roll(cool, -scroll, axis=0)[:H - 2]
    f[:-2] = np.maximum(avg - c, 0)

def frames():
    for i in range(int(FPS * DUR)):
        t = i / FPS
        if IGNITE <= t < DOUSE:
            base = min(1.0, (t - IGNITE) * 1.5)
        else:
            base = max(0.0, 1 - (t - DOUSE) * 1.5) if t >= DOUSE else 0.0
        fire[-2:] = base * MAX * rng.uniform(0.55, 1.0, (2, W))
        if TEXT_FIRE <= t < DOUSE:
            heat = min(1.0, (t - TEXT_FIRE) * 1.2)
            fire[src_mask] = heat * MAX * rng.uniform(0.6, 1.0, src_mask.sum())
        for _ in range(2):
            step(fire)
        yield PAL[np.clip(fire, 0, MAX).astype(np.int16)].tobytes()

# --- Audio: roaring crackle + whoosh on ignition + low boom when the title lands ---
SR = 48000
n = int(SR * DUR)
t = np.arange(n) / SR
noise = rng.standard_normal(n)
roar = np.convolve(noise, np.ones(40) / 40, mode="same")  # low rumble
env = np.clip((t - IGNITE) / 1.0, 0, 1) * np.clip((FADE_OUT + 0.8 - t) / 1.5, 0, 1)
env = env * (1 + 0.6 * np.clip((t - TEXT_FIRE) / 0.8, 0, 1))
crackle = np.zeros(n)
pops = rng.choice(n, 900, replace=False)
crackle[pops] = rng.uniform(-1, 1, len(pops))
crackle = np.convolve(crackle, np.exp(-np.arange(200) / 25), mode="same")
whoosh_env = np.exp(-((t - TEXT_FIRE - 0.3) ** 2) / 0.08)
whoosh = np.convolve(noise, np.ones(8) / 8, mode="same") * whoosh_env
bt = np.clip(t - TEXT_SHOW, 0, None)
boom = np.sin(2 * np.pi * (55 - 15 * bt) * bt) * np.exp(-bt * 2.2) * (t >= TEXT_SHOW)
audio = 2.2 * roar * env + 0.5 * crackle * env + 0.9 * whoosh + 0.8 * boom
audio = audio / np.abs(audio).max() * 0.9
with wave.open("/tmp/omarchy-intro.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((audio * 32767).astype(np.int16).tobytes())

ff = subprocess.Popen([
    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
    "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-loop", "1", "-r", str(FPS), "-i", "/tmp/omarchy-text.png",
    "-i", "/tmp/omarchy-intro.wav",
    "-filter_complex",
    f"[0:v]scale={OUT_W}:{OUT_H}:flags=bicubic,gblur=sigma=1.5[f];"
    f"[1:v]format=rgba,fade=in:st={TEXT_SHOW}:d=1:alpha=1,fade=out:st={DOUSE}:d=0.8:alpha=1[t];"
    f"[f][t]overlay=shortest=1,fade=out:st={FADE_OUT}:d=1,format=yuv420p[v]",
    "-map", "[v]", "-map", "2:a", "-t", str(DUR),
    "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "intro.mp4",
], stdin=subprocess.PIPE)
for fr in frames():
    ff.stdin.write(fr)
ff.stdin.close()
ff.wait()
print("wrote intro.mp4")
