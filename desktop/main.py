"""學習精靈 桌面測試版

- 主視窗：用 QWebEngineView 載入 app/learning-spirit.html（做題、倉庫、對戰都在這裡）
- 桌面寵物：桌面隊伍的每隻精靈各是一個透明小視窗，在工作列上方走來走去
  - 自己會待機呼吸、走路、奔跑、跳、東張西望、睡覺、跳舞
  - 走近別隻時互動（同種 ❤、同屬性 ✦、心情不好 …、其他 ♪），兩隻各說一句話，然後各自走開
  - 動作圖在 art/spirits/frames/（由 tools/make_frames.py 依 art/spirits/rig.json 產生）：
    走路 8 張（依走過的距離換圖，腳步不滑）、眨眼、睡覺閉眼、開心 ^ ^、暈 @ @、
    尾巴／耳朵擺動、拍翅膀、出拳、縮進殼裡
  - 答對題目時開心跳一下，升級轉圈，進化時大轉圈加星光
  - 點寵物：說話＋冒愛心（睡著會被嚇醒）；頭上有 ❗ 時會興奮跳，點牠開啟主視窗做額外題目
  - 可以用滑鼠抓起來晃、甩出去；從太高的地方掉下來會暈
- 系統匣圖示：開啟主視窗、顯示／隱藏寵物、結束
- 關閉主視窗只會縮到系統匣，寵物繼續留在桌面

遊戲狀態全部在網頁裡（localStorage），這支程式每 0.4 秒讀一次桌面隊伍來同步。
存檔位置：%LOCALAPPDATA%\\LearningSpirit
"""
import json
import math
import os
import random
import sys
import time
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPainterPath, QPixmap
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QSystemTrayIcon, QWidget

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "app" / "learning-spirit.html"
ICON = ROOT / "art" / "logo.ico"
DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "LearningSpirit"

# 網頁內的桌面列由真正的桌面寵物取代，所以藏起來
HIDE_DESK_JS = """
(function(){
  const st = document.createElement('style');
  st.textContent = '#desk{display:none!important} body{padding-bottom:24px!important}';
  document.head.appendChild(st);
})();
"""

POLL_JS = """
(function(){
  if (typeof S === 'undefined' || !S) return null;
  if (S.pure) return JSON.stringify([]);
  return JSON.stringify(deskPets().map(p => ({
    id: p.id,
    src: new URL(spriteSrc(p.sp, p.stage), location.href).href,
    name: petName(p), lv: level(p.xp), xp: p.xp, face: mood(p).f,
    sp: p.sp, cat: SP[p.sp].cat, catName: CATS[SP[p.sp].cat].name,
    alert: S.extraPet === p.id,
    say: sayPet === p.id ? sayText : ''
  })));
})();
"""

CLICK_JS = """
(function(id){
  if (typeof S === 'undefined' || !S) return '';
  if (S.extraPet === id) { startExtra(); return 'extra'; }
  const p = S.pets.find(p => p.id === id);
  if (p) say(id, pick(mood(p).say));
  return 'say';
})(%d);
"""

W, H = 190, 190          # 寵物視窗大小
SPRITE = 96              # 精靈圖大小
BUBBLE_H = 54            # 對話框區域高度
BASE = BUBBLE_H + 8 + SPRITE   # 精靈腳底在視窗內的 y
FPS = 60
GRAVITY = 1000.0         # px/s²
WALK_SPEED, RUN_SPEED = 42.0, 125.0   # px/s
STRIDE = 30.0            # 走路圖播完一輪（8 張）前進的距離（px），腳步跟移動速度對得上才不會滑步
NATIVE_FACING = -1       # 原圖大多面向左邊
FRAMES_DIR = ROOT / "art" / "spirits" / "frames"   # 動作圖（tools/make_frames.py 產生）
FRAME_PAD = 16 / 256     # 動作圖比原圖四周多的留白比例
SYMBOL_FONT = "Segoe UI Symbol"

# 寵物之間：靠近時互動（原型值；寵物可以互相重疊）
GREET_DIST = 110         # 走近到這個距離內就互動（px）
PAIR_CD = 45.0           # 同一對互動完，這麼多秒內不再互動
SAY_SEC = 2.8            # 互動對話框顯示秒數

# 自己決定下一個動作時的權重（心情不好時比較愛睡）
ACTIONS = {"idle": 24, "walk": 40, "run": 6, "hop": 8, "look": 9, "sleep": 5, "dance": 5, "flex": 6}
HIDE_WEIGHT = 7          # 有殼的精靈（糰糰、飯盒獸、御膳獸）縮進殼裡的權重
DURATION = {  # 各動作持續秒數（最短、最長）
    "idle": (1.5, 4), "walk": (3, 9), "run": (1.5, 3), "look": (2, 3.5), "sleep": (9, 16),
    "dance": (3.3, 3.3), "dizzy": (2.7, 2.7), "greet": (2, 2), "excited": (1.7, 1.7),
    "flex": (2, 3), "hide": (4, 8),
}
SHELL_IN = 0.45          # 縮進殼／探出頭花的秒數


def ease(rate, dt):
    """每秒以 rate 的速度靠近目標時，這一格要走的比例（跟 FPS 無關）。"""
    return 1 - math.exp(-rate * dt)


class Particle:
    __slots__ = ("text", "x", "y", "vx", "vy", "life", "max", "size", "color", "kind")

    def __init__(self, text, x, y, vx, vy, life, size, color, kind="text"):
        self.text, self.x, self.y, self.vx, self.vy = text, x, y, vx, vy
        self.life = self.max = life
        self.size, self.color, self.kind = size, QColor(color), kind


class PetWindow(QWidget):
    """一隻桌面寵物。動作：待機呼吸、眨眼、擺尾巴／耳朵、走路（8 張走路圖）、奔跑、跳躍、東張西望、
    睡覺（閉眼）、跳舞、拍翅膀、出拳、縮進殼裡、被點擊開心（^ ^ 眼）、被拖著晃、被丟出去、
    摔暈（@ @ 眼）、升級轉圈、和別的寵物打招呼、有額外題時興奮跳。
    移動都用「每秒多少 px」計算，加速、減速、轉身前先停下來，所以不會滑步或倒退走。"""

    def __init__(self, manager, pid):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.resize(W, H)
        self.manager, self.pid = manager, pid
        self.data, self.src, self.pix = {}, None, QPixmap()
        self.fr, self.walk, self.loops, self.shell = {}, [], {}, []   # 動作圖
        self.expr_until = 0.0                      # 開心表情（^ ^ 眼）到什麼時候
        self.blink_until, self.next_blink = 0.0, random.uniform(1, 4)
        self.thrown = False
        area = QApplication.primaryScreen().availableGeometry()
        self.x = random.uniform(area.left(), area.right() - W)
        self.y = float(self.ground())
        self.vx = self.vy = 0.0           # 空中速度（px/s）
        self.speed = 0.0                  # 地面行走速度（px/s，不分方向）
        self.air = False
        self.facing = random.choice([-1, 1])   # 1 往右、-1 往左
        self.want_facing = self.facing
        self.dist = 0.0                   # 走過的距離，決定走路圖播到第幾張
        self.angle = 0.0
        self.spin = 0.0                   # 空中轉圈角速度（度/s）
        self.squash = 0.0                 # >0 壓扁、<0 拉長
        self.clock = random.uniform(0, 10)
        self.parts = []
        self.acc = {}
        self.greet_cd = random.uniform(3, 10)
        self.away = 1                     # 互動完要走開的方向
        self.say_text, self.say_t, self.say_wait = "", 0.0, 0.0   # 互動時自己說的話（不經過網頁）
        self.state, self.t, self.dur = "idle", 0.0, random.uniform(1, 3)
        self.dragging, self.drag_off, self.press_pos = False, QPoint(), None
        self.drag_v = [0.0, 0.0]
        self.last_gp, self.last_drag_t = QPoint(), 0.0
        self.move(round(self.x), round(self.y))

    def ground(self):
        return QApplication.primaryScreen().availableGeometry().bottom() - H + 1

    # ---- 資料同步：答對、升級、進化時有反應 ----
    def load_images(self):
        path = QUrl(self.src).toLocalFile()
        self.pix = QPixmap(path).scaled(SPRITE, SPRITE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        size = round(SPRITE * (1 + 2 * FRAME_PAD))
        self.fr = {f.stem: QPixmap(str(f)).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                   for f in (FRAMES_DIR / Path(path).stem).glob("*.webp")}

        def seq(prefix):
            keys = sorted((k for k in self.fr if k.startswith(prefix + "_") and k[len(prefix) + 1:].isdigit()),
                          key=lambda k: int(k.rsplit("_", 1)[1]))
            return [self.fr[k] for k in keys]
        self.walk = seq("walk")
        self.loops = {k: v for k in ("fidget", "flap", "punch") if (v := seq(k))}
        self.shell = seq("shell")

    def update_data(self, d):
        old = self.data
        if d["src"] != self.src:
            evolved = self.src is not None
            self.src = d["src"]
            self.load_images()
            if evolved:
                self.celebrate(big=True)
        elif old:
            if d.get("lv", 0) > old.get("lv", 0):
                self.celebrate()
            elif d.get("xp", 0) > old.get("xp", 0) and not self.dragging and self.state not in ("sleep", "hide"):
                self.jump(-230, 0)
                self.emit("♪", "#3f7d5c", n=2)
                self.smile(0.9)
        if d != old:
            self.data = d
            self.update()

    # ---- 動作控制 ----
    def set_state(self, s, dur=None):
        self.state, self.t, self.acc = s, 0.0, {}
        lo, hi = DURATION.get(s, (99, 99))
        self.dur = dur if dur is not None else random.uniform(lo, hi)
        if s in ("walk", "run") and random.random() < 0.45:
            self.want_facing = -self.facing          # 轉身：先減速停下，再轉過去
        if s not in ("walk", "run", "idle", "hop"):
            self.speed = 0.0                         # 原地動作：先站定，避免邊滑邊轉身
        if s == "hop":
            self.jump(-300, self.facing * 55)
        if s == "dance":
            self.emit("♪", "#7a62b8", n=1)

    def smile(self, sec):
        self.expr_until = self.clock + sec

    def choose_next(self):
        if self.data.get("alert"):
            return self.set_state("excited")
        w = dict(ACTIONS)
        if self.data.get("face", "😊") != "😊":
            w["sleep"] *= 4
            w["dance"] = 1
        if self.shell:
            w["hide"] = HIDE_WEIGHT
        if not self.loops:                  # 沒有翅膀、手、尾巴可以動的就不做這個動作
            w["flex"] = 0
        self.set_state(random.choices(list(w), weights=list(w.values()))[0])

    def every(self, key, period):
        """每 period 秒回傳一次 True。"""
        a = self.acc.get(key, 0.0) + self.dt
        if a >= period:
            self.acc[key] = a - period
            return True
        self.acc[key] = a
        return False

    def jump(self, vy, vx):
        if self.air:
            return
        self.air, self.vy, self.vx = True, vy, vx
        self.speed = 0.0
        self.squash = -0.18

    def celebrate(self, big=False):
        self.angle = 0.0
        self.set_state("spin", 99)
        self.air = False
        self.jump(-400 if big else -340, 0)
        self.spin = 420.0
        self.smile(2.0)
        self.emit("✦", "#f2b632", n=12 if big else 6, spread=150)
        self.emit("進化！" if big else "Lv UP!", "#d9822b", n=1, size=11, vy=-36)

    def emit(self, text, color, n=1, spread=75, size=None, vy=None, kind="text"):
        cx, cy = W / 2, BASE - SPRITE * 0.75
        for _ in range(n):
            self.parts.append(Particle(
                text, cx + random.uniform(-20, 20), cy + random.uniform(-10, 10),
                random.uniform(-spread, spread), vy if vy is not None else random.uniform(-85, -36),
                random.uniform(0.9, 1.5), size or random.randint(10, 15), color, kind))

    def dust(self, n=3):
        for _ in range(n):
            self.parts.append(Particle("", W / 2 - self.facing * 22 + random.uniform(-8, 8), BASE - 4,
                                       -self.facing * random.uniform(10, 36), random.uniform(-18, -3),
                                       random.uniform(0.45, 0.7), random.randint(5, 9), "#b8b0a0", "dust"))

    def poke(self):
        """被點一下：睡著就驚醒；縮在殼裡就探出頭；不然開心跳一下冒愛心。"""
        if self.state == "hide":
            self.t = max(self.t, self.dur - SHELL_IN)
            self.emit("?", "#6a7fa8", n=1, size=14, vy=-40)
            return
        if self.state == "sleep":
            self.angle = 0.0
            self.set_state("idle", 1.3)
            self.jump(-260, 0)
            self.emit("!", "#c0392b", n=1, size=16, vy=-45)
            return
        self.set_state("idle", 1.7)
        self.jump(-260, 0)
        self.emit("❤", "#e2557a", n=3)
        self.smile(1.4)

    def greet(self, other, symbol, color, n, line, wait=0.0):
        """和走近的寵物互動：轉向對方、跳一下、冒符號、說一句話；結束後往反方向走開。"""
        self.facing = self.want_facing = 1 if other.x > self.x else -1
        self.away = -self.facing
        self.speed = 0.0
        self.set_state("greet")
        self.jump(-200, 0)
        self.emit(symbol, color, n=n, vy=-48)
        self.say_text, self.say_wait, self.say_t = line, wait, SAY_SEC
        if symbol != "…":
            self.smile(1.6)

    @property
    def grounded(self):
        return not self.air and not self.dragging

    # ---- 每一格 ----
    def step(self, dt):
        self.dt = dt
        self.t += dt
        self.clock += dt
        self.squash *= math.exp(-7 * dt)
        self.greet_cd = max(0.0, self.greet_cd - dt)
        if self.clock >= self.next_blink:   # 眨眼：每 2～6 秒一次，偶爾連眨兩下
            self.blink_until = self.clock + 0.14
            self.next_blink = self.clock + (0.3 if random.random() < 0.2 else random.uniform(2, 6))
        if self.say_wait > 0:
            self.say_wait = max(0.0, self.say_wait - dt)
        elif self.say_t > 0:
            self.say_t = max(0.0, self.say_t - dt)
        self.step_particles(dt)

        if self.dragging:                   # 被抓著：跟著滑鼠方向晃
            target = max(-40.0, min(40.0, -self.drag_v[0] * 0.09))
            self.angle += (target - self.angle) * ease(9, dt)
            self.drag_v = [v * math.exp(-6 * dt) for v in self.drag_v]
            self.update()
            return

        area = QApplication.primaryScreen().availableGeometry()
        g = self.ground()
        left, right = area.left(), area.right() - W

        if self.air or self.y < g:          # 空中：重力、轉圈、撞牆反彈
            self.air = True
            self.vy += GRAVITY * dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            if self.spin:
                self.angle = (self.angle + self.spin * dt) % 360
            else:
                self.angle *= math.exp(-5 * dt)
            if self.x < left or self.x > right:
                self.x = max(left, min(self.x, right))
                self.vx = -self.vx * 0.6
                self.facing = self.want_facing = 1 if self.vx > 0 else -1
            if self.y >= g:                 # 落地
                impact = self.vy
                self.y, self.vy, self.vx, self.air = g, 0.0, 0.0, False
                self.angle, self.spin = 0.0, 0.0
                self.squash = min(0.4, impact / 1350)
                if impact > 180:
                    self.dust(4)
                if impact > 720:            # 從很高的地方掉下來 → 暈
                    self.set_state("dizzy")
                elif self.thrown and self.shell:   # 有殼的被丟：先躲在殼裡一下
                    self.set_state("hide", 2.5)
                    self.t = SHELL_IN
                elif self.state in ("hop", "spin"):
                    self.choose_next()
                self.thrown = False
        else:
            self.y = g
            self.ground_action(left, right, dt)

        self.move(round(self.x), round(self.y))
        self.update()

    def ground_action(self, left, right, dt):
        s = self.state
        target = {"walk": WALK_SPEED, "run": RUN_SPEED}.get(s, 0.0)
        if self.want_facing != self.facing:  # 要轉身：先停下來
            target = 0.0
            if self.speed < 4:
                self.facing = self.want_facing
                self.squash = 0.08
        self.speed += (target - self.speed) * ease(4.5 if target else 6, dt)
        if self.speed < 0.5 and not target:
            self.speed = 0.0
        if self.speed:
            nx = self.x + self.facing * self.speed * dt
            if nx <= left or nx >= right:   # 快撞到螢幕邊：停下來轉身
                nx = max(left, min(nx, right))
                self.want_facing = -self.facing
            self.dist += abs(nx - self.x)
            self.x = nx
            if s == "run" and self.every("dust", 0.17):
                self.dust(1)

        if s == "look" and self.every("look", 1.0):     # 東張西望
            self.facing = self.want_facing = -self.facing
        elif s == "sleep":
            self.angle += (10 * self.facing - self.angle) * ease(1.5, dt)
            if self.every("z", 1.3):
                self.parts.append(Particle("Z", W / 2 + 26 * self.facing, BASE - SPRITE * 0.85,
                                           15 * self.facing, -24, 2.0, random.randint(13, 18), "#3d5a99"))
        elif s == "dance":
            self.angle = math.sin(self.t * 10.5) * 14
            if self.every("hop", 0.83):
                self.jump(-170, 0)
                self.emit("♪", "#7a62b8", n=1)
            if self.every("turn", 0.6):
                self.facing = self.want_facing = -self.facing
        elif s == "dizzy":
            self.angle = math.sin(self.t * 12) * 8
            if self.every("star", 0.33):
                self.parts.append(Particle("✦", W / 2 + math.cos(self.t * 9) * 26, BASE - SPRITE - 4,
                                           0, 0, 0.45, 11, "#f2b632"))
        elif s == "greet":
            if self.t < 1.6 and self.every("hop", 0.66):
                self.jump(-160, 0)
        elif s == "flex":                   # 拍翅膀／出拳／甩尾巴
            if "punch" in self.loops and self.every("pow", 0.6):
                self.parts.append(Particle("✦", W / 2 + self.facing * 40, BASE - SPRITE * 0.45,
                                           0, -10, 0.35, 12, "#d9822b"))
            elif "flap" in self.loops and self.every("hop", 1.0):
                self.jump(-150, 0)
        elif s == "excited":                # 有額外題：原地興奮跳
            if self.every("hop", 0.73):
                self.jump(-230, 0)
                self.emit("!", "#c0392b", n=1, size=14, vy=-42)
        if s not in ("sleep", "dance", "dizzy"):
            self.angle *= math.exp(-7 * dt)

        if self.t >= self.dur:
            if s == "greet":                # 互動完：往反方向走開
                self.set_state("walk", random.uniform(2, 4))
                self.want_facing = self.away
                return
            if s in ("walk", "run") and self.speed > 4:   # 走路結束：先慢慢停下
                self.state = "idle"
                self.dur = self.t + random.uniform(1, 3)
                return
            if s == "sleep":
                self.angle = 0.0
                self.emit("!", "#6a7fa8", n=1, size=13)
            self.choose_next()
        elif self.data.get("alert") and s not in ("excited", "dizzy", "spin"):
            self.set_state("excited")

    def step_particles(self, dt):
        for q in self.parts:
            q.x += q.vx * dt
            q.y += q.vy * dt
            if q.kind == "text":
                q.vy += 27 * dt
            q.life -= dt
        self.parts = [q for q in self.parts if q.life > 0]

    # ---- 選這一格要畫哪張動作圖（None 就畫原圖） ----
    def loop(self, key, fps):
        fr = self.loops.get(key)
        return fr[int(self.clock * fps) % len(fr)] if fr else None

    def pick_frame(self, walking):
        s, f = self.state, self.fr
        if self.dragging:                   # 被抓起來：有殼就縮進去，有翅膀就亂拍
            return (self.shell[-1] if self.shell else None) or self.loop("flap", 20) or self.loop("fidget", 14)
        if s == "sleep":
            return f.get("shell_sleep") or f.get("sleep")
        if s == "dizzy":
            return f.get("dizzy")
        if s == "hide" and self.shell:      # 縮進去 → 躲著 → 探出來
            k = min(self.t, max(0.0, self.dur - self.t)) / SHELL_IN
            return self.shell[min(len(self.shell) - 1, int(k * len(self.shell)))]
        if walking and self.walk:
            return self.walk[int(self.dist / STRIDE * len(self.walk)) % len(self.walk)]
        smiling = self.clock < self.expr_until
        if self.air:
            return self.loop("flap", 16) or (f.get("happy") if smiling else None)
        if s == "flex":
            return self.loop("punch", 9) or self.loop("flap", 14) or self.loop("fidget", 12)
        if s in ("dance", "excited"):
            return self.loop("flap", 14) or f.get("happy")
        if smiling:
            return f.get("happy")
        if self.clock < self.blink_until:
            return f.get("blink")
        if s in ("idle", "look", "greet") and self.clock % 6 < 2.6:   # 每隔幾秒擺一下尾巴／耳朵
            return self.loop("fidget", 9)
        return None

    # ---- 繪圖 ----
    def paintEvent(self, _):
        if self.pix.isNull():
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        d, s = self.data, self.state

        walking = self.speed > 0.5 and not self.air and not self.dragging
        sx = sy = 1.0
        bob = 0.0
        if walking and not self.walk:       # 沒有走路圖時，用上下起伏代替
            bob = abs(math.sin(self.dist / STRIDE * math.pi * 2)) * 4
        elif s == "sleep":
            k = math.sin(self.clock * 1.8) * 0.035
            sx, sy = 1 + k, 1 - k
        elif not self.air and not walking:  # 待機呼吸
            k = math.sin(self.clock * 3.6) * 0.02
            sx, sy = 1 - k, 1 + k
        sx *= 1 + self.squash
        sy *= 1 - self.squash

        p.save()
        if self.dragging:                   # 抓著頭：以頭頂為支點晃
            p.translate(W / 2, BASE - SPRITE)
            p.rotate(self.angle)
            p.translate(0, SPRITE)
        elif self.spin or s == "spin":      # 轉圈：以中心為支點
            p.translate(W / 2, BASE - SPRITE / 2)
            p.rotate(self.angle)
            p.translate(0, SPRITE / 2)
        else:                               # 其他：以腳底為支點
            p.translate(W / 2, BASE - bob)
            p.rotate(self.angle)
        p.scale(self.facing * NATIVE_FACING * sx, sy)
        frame = self.pick_frame(walking)
        if frame is not None:
            pad = SPRITE * FRAME_PAD
            p.drawPixmap(QPointF(-SPRITE / 2 - pad, -SPRITE - pad), frame)
        else:
            p.drawPixmap(QPointF(-SPRITE / 2, -SPRITE), self.pix)
        p.restore()

        # 粒子：愛心、音符、星星、Zz、灰塵
        for q in self.parts:
            a = max(0, min(255, int(255 * q.life / q.max)))
            c = QColor(q.color)
            c.setAlpha(a)
            if q.kind == "dust":
                p.setPen(Qt.NoPen)
                c.setAlpha(a // 2)
                p.setBrush(c)
                r = q.size * (1.5 - q.life / q.max)
                p.drawEllipse(QRectF(q.x - r, q.y - r, r * 2, r * 2))
            else:
                f = QFont(SYMBOL_FONT, q.size)
                f.setBold(True)
                p.setFont(f)
                rect = QRectF(q.x - 40, q.y - 15, 80, 30)
                halo = QColor(255, 255, 255, a * 3 // 4)   # 白色外框，深色桌布上也看得到
                p.setPen(halo)
                for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    p.drawText(rect.translated(ox, oy), Qt.AlignCenter, q.text)
                p.setPen(c)
                p.drawText(rect, Qt.AlignCenter, q.text)

        # 名字牌（睡覺、暈的時候換表情）
        f = QFont("Microsoft JhengHei", 8)
        f.setBold(True)
        p.setFont(f)
        face = "😴" if s in ("sleep",) else "😵" if s == "dizzy" else "🙈" if s == "hide" else d.get("face", "")
        label = f"{face} {d.get('name', '')} Lv.{d.get('lv', 1)}"
        tw = p.fontMetrics().horizontalAdvance(label) + 14
        r = QRectF((W - tw) / 2, H - 24, tw, 20)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(30, 45, 65, 200))
        p.drawRoundedRect(r, 10, 10)
        p.setPen(QColor("white"))
        p.drawText(r, Qt.AlignCenter, label)

        # 對話框
        own = self.say_text if self.say_t > 0 and self.say_wait == 0 else ""
        text = "❗ 我身上有額外題目！點我～" if d.get("alert") else own or d.get("say", "")
        if text:
            f = QFont("Microsoft JhengHei", 9)
            p.setFont(f)
            br = p.fontMetrics().boundingRect(0, 0, W - 28, 200, Qt.TextWordWrap, text)
            bw, bh = br.width() + 18, br.height() + 12
            box = QRectF((W - bw) / 2, BUBBLE_H - bh - 2, bw, bh)
            path = QPainterPath()
            path.addRoundedRect(box, 10, 10)
            tail = QPainterPath()
            cx = W / 2
            tail.moveTo(cx - 7, box.bottom() - 1)
            tail.lineTo(cx, box.bottom() + 8)
            tail.lineTo(cx + 7, box.bottom() - 1)
            path = path.united(tail)
            alert = d.get("alert")
            p.setPen(QColor("#c0392b") if alert else QColor("#8a9bb0"))
            p.setBrush(QColor("#fff4e5") if alert else QColor("white"))
            p.drawPath(path)
            p.setPen(QColor("#222"))
            p.drawText(box.adjusted(9, 6, -9, -6), Qt.TextWordWrap | Qt.AlignCenter, text)
        p.end()

    # ---- 滑鼠：點擊、拖曳、丟出去 ----
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.press_pos = e.globalPosition().toPoint()
            self.drag_off = self.press_pos - self.pos()
            self.last_gp, self.last_drag_t = self.press_pos, time.perf_counter()
        elif e.button() == Qt.RightButton:
            self.manager.tray_menu.popup(e.globalPosition().toPoint())

    def mouseMoveEvent(self, e):
        if self.press_pos is None:
            return
        gp = e.globalPosition().toPoint()
        if not self.dragging and (gp - self.press_pos).manhattanLength() > 6:
            self.dragging = True
            self.air, self.spin, self.speed = False, 0.0, 0.0
            if self.state == "sleep":
                self.set_state("idle")
            self.emit("!", "#c0392b", n=1, size=14, vy=-42)
        if self.dragging:
            now = time.perf_counter()
            dt = max(0.004, now - self.last_drag_t)
            dv = gp - self.last_gp
            self.drag_v = [self.drag_v[0] * 0.5 + dv.x() / dt * 0.5, self.drag_v[1] * 0.5 + dv.y() / dt * 0.5]
            self.last_gp, self.last_drag_t = gp, now
            np = gp - self.drag_off
            self.x, self.y = float(np.x()), float(min(np.y(), self.ground()))
            self.move(round(self.x), round(self.y))

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        if self.dragging:                   # 放手：帶著滑鼠速度丟出去
            self.dragging = False
            self.thrown = True
            self.state, self.t, self.dur, self.acc = "hop", 0.0, 99, {}   # 落地後再決定下一個動作
            self.air = True
            self.vx = max(-550.0, min(550.0, self.drag_v[0]))
            self.vy = max(-550.0, min(550.0, self.drag_v[1]))
            if abs(self.vx) > 30:
                self.facing = self.want_facing = 1 if self.vx > 0 else -1
        else:
            self.poke()
            self.manager.pet_clicked(self.pid)
        self.press_pos = None


class MainWindow(QMainWindow):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setWindowTitle("學習精靈（測試版）")
        self.setWindowIcon(QIcon(str(ICON)))
        self.resize(1180, 820)

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.profile = QWebEngineProfile("learning-spirit", self)
        self.profile.setPersistentStoragePath(str(DATA_DIR / "storage"))
        self.profile.setCachePath(str(DATA_DIR / "cache"))
        self.view = QWebEngineView(self)
        self.page = QWebEnginePage(self.profile, self.view)
        self.view.setPage(self.page)
        self.setCentralWidget(self.view)
        self.page.loadFinished.connect(lambda ok: ok and self.page.runJavaScript(HIDE_DESK_JS))
        self.view.load(QUrl.fromLocalFile(str(HTML)))

    def closeEvent(self, e):
        e.ignore()
        self.hide()
        self.manager.tray.showMessage("學習精靈", "已縮到系統匣，寵物還在桌面上陪你。",
                                      QSystemTrayIcon.Information, 2500)

    def bring_up(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()


class Manager:
    def __init__(self, app):
        self.app = app
        self.pets = {}
        self.pair_cd = {}   # frozenset({id, id}) → 這一對下次可以再互動的時間
        self.pets_visible = True
        self.win = MainWindow(self)

        self.tray = QSystemTrayIcon(QIcon(str(ICON)), app)
        self.tray.setToolTip("學習精靈")
        self.tray_menu = QMenu()
        a_open = QAction("開啟學習精靈", self.tray_menu)
        a_open.triggered.connect(self.win.bring_up)
        self.a_toggle = QAction("隱藏桌面寵物", self.tray_menu)
        self.a_toggle.triggered.connect(self.toggle_pets)
        a_quit = QAction("結束", self.tray_menu)
        a_quit.triggered.connect(app.quit)
        for a in (a_open, self.a_toggle):
            self.tray_menu.addAction(a)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(a_quit)
        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(
            lambda r: r in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick) and self.win.bring_up())
        self.tray.show()

        self.poll_timer = QTimer(interval=400, timeout=self.poll)
        self.poll_timer.start()
        self.last_tick = time.perf_counter()
        self.walk_timer = QTimer(interval=1000 // FPS, timeout=self.walk)
        self.walk_timer.setTimerType(Qt.PreciseTimer)   # 60 fps，動作才順
        self.walk_timer.start()
        self.win.show()

    def poll(self):
        self.win.page.runJavaScript(POLL_JS, 0, self.sync)

    def sync(self, result):
        if result is None:
            return
        data = json.loads(result)
        ids = {d["id"] for d in data}
        for pid in list(self.pets):
            if pid not in ids:
                self.pets.pop(pid).deleteLater()
        for d in data:
            w = self.pets.get(d["id"])
            if w is None:
                w = self.pets[d["id"]] = PetWindow(self, d["id"])
                if self.pets_visible:
                    w.show()
            w.update_data(d)

    def walk(self):
        if not self.pets_visible:
            return
        now = time.perf_counter()
        dt = min(0.05, now - self.last_tick)    # 電腦卡住時不要一次跳太遠
        self.last_tick = now
        pets = list(self.pets.values())
        for w in pets:
            w.step(dt)
        # 走近別隻時互動（同一對 PAIR_CD 秒內不重複）
        now = time.monotonic()
        free = [w for w in pets if w.grounded and w.greet_cd == 0
                and w.state in ("walk", "idle", "look", "run")]
        for i, a in enumerate(free):
            for b in free[i + 1:]:
                if a.state == "greet" or b.state == "greet" or abs(a.x - b.x) > GREET_DIST:
                    continue
                if not (self.approaching(a, b) or self.approaching(b, a)):
                    continue
                key = frozenset((a.pid, b.pid))
                if now < self.pair_cd.get(key, 0):
                    continue
                self.pair_cd[key] = now + PAIR_CD
                self.react(a, b)
                a.greet_cd = b.greet_cd = random.uniform(12, 20)

    @staticmethod
    def approaching(a, b):
        """a 正朝 b 走過去。"""
        toward = 1 if b.x > a.x else -1
        return a.speed > 1 and a.facing == toward and a.want_facing == toward

    def react(self, a, b):
        """依兩隻的關係決定互動：同種 ❤、同屬性 ✦（對戰有羈絆）、心情不好 …、其他 ♪。"""
        da, db = a.data, b.data
        na, nb = da.get("name", ""), db.get("name", "")
        if da.get("sp") and da.get("sp") == db.get("sp"):
            sym, color, n, la, lb = "❤", "#e2557a", 3, f"是另一隻{nb}耶！", "我們是同一種！"
        elif da.get("cat") and da.get("cat") == db.get("cat"):
            sym, color, n, la, lb = "✦", "#f2b632", 4, f"同樣是{da.get('catName', '')}屬性！", "一起出戰有羈絆加成！"
        elif da.get("face", "😊") != "😊":
            sym, color, n, la, lb = "…", "#6a7fa8", 1, "主人好久沒來了…", "我們一起等主人吧"
        else:
            sym, color, n = "♪", "#3f7d5c", 2
            la, lb = random.choice([(f"嗨，{nb}！", f"嗨～{na}！"), ("你今天學了幾個字？", "我學了好多！"),
                                    ("一起玩吧！", "好啊！"), ("比賽誰先長大！", "我才不會輸！")])
        a.greet(b, sym, color, n, la)
        b.greet(a, sym, color, n, lb, wait=1.0)   # 對方晚一點回話

    def pet_clicked(self, pid):
        def done(r):
            if r == "extra":
                self.win.bring_up()
            self.poll()
        self.win.page.runJavaScript(CLICK_JS % pid, 0, done)

    def toggle_pets(self):
        self.pets_visible = not self.pets_visible
        for w in self.pets.values():
            w.setVisible(self.pets_visible)
        self.a_toggle.setText("隱藏桌面寵物" if self.pets_visible else "顯示桌面寵物")


def main():
    if sys.platform == "win32":  # 讓工作列顯示學習精靈的圖示，而不是 Python 的
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("LearningSpirit.Desktop")
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationName("LearningSpirit")
    app.setWindowIcon(QIcon(str(ICON)))
    app.setQuitOnLastWindowClosed(False)
    _m = Manager(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
