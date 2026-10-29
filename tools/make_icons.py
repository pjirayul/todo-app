"""Draws the app icon PNGs (voice-wave on the purple gradient). Run: python tools/make_icons.py"""
from PIL import Image, ImageDraw
S = 4  # draw 4x bigger, then shrink = smooth edges
def icon(size, rounded=True):
    n = size * S
    grad = Image.new("RGB", (n, n))
    px = grad.load()
    c = [(0x5b, 0x4c, 0xf0), (0x7a, 0x45, 0xe8), (0x9b, 0x3f, 0xd6)]
    for y in range(n):
        for x in range(n):
            t = (x + y) / (2 * n)
            a, b, u = (c[0], c[1], t * 2) if t < .5 else (c[1], c[2], (t - .5) * 2)
            px[x, y] = tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))
    mask = Image.new("L", (n, n), 255)
    if rounded:
        mask = Image.new("L", (n, n), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, n - 1, n - 1], radius=int(n * .234), fill=255)
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0)); img.paste(grad, mask=mask)
    d = ImageDraw.Draw(img)
    k = n / 64 * 1.75 * (0.8 if not rounded else 1)   # wave scale (smaller on the maskable one)
    o = (n - 24 * k) / 2
    w = 2.4 * k
    for x, y1, y2 in [(4, 10, 14), (8, 7, 17), (12, 4, 20), (16, 8, 16), (20, 11, 13)]:
        X, a, b = o + x * k, o + y1 * k, o + y2 * k
        d.line([(X, a), (X, b)], fill="white", width=int(w))
        for Y in (a, b): d.ellipse([X - w / 2, Y - w / 2, X + w / 2, Y + w / 2], fill="white")
    return img.resize((size, size), Image.LANCZOS)
for name, size, r in [("icon-192.png", 192, True), ("icon-512.png", 512, False), ("apple-touch-icon.png", 180, False)]:
    icon(size, r).save(name)
