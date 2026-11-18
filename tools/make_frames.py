"""從每張精靈去背圖產生桌面寵物用的動作圖（不用重畫，全部用網格變形和描繪眼睛做出來）。

會產生的圖（art/spirits/frames/<代號>-<階段>/*.webp）：
  walk_0~7     走路：腳分前後（或左右）兩群輪流跨步、抬腳，身體一步一起伏並往前傾
  fidget_0~5   待機小動作：尾巴、耳朵、觸角、頭上的葉子、頭帶輕輕擺動
  flap_0~5     揮動：翅膀拍動（有翅膀的精靈）
  punch_0~5    出拳：手套／盾牌往前推（拳拳、沙發獸、小屋守衛）
  shell_0~2    縮進殼裡（糰糰、飯盒獸、御膳獸）：頭縮小變暗、滑進殼口，腳往上縮，殼貼地
  shell_sleep  縮在殼裡睡覺
  blink        眨眼（眼睛閉上）
  sleep        睡覺的閉眼
  happy        開心的 ^ ^ 眼
  dizzy        暈眩的 @ @ 眼

部位位置寫在 art/spirits/rig.json（眼睛、會擺動的部位與關節、殼）。換了精靈圖或改了 rig.json 後重跑：
  python tools/make_frames.py            # 全部
  python tools/make_frames.py abc-1      # 只做指定的
原圖大多面向左邊，所以「往前」是往左；桌面程式往右走時會整張水平翻轉。
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "art" / "spirits"
OUT = SRC / "frames"
RIG = json.loads((SRC / "rig.json").read_text(encoding="utf-8"))
PAD = 16          # 畫布四周留白（原圖 256 → 288），抬腳、擺尾巴時不會被切掉
GRID = 8          # 變形網格大小（px），越小越平滑
OUT_SIZE = 176    # 輸出大小；桌面上精靈約顯示 96px
LOOP = 6          # 擺動類動作每輪幾張


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def warp(img, src_of):
    """網格變形：src_of(x, y) 回傳輸出圖上 (x, y) 這一點要從原圖哪裡取色。"""
    size = img.width
    mesh = []
    for gy in range(0, size, GRID):
        for gx in range(0, size, GRID):
            box = (gx, gy, min(gx + GRID, size), min(gy + GRID, size))
            quad = []
            for cx, cy in ((box[0], box[1]), (box[0], box[3]), (box[2], box[3]), (box[2], box[1])):
                quad += list(src_of(cx, cy))
            mesh.append((box, quad))
    return img.transform((size, size), Image.MESH, mesh, Image.BICUBIC)


def region_weight(region, x, y):
    """橢圓範圍內為 1，邊緣柔和地降到 0。"""
    cx, cy, rx, ry = [v + (PAD if i < 2 else 0) for i, v in enumerate(region)]
    d = math.hypot((x - cx) / rx, (y - cy) / ry)
    return 1 - smoothstep(0.7, 1.0, d)


def P(pt):
    return pt[0] + PAD, pt[1] + PAD


def part_weight(part, x, y):
    """部位的影響範圍：從關節往部位方向的扇形，越靠近關節動越少，邊緣柔和。
    用扇形而不是只用橢圓，部位擺出原本範圍時才不會被切掉。"""
    px, py = P(part["pivot"])
    cx, cy, rx, ry = part["region"]
    cx, cy = cx + PAD, cy + PAD
    ux, uy = cx - px, cy - py
    reach = math.hypot(ux, uy)
    vx, vy = x - px, y - py
    d = math.hypot(vx, vy)
    if d < 1e-6 or reach < 1e-6:
        return 0.0
    half = min(math.radians(45), math.atan2(max(rx, ry), reach) + math.radians(8))
    cos_a = (vx * ux + vy * uy) / (d * reach)
    w_ang = smoothstep(math.cos(half + math.radians(12)), math.cos(half), cos_a)
    far = reach + max(rx, ry)
    w_rad = 1 - smoothstep(far * 1.1, far * 1.3, d)
    w_near = smoothstep(0, 12, d)
    return w_ang * w_rad * w_near


# ---------- 走路 ----------
def walk_frames(canvas):
    size = canvas.width
    left, top, right, bottom = canvas.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()
    bw, bh = right - left, bottom - top
    leg_top = bottom - bh * 0.24
    band = canvas.crop((0, int(leg_top), size, bottom)).getchannel("A")
    xs = [x for x in range(size) for y in range(0, band.height, 3) if band.getpixel((x, y)) > 64]
    split = sum(xs) / len(xs) if xs else (left + right) / 2
    stride, lift = bw * 0.055, bh * 0.045
    bob, lean = bh * 0.022, bw * 0.018
    out = []
    for k in range(8):
        ph = 2 * math.pi * k / 8
        dx_l, up_l = -stride * math.sin(ph), lift * max(0.0, math.cos(ph))
        dx_r, up_r = stride * math.sin(ph), lift * max(0.0, -math.cos(ph))
        body_up = bob * (1 + math.cos(2 * ph)) / 2

        def src(x, y):
            w = smoothstep(leg_top, bottom, y)
            b = 0.5 + 0.5 * math.tanh((x - split) / (bw * 0.06))
            dx = (1 - b) * dx_l + b * dx_r
            up = (1 - b) * up_l + b * up_r
            rel = (y - top) / bh
            return x - (w * dx - lean * (1 - rel)), y - (-w * up - body_up * (1 - w))
        out.append(warp(canvas, src))
    return out


# ---------- 部位擺動（尾巴、耳朵、翅膀、手） ----------
def part_frames(canvas, parts):
    out = []
    for k in range(LOOP):
        poses = []
        for p in parts:
            s = math.sin(2 * math.pi * (k / LOOP + p.get("phase", 0)))
            push = p.get("punch")
            if push:  # 出拳：快速推出再收回（只往前，不往後）
                s = max(0.0, s) ** 0.6
            poses.append((p, s))

        def src(x, y):
            for p, s in poses:
                w = part_weight(p, x, y)
                if w <= 0:
                    continue
                px, py = P(p["pivot"])
                if p.get("punch"):
                    x -= w * s * p["punch"][0]
                    y -= w * s * p["punch"][1]
                a = math.radians(-p["amp"] * s * w)
                dx, dy = x - px, y - py
                x, y = px + dx * math.cos(a) - dy * math.sin(a), py + dx * math.sin(a) + dy * math.cos(a)
            return x, y
        out.append(warp(canvas, src))
    return out


# ---------- 縮進殼裡 ----------
SHELL_DARK = (38, 30, 25)      # 殼裡最暗的顏色
SHELL_INNER = (74, 58, 46)     # 殼口靠外側、比較亮的顏色
SHELL_LINE = (30, 24, 20)      # 殼口描邊（接近原圖的描邊色）


def shell_hole(canvas, opening, silhouette):
    """殼口：橢圓的深色洞，上方靠殼內最暗、往外側漸亮，邊緣描一圈深色線。
    只畫在原本精靈的輪廓內（silhouette），所以不會凸出殼外；上緣和右緣會被米飯邊蓋住。"""
    cx, cy, rx, ry = opening[0] + PAD, opening[1] + PAD, opening[2], opening[3]
    box = [cx - rx, cy - ry, cx + rx, cy + ry]
    hole = Image.new("RGBA", canvas.size, SHELL_INNER + (255,))
    shade = Image.new("L", canvas.size, 0)        # 暗部：偏右上（殼的深處）
    ImageDraw.Draw(shade).ellipse([cx - rx * 0.55, cy - ry * 0.95, cx + rx * 1.25, cy + ry * 0.55], fill=255)
    hole.paste(Image.new("RGBA", canvas.size, SHELL_DARK + (255,)), mask=shade.filter(ImageFilter.GaussianBlur(rx * 0.35)))
    line = ImageDraw.Draw(hole)
    line.ellipse(box, outline=SHELL_LINE + (255,), width=3)
    mask = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(mask).ellipse([box[0] - 1, box[1] - 1, box[2] + 1, box[3] + 1], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(0.7))
    hole.putalpha(Image.composite(silhouette, Image.new("L", canvas.size, 0), mask))
    return hole, mask


def shell_frames(canvas, shell):
    """縮進殼裡：頭縮小、往殼口裡滑、越來越暗，只畫在殼口裡面，最後藏進殼口的陰影；
    頭原本的位置露出深色的殼口（只在精靈輪廓內）；腳往上縮，整隻往下沉讓殼貼地。
    圖層由下而上：殼口 → 頭 → 身體（米飯邊蓋在殼口和頭的上面）。"""
    bottom = canvas.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()[3]
    legs = shell["legs"] + PAD
    leg_h = bottom - legs
    head = shell.get("head")
    if head:
        alpha = canvas.getchannel("A")
        poly = Image.new("L", canvas.size, 0)
        ImageDraw.Draw(poly).polygon([P(pt) for pt in head["poly"]], fill=255)
        cut = poly.filter(ImageFilter.MaxFilter(5))          # 身體挖掉的範圍稍微大一點，才不會留下頭的輪廓線
        poly = poly.filter(ImageFilter.GaussianBlur(0.8))
        head_layer = canvas.copy()
        head_layer.putalpha(Image.composite(alpha, Image.new("L", canvas.size, 0), poly))
        body = canvas.copy()
        body.putalpha(Image.composite(Image.new("L", canvas.size, 0), alpha, cut))
        silhouette = alpha.point(lambda a: 255 if a > 24 else 0).filter(ImageFilter.GaussianBlur(0.6))
        hole, inside = shell_hole(canvas, shell["opening"], silhouette)
        hx0, hy0, hx1, hy1 = head_layer.getchannel("A").getbbox()
        hc = ((hx0 + hx1) / 2, (hy0 + hy1) / 2)
    out = []
    for t in (0.35, 0.7, 1.0):
        img = canvas
        if head:
            k = 1 - 0.4 * t                                  # 頭越縮越小
            tx, ty = hc[0] + head["slide"][0] * t, hc[1] + head["slide"][1] * t
            moved = head_layer.transform(
                canvas.size, Image.AFFINE, (1 / k, 0, hc[0] - tx / k, 0, 1 / k, hc[1] - ty / k), Image.BICUBIC)
            dim = 1 - 0.75 * t                               # 越往裡面越暗
            r, g, b, a = moved.split()
            r, g, b = (ch.point(lambda v, c=c: int(v * dim + c * (1 - dim))) for ch, c in zip((r, g, b), SHELL_DARK))
            a = Image.composite(a, Image.new("L", canvas.size, 0), inside)   # 只看得到殼口裡面的部分
            moved = Image.merge("RGBA", (r, g, b, a))
            img = Image.alpha_composite(Image.alpha_composite(hole, moved), body)
        sy = 1 - 0.8 * t
        shift = leg_h * (1 - sy)

        def src(x, y):
            y -= shift                                      # 整隻往下沉，殼貼地
            if y > legs:
                y = legs + (y - legs) / sy                  # 腳往上縮
            return x, y
        out.append(warp(img, src))
    return out


# ---------- 表情（眼睛） ----------
def eye_fill_color(canvas, cx, cy, rx, ry):
    """取眼睛上方一圈皮膚的顏色，用來蓋掉張開的眼睛。"""
    px = canvas.load()
    samples = []
    for i in range(48):
        a = math.pi + math.pi * i / 47           # 上半圈
        for f in (1.35, 1.55):
            x, y = int(cx + math.cos(a) * rx * f), int(cy + math.sin(a) * ry * f)
            if 0 <= x < canvas.width and 0 <= y < canvas.height and px[x, y][3] > 200:
                samples.append(px[x, y][:3])
    if not samples:
        return (230, 200, 180)
    samples.sort(key=lambda c: sum(c))
    keep = samples[len(samples) // 3:]           # 去掉偏暗的描邊
    return tuple(sorted(c[i] for c in keep)[len(keep) // 2] for i in range(3))


def draw_eyes(canvas, eyes, style):
    img = canvas.copy()
    for ex, ey, rx, ry in eyes:
        cx, cy = ex + PAD, ey + PAD
        fill = eye_fill_color(canvas, cx, cy, rx, ry)
        mask = Image.new("L", img.size, 0)
        ImageDraw.Draw(mask).ellipse([cx - rx * 1.12, cy - ry * 1.12, cx + rx * 1.12, cy + ry * 1.12], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(1.2))
        layer = Image.new("RGBA", img.size, fill + (255,))
        alpha = Image.composite(img.getchannel("A"), Image.new("L", img.size, 0), mask)
        layer.putalpha(alpha)
        img.alpha_composite(layer)

        dark = sum(fill) / 3 < 90
        ink = (235, 228, 220, 255) if dark else (58, 40, 36, 255)
        width = max(2, round(min(rx, ry) * 0.3))
        d = ImageDraw.Draw(img)
        n = 14
        if style in ("blink", "sleep"):   # ︶ 往下彎的閉眼線（睡覺更彎）
            bend = 0.38 if style == "sleep" else 0.18
            pts = [(cx + rx * u, cy + ry * (0.1 + bend * (1 - u * u))) for u in (i / n * 2 - 1 for i in range(n + 1))]
        elif style == "happy":            # ^ 開心眼
            pts = [(cx + rx * u, cy + ry * (0.25 - 0.55 * (1 - abs(u)))) for u in (i / n * 2 - 1 for i in range(n + 1))]
        else:                             # @ 暈眩的漩渦
            r0 = min(rx, ry) * 0.95
            pts = [(cx + math.cos(a) * r0 * a / (3 * math.pi), cy + math.sin(a) * r0 * a / (3 * math.pi))
                   for a in (i * 3 * math.pi / 40 for i in range(41))]
            width = max(2, width - 1)
        d.line(pts, fill=ink, width=width, joint="curve")
    return img


def save(img, path):
    img.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS).save(path, "WEBP", quality=90, method=6)


def make(name):
    rig = RIG.get(name, {"eyes": [], "parts": []})
    src = Image.open(SRC / f"{name}.png").convert("RGBA")
    canvas = Image.new("RGBA", (src.width + PAD * 2,) * 2, (0, 0, 0, 0))
    canvas.paste(src, (PAD, PAD))
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("*.webp"):
        old.unlink()
    made = {}

    for i, f in enumerate(walk_frames(canvas)):
        save(f, d / f"walk_{i}.webp")
    made["walk"] = 8
    for anim in ("fidget", "flap", "punch"):
        parts = [p for p in rig["parts"] if p["anim"] == anim]
        if parts:
            for i, f in enumerate(part_frames(canvas, parts)):
                save(f, d / f"{anim}_{i}.webp")
            made[anim] = LOOP
    eyes = rig.get("eyes", [])
    if eyes:
        for style in ("blink", "sleep", "happy", "dizzy"):
            save(draw_eyes(canvas, eyes, style), d / f"{style}.webp")
        made["eyes"] = 4
    if rig.get("shell"):
        for i, f in enumerate(shell_frames(canvas, rig["shell"])):
            save(f, d / f"shell_{i}.webp")
        base = draw_eyes(canvas, eyes, "sleep") if eyes else canvas
        save(shell_frames(base, rig["shell"])[-1], d / "shell_sleep.webp")
        made["shell"] = 4
    return made


def main():
    names = sys.argv[1:] or sorted(k for k in RIG if not k.startswith("_"))
    total = 0
    for name in names:
        made = make(name)
        total += sum(made.values())
        print(name, " ".join(f"{k}×{v}" for k, v in made.items()))
    print(f"共 {total} 張")


if __name__ == "__main__":
    main()
