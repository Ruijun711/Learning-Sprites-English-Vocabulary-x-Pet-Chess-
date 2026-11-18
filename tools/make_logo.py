"""產生學習精靈的 logo：art/logo.png（512×512）與 art/logo.ico（Windows 捷徑、系統匣用）。

圓角方塊底（森林綠漸層＋中央光暈）上放字靈，右上角一顆星光。
用法：python tools/make_logo.py
"""
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SPRITE = ROOT / "art" / "spirits" / "abc-1.png"
S = 512


def gradient(size, top, bottom):
    img = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(img)
    for y in range(size):
        t = y / (size - 1)
        d.line([(0, y), (size, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)) + (255,))
    return img


def star(d, cx, cy, r, fill):
    pts = []
    for i in range(8):
        rr = r if i % 2 == 0 else r * 0.28
        import math
        a = math.pi / 4 * i - math.pi / 2
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)


def main():
    # 圓角底
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=112, fill=255)
    bg = gradient(S, (78, 150, 110), (34, 84, 62))

    # 中央光暈
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([86, 96, S - 86, S - 76], fill=(255, 238, 170, 150))
    glow = glow.filter(ImageFilter.GaussianBlur(48))
    bg = Image.alpha_composite(bg, glow)

    # 字靈＋淡陰影
    sp = Image.open(SPRITE).convert("RGBA").resize((400, 400), Image.LANCZOS)
    shadow = Image.new("RGBA", sp.size, (0, 0, 0, 0))
    shadow.putalpha(sp.getchannel("A").point(lambda a: a * 0.35))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    ox, oy = (S - 400) // 2, (S - 400) // 2 + 14
    bg.alpha_composite(shadow, (ox + 6, oy + 12))
    bg.alpha_composite(sp, (ox, oy))

    # 星光
    d = ImageDraw.Draw(bg)
    star(d, 420, 92, 44, (255, 222, 120, 255))
    star(d, 420, 92, 22, (255, 255, 240, 255))
    star(d, 92, 400, 18, (255, 240, 190, 230))

    # 套圓角
    bg.putalpha(ImageChops.multiply(bg.getchannel("A"), mask))
    out_png, out_ico = ROOT / "art" / "logo.png", ROOT / "art" / "logo.ico"
    bg.save(out_png)
    bg.save(out_ico, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"已產生 {out_png} 與 {out_ico}")


if __name__ == "__main__":
    main()
