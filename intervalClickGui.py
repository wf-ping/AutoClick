#!/usr/bin/env python3
"""
间隔点击（Interval Click）GUI

说明文档已移至：
- 中文：docs/intervalClickGui.devguide.zh-CN.md
- English: docs/intervalClickGui.devguide.en.md
"""
import sys

import pyautogui
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QGuiApplication,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QAbstractButton,
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QDoubleSpinBox,
    QSpinBox,
)

# 圆圈半径（像素），缩小
R = 20
CIRCLE_SIZE = R * 2 + 4
DEFAULT_INTERVAL = 1.0
MIN_INTERVAL_SEC = 0.1  # 点击间隔底线 100 毫秒

# 坐标提示距离圆心的偏移与边距（像素）
COORD_HINT_OFFSET = 14
COORD_HINT_MARGIN = 10

# 圆圈复位/初始位置（以操作面板左上角为原点，单位：像素）
# - x 为正向右
# - y 为正向下
# 中文版偏移
CIRCLE_OFFSET_X_ZH = 150
CIRCLE_OFFSET_Y_ZH = 35
# 英文版偏移
CIRCLE_OFFSET_X_EN = 230
CIRCLE_OFFSET_Y_EN = 35

# 语言
LANG_ZH = "zh"
LANG_EN = "en"
CURRENT_LANG = LANG_ZH


TRANSLATIONS = {
    "zh": {
        "title": "间隔点击",
        "drag_bar": "间隔点击 — 拖动此处移动",
        "coord_title": "圆心坐标 (拖动可移动):",
        "interval": "间隔(秒):",
        "count": "点击次数:",
        "count_placeholder": "不限",
        "start": "开始",
        "stop": "停止",
        "reset": "复位",
        "close": "关闭",
        "running": "运行中 (按停止结束)",
        "moved_out_stop": "鼠标已移出圆圈，已自动停止",
        "stopped_total": "已停止，共点击 {done} 次",
        "done_total": "已完成，共点击 {done} 次",
        "clicked_progress": "已点击 {done}/{target}",
        "pined": "置顶",
        "unpined": "未置顶",
        "lang_toggle": "EN",
    },
    "en": {
        "title": "Interval Click",
        "drag_bar": "Interval Click — drag here to move",
        "coord_title": "Center coords (drag circle to move):",
        "interval": "Interval (s):",
        "count": "Click count:",
        "count_placeholder": "Unlimited",
        "start": "Start",
        "stop": "Stop",
        "reset": "Reset",
        "close": "Close",
        "running": "Running (press Stop)",
        "moved_out_stop": "Mouse moved out of circle; stopped",
        "stopped_total": "Stopped. Total clicks: {done}",
        "done_total": "Done. Total clicks: {done}",
        "clicked_progress": "Clicked {done}/{target}",
        "pined": "Pinned",
        "unpined": "Unpinned",
        "lang_toggle": "中文",
    }
}

def _t(key: str) -> str:
    return TRANSLATIONS.get(CURRENT_LANG, TRANSLATIONS[LANG_ZH]).get(key, key)

class PinToggle(QAbstractButton):
    """铆钉式置顶开关：置顶竖直，取消置顶倾斜。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(22, 22)
        self.set_language(CURRENT_LANG)
        self.toggled.connect(lambda _on: self._refresh_tooltip())
        self._refresh_tooltip()

    def set_language(self, lang: str):
        global CURRENT_LANG
        CURRENT_LANG = lang
        self._refresh_tooltip()

    def _refresh_tooltip(self):
        self.setToolTip(_t("pined") if self.isChecked() else _t("unpined"))

    def enterEvent(self, event):
        self._refresh_tooltip()
        super().enterEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # hover/pressed 背景
        if self.isDown():
            bg = QColor(255, 255, 255, 30)
        elif self.underMouse():
            bg = QColor(255, 255, 255, 18)
        else:
            bg = QColor(0, 0, 0, 0)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 4, 4)

        # 图标（📌）旋转：置顶=竖直，非置顶=倾斜
        painter.setPen(QPen(QColor(240, 240, 240), 1))
        font = painter.font()
        font.setPointSize(12)
        painter.setFont(font)

        angle = 0 if self.isChecked() else -45
        center = self.rect().center()
        painter.translate(center)
        painter.rotate(angle)
        painter.translate(-center)
        painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), "📌")


class CoordHintWindow(QWidget):
    """拖动圆圈时显示的坐标提示（独立小窗，避免被圆圈尺寸限制）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self._text = ""
        self._font = QFont()
        self._font.setPointSize(10)
        self._font.setBold(True)
        self._padding_x = 8
        self._padding_y = 5

    def set_text(self, text: str):
        self._text = text
        fm = QFontMetrics(self._font)
        text_rect = fm.boundingRect(self._text)
        w = text_rect.width() + self._padding_x * 2
        h = text_rect.height() + self._padding_y * 2
        self.setFixedSize(max(72, w), max(24, h))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self._font)

        bg = QColor(30, 30, 30, 210)
        border = QColor(255, 140, 80, 200)
        painter.setPen(QPen(border, 1))
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 6, 6)

        painter.setPen(QPen(QColor(255, 180, 120), 1))
        painter.drawText(
            self.rect().adjusted(
                self._padding_x, self._padding_y, -self._padding_x, -self._padding_y
            ),
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            self._text,
        )


class CircleWindow(QWidget):
    """独立的可拖动小圆窗口，圆心即点击目标。运行中变为贴纸模式（变浅、不可操作）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(CIRCLE_SIZE, CIRCLE_SIZE)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._drag_start = None
        self._dragging = False
        self._sticker_mode = False  # True=仅显示贴纸，不可点击/拖动
        self._hint = CoordHintWindow()
        self._hint.hide()

    def set_sticker_mode(self, on: bool):
        """开启时：圆圈变浅、鼠标穿透，仅作显示；关闭时：恢复可拖动。"""
        self._sticker_mode = on
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, on)
        self.setWindowOpacity(0.38 if on else 1.0)
        if on:
            self._hint.hide()
            self._dragging = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self._sticker_mode:
            # 贴纸模式：颜色变浅
            painter.setPen(QPen(QColor(255, 140, 80), 2))
            painter.setBrush(QBrush(QColor(255, 160, 100, 80)))
        elif self._dragging:
            # 拖动中：颜色更浅
            painter.setPen(QPen(QColor(255, 170, 120), 2))
            painter.setBrush(QBrush(QColor(255, 190, 150, 90)))
        else:
            painter.setPen(QPen(QColor("#ff6600"), 3))
            painter.setBrush(QBrush(QColor(255, 102, 0, 140)))
        painter.drawEllipse(2, 2, self.width() - 4, self.height() - 4)
        painter.setPen(QPen(QColor("#ffaa00") if not self._sticker_mode else QColor(255, 180, 120), 1))
        painter.drawEllipse(2, 2, self.width() - 4, self.height() - 4)

        # 拖动中：圆心十字准星
        if self._dragging and (not self._sticker_mode):
            c = self.rect().center()
            painter.setPen(QPen(QColor(255, 230, 210), 2))
            arm = 7
            painter.drawLine(c.x() - arm, c.y(), c.x() + arm, c.y())
            painter.drawLine(c.x(), c.y() - arm, c.x(), c.y() + arm)
            painter.setPen(QPen(QColor(60, 60, 60, 160), 1))
            painter.drawEllipse(c, 2, 2)

    def get_center_screen(self):
        """返回圆心在屏幕上的坐标 (x, y)。"""
        c = self.rect().center()
        gp = self.mapToGlobal(c)
        return (int(gp.x()), int(gp.y()))

    def _screen_available_geometry_for_point(self, gp: QPoint) -> QRect:
        screen = QGuiApplication.screenAt(gp)
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            return QRect(0, 0, 10_000, 10_000)
        return screen.availableGeometry()

    def _update_hint(self):
        if (not self._dragging) or self._sticker_mode:
            self._hint.hide()
            return

        sx, sy = self.get_center_screen()
        center_gp = QPoint(sx, sy)
        avail = self._screen_available_geometry_for_point(center_gp)

        self._hint.set_text(f"X={sx}, Y={sy}")
        hw, hh = self._hint.width(), self._hint.height()

        # 候选象限：NE, NW, SE, SW
        candidates = [
            (COORD_HINT_OFFSET, -COORD_HINT_OFFSET - hh),  # NE
            (-COORD_HINT_OFFSET - hw, -COORD_HINT_OFFSET - hh),  # NW
            (COORD_HINT_OFFSET, COORD_HINT_OFFSET),  # SE
            (-COORD_HINT_OFFSET - hw, COORD_HINT_OFFSET),  # SW
        ]

        def clamp(v: int, lo: int, hi: int) -> int:
            return max(lo, min(hi, v))

        best_xy = None
        best_penalty = None
        for dx, dy in candidates:
            x = sx + dx
            y = sy + dy
            rect = QRect(x, y, hw, hh)
            overflow_left = max(0, (avail.left() + COORD_HINT_MARGIN) - rect.left())
            overflow_top = max(0, (avail.top() + COORD_HINT_MARGIN) - rect.top())
            overflow_right = max(0, rect.right() - (avail.right() - COORD_HINT_MARGIN))
            overflow_bottom = max(0, rect.bottom() - (avail.bottom() - COORD_HINT_MARGIN))
            penalty = overflow_left + overflow_top + overflow_right + overflow_bottom

            if best_penalty is None or penalty < best_penalty:
                best_penalty = penalty
                best_xy = (x, y)

        x, y = best_xy if best_xy is not None else (sx + COORD_HINT_OFFSET, sy + COORD_HINT_OFFSET)
        x = clamp(int(x), avail.left() + COORD_HINT_MARGIN, avail.right() - COORD_HINT_MARGIN - hw)
        y = clamp(int(y), avail.top() + COORD_HINT_MARGIN, avail.bottom() - COORD_HINT_MARGIN - hh)

        self._hint.move(x, y)
        self._hint.show()

    def mousePressEvent(self, e):
        if self._sticker_mode:
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_start = e.globalPosition().toPoint()
            self._dragging = True
            self.update()
            self._update_hint()

    def mouseMoveEvent(self, e):
        if self._sticker_mode:
            return
        if self._drag_start is not None and e.buttons() & Qt.MouseButton.LeftButton:
            delta = e.globalPosition().toPoint() - self._drag_start
            self._drag_start = e.globalPosition().toPoint()
            self.move(self.pos() + delta)
            self._update_hint()

    def mouseReleaseEvent(self, e):
        if self._sticker_mode:
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_start = None
            self._dragging = False
            self._hint.hide()
            self.update()


class ControlPanel(QWidget):
    """操作框：显示圆心坐标、间隔、开始/停止/关闭。可独立拖动。"""

    def __init__(self, circle_win: CircleWindow):
        super().__init__()
        self.circle_win = circle_win
        global CURRENT_LANG
        self.lang = CURRENT_LANG  # 默认中文
        self.setWindowTitle(_t("title"))
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowOpacity(0.92)
        self.setStyleSheet("""
            QWidget { background-color: #2d2d2d; border-radius: 6px; }
            QLabel { color: #eee; }
            QPushButton { background: #444; color: #fff; border: none; padding: 6px 10px; border-radius: 4px; }
            QPushButton:hover { background: #555; }
            QPushButton:disabled { background: #333; color: #666; }
            QSpinBox, QDoubleSpinBox {
                background: #1e1e1e; color: #ff6600; border: 1px solid #555;
                padding: 4px 22px 4px 6px; border-radius: 4px;
                min-height: 28px;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                width: 20px; height: 14px; margin: 0; padding: 0;
                background: #2e7d32; color: #fff;
                font-weight: bold; font-size: 13px;
                border: none; border-left: 1px solid #555; border-bottom: 1px solid #666;
                subcontrol-origin: border; subcontrol-position: top right;
                border-top-right-radius: 4px;
            }
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover { background: #388e3c; }
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                width: 20px; height: 14px; margin: 0; padding: 0;
                background: #c62828; color: #fff;
                font-weight: bold; font-size: 13px;
                border: none; border-left: 1px solid #555;
                subcontrol-origin: border; subcontrol-position: bottom right;
                border-bottom-right-radius: 4px;
            }
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background: #d32f2f; }
        """)

        self._panel_drag_start = None
        self.running = False
        self.click_timer = QTimer(self)
        self.click_timer.timeout.connect(self._on_click_tick)
        self.mouse_watch_timer = QTimer(self)
        self.mouse_watch_timer.timeout.connect(self._check_mouse_in_circle)
        self.interval_sec = DEFAULT_INTERVAL
        self.click_count_target = None  # None = 不限
        self.click_count_done = 0

        self._build_ui()
        self._update_coord_label()

        self.coord_update_timer = QTimer(self)
        self.coord_update_timer.timeout.connect(self._update_coord_label)
        self.coord_update_timer.start(200)

    def _apply_language(self):
        self.setWindowTitle(_t("title"))
        self.drag_bar.setText(_t("drag_bar"))
        self.coord_title_label.setText(_t("coord_title"))
        self.interval_label.setText(_t("interval"))
        self.count_label.setText(_t("count"))
        self.start_btn.setText(_t("start"))
        self.stop_btn.setText(_t("stop"))
        self.reset_btn.setText(_t("reset"))
        self.close_btn.setText(_t("close"))
        self.lang_btn.setText(_t("lang_toggle"))
        self.count_spin.setSpecialValueText(_t("count_placeholder"))
        self.count_spin.lineEdit().setPlaceholderText(_t("count_placeholder"))

        self.pin_btn.set_language(self.lang)
        # 更新后刷新尺寸（确保文本变化时宽度可收缩）
        self.adjustSize()

    def _toggle_language(self):
        global CURRENT_LANG
        self.lang = LANG_EN if self.lang == LANG_ZH else LANG_ZH
        CURRENT_LANG = self.lang
        self._apply_language()
        # 根据语言重新计算尺寸，避免英文变宽后无法恢复
        self.adjustSize()
        # 语言切换后重新按偏移规则放置圆圈（与面板解耦）
        self._place_circle_relative_to_panel()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 8, 12, 12)

        # 顶部拖动条（拖动此处可移动操作框）
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        self.lang_btn = QPushButton(_t("lang_toggle"))
        self.lang_btn.setFixedWidth(40)
        self.lang_btn.setMinimumHeight(22)
        self.lang_btn.clicked.connect(self._toggle_language)

        self.pin_btn = PinToggle()
        self.pin_btn.setChecked(True)
        self.pin_btn.toggled.connect(self._toggle_always_on_top)

        self.drag_bar = QLabel(_t("drag_bar"))
        self.drag_bar.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0;")
        self.drag_bar.setCursor(Qt.CursorShape.SizeAllCursor)

        top_row.addWidget(self.drag_bar)
        top_row.addStretch()
        top_row.addWidget(self.lang_btn)
        top_row.addWidget(self.pin_btn)
        layout.addLayout(top_row)

        coord_layout = QVBoxLayout()
        self.coord_title_label = QLabel(_t("coord_title"))
        coord_layout.addWidget(self.coord_title_label)
        self.coord_label = QLabel("X=0, Y=0")
        self.coord_label.setStyleSheet("color: #ff6600; font-family: Consolas; font-size: 13px;")
        coord_layout.addWidget(self.coord_label)
        layout.addLayout(coord_layout)

        interval_row = QHBoxLayout()
        self.interval_label = QLabel(_t("interval"))
        interval_row.addWidget(self.interval_label)
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.interval_spin.setMinimum(MIN_INTERVAL_SEC)
        self.interval_spin.setMaximum(3600)
        self.interval_spin.setDecimals(3)
        self.interval_spin.setSingleStep(0.1)
        self.interval_spin.setValue(DEFAULT_INTERVAL)
        self.interval_spin.setFixedWidth(110)
        self.interval_spin.setMinimumHeight(28)
        interval_row.addWidget(self.interval_spin)
        interval_row.addStretch()
        layout.addLayout(interval_row)

        count_row = QHBoxLayout()
        self.count_label = QLabel(_t("count"))
        count_row.addWidget(self.count_label)
        self.count_spin = QSpinBox()
        self.count_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.count_spin.setMinimum(0)
        self.count_spin.setMaximum(999999)
        self.count_spin.setValue(0)
        self.count_spin.setSpecialValueText(_t("count_placeholder"))
        self.count_spin.setFixedWidth(110)
        self.count_spin.setMinimumHeight(28)
        count_row.addWidget(self.count_spin)
        count_row.addStretch()
        layout.addLayout(count_row)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.status_label)

        # 按钮区：两行更紧凑（避免面板变宽）
        btn_row1 = QHBoxLayout()
        btn_row1.setSpacing(8)
        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(8)

        self.start_btn = QPushButton(_t("start"))
        self.start_btn.clicked.connect(self._start_click)
        self.stop_btn = QPushButton(_t("stop"))
        self.stop_btn.clicked.connect(self._stop_click)
        self.stop_btn.setEnabled(False)
        self.reset_btn = QPushButton(_t("reset"))
        self.reset_btn.clicked.connect(self._reset_circle)
        self.close_btn = QPushButton(_t("close"))
        self.close_btn.clicked.connect(self._do_close)

        for b in (self.start_btn, self.stop_btn, self.reset_btn, self.close_btn):
            b.setMinimumHeight(30)

        btn_row1.addWidget(self.start_btn)
        btn_row1.addWidget(self.stop_btn)
        btn_row2.addWidget(self.reset_btn)
        btn_row2.addWidget(self.close_btn)
        layout.addLayout(btn_row1)
        layout.addLayout(btn_row2)

        # 初始化一次语言相关文本（包含 pin tooltip）
        self._apply_language()

    def _place_circle_relative_to_panel(self):
        """将圆圈放到操作面板相对偏移位置（初始/复位一致）。"""
        # 注意：圆圈位置完全由 CIRCLE_OFFSET_X/Y 控制，与面板宽度无关（语言切换不会影响相对偏移）
        px = self.x()
        py = self.y()
        x = px + int(CIRCLE_OFFSET_X_ZH if self.lang == LANG_ZH else CIRCLE_OFFSET_X_EN)
        y = py + int(CIRCLE_OFFSET_Y_ZH if self.lang == LANG_ZH else CIRCLE_OFFSET_Y_EN)

        # 屏幕边界保护（按面板所在屏幕/主屏可用区域 clamp）
        screen = QGuiApplication.screenAt(QPoint(px + self.width() // 2, py + self.height() // 2))
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is not None:
            avail = screen.availableGeometry()
            x = max(avail.left(), min(x, avail.right() - CIRCLE_SIZE))
            y = max(avail.top(), min(y, avail.bottom() - CIRCLE_SIZE))

        self.circle_win.move(int(x), int(y))
        self._raise_circle_above_panel()

    def _reset_circle(self):
        """将圆圈复位到默认位置（操作面板右上角）。"""
        if self.running:
            return
        self._place_circle_relative_to_panel()
        self._update_coord_label()

    def _raise_circle_above_panel(self):
        # 只保证层级：圆圈始终压在操作面板之上（不绑定位置）
        try:
            self.circle_win.raise_()
        except Exception:
            pass

    def _toggle_always_on_top(self, on: bool):
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, on)
        # 重新 show 以应用 window flags
        self.show()
        self._raise_circle_above_panel()

    def _update_coord_label(self):
        if self.running:
            return
        try:
            sx, sy = self.circle_win.get_center_screen()
            self.coord_label.setText(f"X={sx}, Y={sy}")
        except Exception:
            self.coord_label.setText("X=?, Y=?")

    def _get_click_center(self):
        return self.circle_win.get_center_screen()

    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton:
            return
        # 仅当点击在顶部拖动条区域时开始拖动（前约 28px）
        if e.position().y() < 28:
            self._panel_drag_start = e.globalPosition().toPoint()

    def mouseMoveEvent(self, e):
        if self._panel_drag_start is not None and e.buttons() & Qt.MouseButton.LeftButton:
            delta = e.globalPosition().toPoint() - self._panel_drag_start
            self._panel_drag_start = e.globalPosition().toPoint()
            self.move(self.pos() + delta)
            # 不绑定圆圈位置；仅保持圆圈在面板之上
            self._raise_circle_above_panel()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._panel_drag_start = None

    def _start_click(self):
        self.interval_sec = self.interval_spin.value()
        n = self.count_spin.value()
        self.click_count_target = n if n > 0 else None
        self.click_count_done = 0

        self.running = True
        self.circle_win.set_sticker_mode(True)  # 圆圈变贴纸：变浅、不可操作，点击穿透
        self.click_timer.stop()
        # 鼠标检测间隔必须小于点击间隔，否则每次点击会把鼠标拉回圆心，难以触发移出停止
        click_interval_ms = int(self.interval_sec * 1000)
        watch_ms = min(100, max(20, click_interval_ms // 3))  # 每段点击间隔内至少检测 3 次，20~100ms
        self.mouse_watch_timer.start(watch_ms)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.reset_btn.setEnabled(False)
        self.interval_spin.setEnabled(False)
        self.count_spin.setEnabled(False)
        self.status_label.setText("")
        # 启动时稍微延迟，避免第一次立即触发
        QTimer.singleShot(10, self._on_click_tick)

    def _on_click_tick(self):
        if not self.running:
            return
        try:
            sx, sy = self._get_click_center()
            # 先隐藏圆圈，再点击，这样点击会落到下层窗口；点击后再显示圆圈
            self.circle_win.hide()
            # 稍微延长延迟，确保窗口从合成层移除
            QTimer.singleShot(10, lambda: self._perform_click_then_show(sx, sy))
        except Exception:
            self.circle_win.show()
            self.click_timer.start(int(self.interval_sec * 1000))

    def _perform_click_then_show(self, sx: int, sy: int):
        """执行一次点击后重新显示圆圈，并更新状态/调度下一次。"""
        try:
            pyautogui.moveTo(sx, sy, duration=0)
            pyautogui.click(button="left")
        except Exception:
            pass
        self.circle_win.show()
        self.click_count_done += 1
        self.coord_label.setText(f"X={sx}, Y={sy}")
        if self.click_count_target is not None:
            self.status_label.setText(
                _t("clicked_progress").format(
                    done=self.click_count_done, target=self.click_count_target
                )
            )
            if self.click_count_done >= self.click_count_target:
                self.status_label.setText(_t("done_total").format(done=self.click_count_done))
                self._stop_click(completed=True)
                return
        else:
            self.status_label.setText(_t("running"))
        if self.running:
            self.click_timer.start(int(self.interval_sec * 1000))

    def _check_mouse_in_circle(self):
        """运行时按间隔检测（间隔始终小于点击间隔）：鼠标若移出预设圆圈范围则自动停止。"""
        if not self.running:
            return
        try:
            cx, cy = self.circle_win.get_center_screen()
            mx, my = pyautogui.position()
            dist_sq = (mx - cx) ** 2 + (my - cy) ** 2
            if dist_sq > R * R:
                self.mouse_watch_timer.stop()
                self._stop_click()
                self.status_label.setText(_t("moved_out_stop"))
        except Exception:
            pass

    def _stop_click(self, completed=False):
        self.running = False
        self.mouse_watch_timer.stop()
        self.circle_win.set_sticker_mode(False)  # 恢复圆圈可拖动、正常颜色
        self.click_timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.reset_btn.setEnabled(True)
        self.interval_spin.setEnabled(True)
        self.count_spin.setEnabled(True)
        if self.click_count_done > 0 and not completed:
            self.status_label.setText(_t("stopped_total").format(done=self.click_count_done))
        self._update_coord_label()

    def _do_close(self):
        self._stop_click()
        self.coord_update_timer.stop()
        self.circle_win.close()
        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    # 使用 Fusion 样式，保证各平台 SpinBox 都显示上下两个增减按钮
    app.setStyle("Fusion")

    circle_win = CircleWindow()
    panel = ControlPanel(circle_win)

    panel.adjustSize()
    # 初始位置：优先鼠标所在屏幕，其次主屏，水平/垂直居中
    try:
        mx, my = pyautogui.position()
        screen = QGuiApplication.screenAt(QPoint(int(mx), int(my)))
    except Exception:
        screen = None
    if screen is None:
        screen = QGuiApplication.primaryScreen()
    if screen is not None:
        avail = screen.availableGeometry()
        x = avail.left() + (avail.width() - panel.width()) // 2
        y = avail.top() + (avail.height() - panel.height()) // 2
        panel.move(int(x), int(y))
    panel.show()
    # 等面板真实显示并完成布局后再摆放圆圈，避免初始/复位位置出现像素级差异
    QTimer.singleShot(0, panel._place_circle_relative_to_panel)
    circle_win.show()
    circle_win.raise_()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
