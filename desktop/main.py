"""學習精靈 桌面測試版

- 主視窗：用 QWebEngineView 載入 app/learning-spirit.html（做題、倉庫、對戰都在這裡）
- 桌面寵物：桌面隊伍的每隻精靈各是一個透明小視窗，在工作列上方走來走去
  - 點寵物：說話；頭上有 ❗ 時點牠，開啟主視窗做額外題目
  - 可以用滑鼠拖曳，放開後會掉回地面
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
from pathlib import Path

from PySide6.QtCore import QPoint, QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPainterPath, QPixmap
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QSystemTrayIcon, QWidget

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "app" / "learning-spirit.html"
ICON = ROOT / "art" / "spirits" / "abc-1.png"
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
    name: petName(p), lv: level(p.xp), face: mood(p).f,
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


class PetWindow(QWidget):
    def __init__(self, manager, pid):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.resize(W, H)
        self.manager, self.pid = manager, pid
        self.data, self.src, self.pix = {}, None, QPixmap()
        area = QApplication.primaryScreen().availableGeometry()
        self.x = random.uniform(area.left(), area.right() - W)
        self.y = float(self.ground())
        self.vx, self.vy = 0.0, 0.0
        self.pause = random.randint(20, 80)
        self.phase = random.uniform(0, 6.28)
        self.dragging, self.drag_off, self.press_pos = False, QPoint(), None
        self.move(int(self.x), int(self.y))

    def ground(self):
        return QApplication.primaryScreen().availableGeometry().bottom() - H + 1

    def update_data(self, d):
        if d["src"] != self.src:
            self.src = d["src"]
            pix = QPixmap(QUrl(self.src).toLocalFile())
            self.pix = pix.scaled(SPRITE, SPRITE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if d != self.data:
            self.data = d
            self.update()

    # ---- 移動 ----
    def step(self):
        if self.dragging:
            return
        area = QApplication.primaryScreen().availableGeometry()
        g = self.ground()
        if self.y < g:                       # 被拖到半空中：掉下來
            self.vy += 1.2
            self.y = min(g, self.y + self.vy)
        else:
            self.y, self.vy = g, 0.0
            if self.pause > 0:
                self.pause -= 1
                self.vx = 0.0
            elif self.vx == 0.0:
                self.vx = random.choice([-1, 1]) * random.uniform(0.8, 1.6)
            else:
                self.x += self.vx
                if random.random() < 0.006:  # 偶爾停下來
                    self.pause = random.randint(40, 160)
        if self.x < area.left() or self.x > area.right() - W:
            self.x = max(area.left(), min(self.x, area.right() - W))
            self.vx = -self.vx
        self.phase += 0.25 if self.vx else 0.06
        self.move(int(self.x), int(self.y))
        self.update()

    # ---- 繪圖 ----
    def paintEvent(self, _):
        if self.pix.isNull():
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        d = self.data
        bob = abs(math.sin(self.phase)) * (5 if self.vx else 2)

        # 精靈（往左走時水平翻轉）
        sx = (W - SPRITE) / 2
        sy = BUBBLE_H + 8 - bob
        if self.vx < 0:
            p.save()
            p.translate(sx + SPRITE, sy)
            p.scale(-1, 1)
            p.drawPixmap(0, 0, self.pix)
            p.restore()
        else:
            p.drawPixmap(int(sx), int(sy), self.pix)

        # 名字牌
        f = QFont("Microsoft JhengHei", 8)
        f.setBold(True)
        p.setFont(f)
        label = f"{d.get('face', '')} {d.get('name', '')} Lv.{d.get('lv', 1)}"
        tw = p.fontMetrics().horizontalAdvance(label) + 14
        r = QRectF((W - tw) / 2, H - 24, tw, 20)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(30, 45, 65, 200))
        p.drawRoundedRect(r, 10, 10)
        p.setPen(QColor("white"))
        p.drawText(r, Qt.AlignCenter, label)

        # 對話框
        text = "❗ 我身上有額外題目！點我～" if d.get("alert") else d.get("say", "")
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

    # ---- 滑鼠 ----
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.press_pos = e.globalPosition().toPoint()
            self.drag_off = self.press_pos - self.pos()
        elif e.button() == Qt.RightButton:
            self.manager.tray_menu.popup(e.globalPosition().toPoint())

    def mouseMoveEvent(self, e):
        if self.press_pos is None:
            return
        gp = e.globalPosition().toPoint()
        if not self.dragging and (gp - self.press_pos).manhattanLength() > 6:
            self.dragging = True
        if self.dragging:
            np = gp - self.drag_off
            self.x, self.y = float(np.x()), float(min(np.y(), self.ground()))
            self.move(int(self.x), int(self.y))

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        if not self.dragging:
            self.manager.pet_clicked(self.pid)
        self.dragging, self.press_pos, self.vy = False, None, 0.0


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
        self.walk_timer = QTimer(interval=33, timeout=self.walk)
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
        if self.pets_visible:
            for w in self.pets.values():
                w.step()

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
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationName("LearningSpirit")
    app.setQuitOnLastWindowClosed(False)
    _m = Manager(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
