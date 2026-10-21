# Genera icono.ico a partir de la silueta (mismo trazado que usa el programa).
import math, sys
from PIL import Image, ImageDraw
src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "Non_Synapse_Mouse.py"), encoding="utf-8").read()
i = src.index("_MOUSE_LINES = ["); j = src.index("\n    ]\n", i) + 6
ns = {}; exec("\n".join(l[4:] if l.startswith("    ") else l for l in src[i:j].splitlines()), ns)
LINES = ns["_MOUSE_LINES"]

def catmull(pts, per_unit):
    P_ = [pts[0]] + list(pts) + [pts[-1]]; out = []
    for i in range(1, len(pts)):
        p0, p1, p2, p3 = P_[i-1], P_[i], P_[i+1], P_[i+2]
        seg = max(1, int(math.hypot(p2[0]-p1[0], p2[1]-p1[1]) * per_unit))
        for n in range(seg):
            t = n/seg; t2 = t*t; t3 = t2*t
            out.append(tuple(0.5*(2*p1[j]+(p2[j]-p0[j])*t+(2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t2+(3*p1[j]-p0[j]-3*p2[j]+p3[j])*t3) for j in (0, 1)))
    out.append(tuple(pts[-1])); return out

def icon(size):
    ss = 8 if size <= 64 else 4
    big = size * ss
    tile = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle((0, 0, big - 1, big - 1), radius=int(big * 0.22), fill=(32, 32, 32, 255))
    # silueta: ocupa ~80 % del alto del icono; mas gruesa cuanto mas pequeno
    fill = 0.80
    k = big / 24.0 * fill; off = big / 2 - 12 * k
    frac = 0.095 if size <= 32 else (0.075 if size <= 64 else 0.06)
    r = max(1.5, size * frac) * ss / 2 * fill / 0.94 * 0.94
    mask = Image.new("L", (big, big), 0); md = ImageDraw.Draw(mask)
    for pl in LINES:
        for (x, y) in catmull(pl, max(8, ss * 3)):
            md.ellipse((x*k+off-r, y*k+off-r, x*k+off+r, y*k+off+r), fill=255)
    green = Image.new("RGBA", (big, big), (68, 214, 44, 255))
    tile.paste(green, (0, 0), mask)
    return tile.resize((size, size), Image.LANCZOS)

sizes = [256, 128, 64, 48, 32, 24, 16]
ims = {s: icon(s) for s in sizes}
ims[256].save("/home/claude/work/icono.ico", format="ICO", sizes=[(s, s) for s in sizes], append_images=[ims[s] for s in sizes[1:]])
sheet = Image.new("RGB", (620, 280), (60, 60, 60)); x = 10
for s in sizes:
    sheet.paste(ims[s], (x, 10), ims[s]); x += s + 10
sheet.save("/home/claude/work/tests/out/icon_sheet.png")
chk = Image.open("/home/claude/work/icono.ico"); print(chk.info.get("sizes"), chk.size)
