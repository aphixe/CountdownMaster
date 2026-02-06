import csv
import ctypes
import math
import logging
import os
import shutil
import sys
from typing import Optional
from dataclasses import dataclass, field

from PySide6.QtCore import (
    QDate,
    QDateTime,
    QEvent,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRect,
    QRectF,
    QSettings,
    Signal,
    QSize,
    QTimer,
    Qt,
    QTime,
    QVariantAnimation,
    QEasingCurve,
)
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QFont,
    QFontDatabase,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QCalendarWidget,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QSlider,
    QSpinBox,
    QStackedLayout,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QScrollArea,
    QToolTip,
    QVBoxLayout,
    QWidget,
    QColorDialog,
    QGraphicsBlurEffect,
    QDateEdit,
    QTimeEdit,
    QInputDialog,
    QKeySequenceEdit,
)

try:
    from PySide6.QtWidgets import QMacVisualEffect
except Exception:
    QMacVisualEffect = None

APP_NAME = "Countdown Master"
DATA_DIR: Optional[str] = None
SETTINGS_PATH = "settings.ini"


def resolve_data_dir() -> str:
    if getattr(sys, "frozen", False):
        if sys.platform == "darwin":
            home = os.path.expanduser("~")
            base = os.path.join(
                home,
                "Library",
                "Application Support",
                APP_NAME,
            )
        else:
            base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(base, exist_ok=True)
    return base


def init_paths() -> None:
    global DATA_DIR, SETTINGS_PATH
    if DATA_DIR is None:
        DATA_DIR = resolve_data_dir()
    SETTINGS_PATH = os.path.join(DATA_DIR, "settings.ini")
    if os.path.exists(SETTINGS_PATH):
        return
    legacy_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.ini"),
        os.path.join(os.getcwd(), "settings.ini"),
    ]
    for legacy_path in legacy_paths:
        if legacy_path == SETTINGS_PATH or not os.path.exists(legacy_path):
            continue
        try:
            shutil.copy2(legacy_path, SETTINGS_PATH)
        except Exception:
            pass
        break


def get_settings() -> QSettings:
    if SETTINGS_PATH == "settings.ini" and DATA_DIR is None:
        init_paths()
    return QSettings(SETTINGS_PATH, QSettings.IniFormat)

@dataclass
class UiSettings:
    blur_radius: int = 14
    opacity: float = 0.85
    bg_color: QColor = field(default_factory=lambda: QColor("#2b313b"))
    text_color: QColor = field(default_factory=lambda: QColor("#ebb6e8"))
    accent_color: QColor = field(default_factory=lambda: QColor("#6dd3fb"))
    font_size: int = 36
    label_size: int = 10
    day_time_color: QColor = field(default_factory=lambda: QColor("#bdfdbb"))
    day_time_font_size: int = 13
    day_start_hour: int = 6
    day_start_minute: int = 30
    day_end_hour: int = 23
    day_end_minute: int = 0
    heatmap_color: QColor = field(default_factory=lambda: QColor("#8afb71"))
    heatmap_hover_bg_color: QColor = field(default_factory=lambda: QColor("#1f2937"))
    heatmap_hover_text_color: QColor = field(default_factory=lambda: QColor("#f8fafc"))
    heatmap_hover_cell_color: QColor = field(default_factory=lambda: QColor("#429e7f"))
    heatmap_cell_size: int = 4
    heatmap_month_padding: int = 1
    heatmap_month_label_size: int = 8
    graph_line_color: QColor = field(default_factory=lambda: QColor("#6dd3fb"))
    graph_dot_color: QColor = field(default_factory=lambda: QColor("#ebb6e8"))
    graph_fill_color: QColor = field(default_factory=lambda: QColor("#6dd3fb"))
    graph_grid_color: QColor = field(default_factory=lambda: QColor("#94a3b8"))
    total_today_color: QColor = field(default_factory=lambda: QColor("#94a3b8"))
    total_today_font_size: int = 10
    goal_left_color: QColor = field(default_factory=lambda: QColor("#6dd3fb"))
    goal_left_font_size: int = 10
    super_goal_bar_start: QColor = field(default_factory=lambda: QColor("#6dd3fb"))
    super_goal_bar_end: QColor = field(default_factory=lambda: QColor("#8afb71"))
    super_goal_bar_bg: QColor = field(default_factory=lambda: QColor("#1f2937"))
    super_goal_bar_width: int = 120
    super_goal_bar_height: int = 8
    goal_pulse_seconds: float = 2.0
    always_on_top: bool = False
    year_total_display: str = "hours"
    week_start_day: int = 1
    week_end_day: int = 7
    show_heatmap: bool = True
    show_day_time: bool = True
    show_total_today: bool = True
    show_year_total: bool = True
    show_super_goal_left: bool = True
    show_status_label: bool = True
    show_start_button: bool = True
    show_clock_button: bool = True
    show_longest_streak: bool = True
    show_current_streak: bool = True
    use_24h_time: bool = True


@dataclass
class HotkeySettings:
    start_hotkey: str = ""
    clock_hotkey: str = ""
    start_xinput_button: str = ""
    clock_xinput_button: str = ""


@dataclass(frozen=True)
class GraphSeries:
    label: str
    totals: dict[str, int]
    line_color: QColor
    dot_color: QColor
    fill_color: QColor


@dataclass(frozen=True)
class CalendarBlock:
    day_index: int
    start_seconds: int
    end_seconds: int
    label: str
    color: QColor
    profile_label: str


XINPUT_BUTTONS = {
    "DPad Up": 0x0001,
    "DPad Down": 0x0002,
    "DPad Left": 0x0004,
    "DPad Right": 0x0008,
    "Start": 0x0010,
    "Back": 0x0020,
    "Left Stick": 0x0040,
    "Right Stick": 0x0080,
    "Left Shoulder": 0x0100,
    "Right Shoulder": 0x0200,
    "A": 0x1000,
    "B": 0x2000,
    "X": 0x4000,
    "Y": 0x8000,
}

PYGAME_BUTTON_MAP = {
    "DPad Up": ("hat", (0, 1)),
    "DPad Down": ("hat", (0, -1)),
    "DPad Left": ("hat", (-1, 0)),
    "DPad Right": ("hat", (1, 0)),
    "Start": ("button", 7),
    "Back": ("button", 6),
    "Left Stick": ("button", 8),
    "Right Stick": ("button", 9),
    "Left Shoulder": ("button", 4),
    "Right Shoulder": ("button", 5),
    "A": ("button", 0),
    "B": ("button", 1),
    "X": ("button", 2),
    "Y": ("button", 3),
}


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", ctypes.c_ulong),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


class XInputReader:
    def __init__(self) -> None:
        self.backend_name = "XInput"
        self._dll = self._load_xinput()
        self.available = self._dll is not None
        if self.available:
            self._dll.XInputGetState.argtypes = [
                ctypes.c_uint,
                ctypes.POINTER(XINPUT_STATE),
            ]
            self._dll.XInputGetState.restype = ctypes.c_uint

    def _load_xinput(self):
        if sys.platform != "win32" or not hasattr(ctypes, "WinDLL"):
            return None
        for dll_name in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
            try:
                return ctypes.WinDLL(dll_name)
            except Exception:
                continue
        return None

    def read_buttons(self, index: int = 0) -> Optional[int]:
        if not self.available:
            return None
        state = XINPUT_STATE()
        result = self._dll.XInputGetState(index, ctypes.byref(state))
        if result != 0:
            return None
        return int(state.Gamepad.wButtons)


class PygameGamepadReader:
    def __init__(self) -> None:
        self.backend_name = "SDL"
        self._pygame = None
        self._joystick = None
        try:
            import pygame

            self._pygame = pygame
            self._pygame.init()
            self._pygame.joystick.init()
            self._ensure_joystick()
            self.available = True
        except Exception:
            self.available = False

    def _ensure_joystick(self) -> None:
        if self._pygame is None:
            return
        try:
            count = self._pygame.joystick.get_count()
        except Exception:
            self._joystick = None
            return
        if count <= 0:
            self._joystick = None
            return
        if self._joystick is None:
            try:
                self._joystick = self._pygame.joystick.Joystick(0)
                self._joystick.init()
            except Exception:
                self._joystick = None

    def read_buttons(self, index: int = 0) -> Optional[int]:
        if self._pygame is None:
            return None
        self._ensure_joystick()
        if self._joystick is None:
            return None
        try:
            self._pygame.event.pump()
        except Exception:
            return None
        buttons = 0
        hat = (0, 0)
        try:
            if self._joystick.get_numhats() > 0:
                hat = self._joystick.get_hat(0)
        except Exception:
            hat = (0, 0)
        for name, mask in XINPUT_BUTTONS.items():
            mapping = PYGAME_BUTTON_MAP.get(name)
            if not mapping:
                continue
            kind, value = mapping
            if kind == "button":
                try:
                    if (
                        self._joystick.get_numbuttons() > value
                        and self._joystick.get_button(value)
                    ):
                        buttons |= mask
                except Exception:
                    continue
            else:
                hat_x, hat_y = hat
                if value[0] and hat_x == value[0]:
                    buttons |= mask
                if value[1] and hat_y == value[1]:
                    buttons |= mask
        return buttons


class GamepadReader:
    def __init__(self) -> None:
        self._backend = XInputReader()
        if self._backend.available:
            self.available = True
        else:
            self._backend = PygameGamepadReader()
            self.available = self._backend.available
        self.backend_name = (
            self._backend.backend_name if self.available else ""
        )
        self.group_label = (
            f"Gamepad ({self.backend_name})" if self.backend_name else "Gamepad"
        )

    def read_buttons(self, index: int = 0) -> Optional[int]:
        return self._backend.read_buttons(index)


def qcolor_to_hex(color: QColor) -> str:
    return color.name(QColor.HexRgb)


def hex_to_qcolor(value: str, fallback: QColor) -> QColor:
    color = QColor(value)
    if not color.isValid():
        return fallback
    return color


def qcolor_to_abgr(color: QColor, opacity: float) -> int:
    alpha = max(0, min(255, int(opacity * 255)))
    return (alpha << 24) | (color.blue() << 16) | (color.green() << 8) | color.red()


def qcolor_to_rgba(color: QColor, opacity: float) -> str:
    alpha = max(0, min(255, int(opacity * 255)))
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})"


def default_font_family() -> str:
    if sys.platform == "win32":
        return "Segoe UI"
    try:
        return QFontDatabase.systemFont(QFontDatabase.GeneralFont).family()
    except Exception:
        return "Sans Serif"


def parse_bool(value: object, fallback: bool) -> bool:
    if value is None:
        return fallback
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return fallback


def format_duration_hm(total_seconds: int) -> str:
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours}h {minutes}m"


def format_duration_hms(total_seconds: int) -> str:
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours}h {minutes}m {seconds}s"


def format_percent(part_seconds: int, goal_seconds: int) -> str:
    if goal_seconds <= 0:
        return "N/A"
    percent = (part_seconds / goal_seconds) * 100
    return f"{percent:.0f}%"


LOGGER = logging.getLogger("countdown")
HEATMAP_CELL_SIZE_MIN = 2
HEATMAP_CELL_SIZE_MAX = 20
YEAR_TOTAL_DISPLAY_MODES = ("hours", "days", "week", "avg_week")
DEFAULT_PROFILES = (
    ("Activate Immersion", "active.csv"),
    ("Passive Immersion", "passive.csv"),
    ("Phonetic Training", "phonetic.csv"),
    ("Output", "output.csv"),
    ("Soroban", "soroban.csv"),
    ("Anki/Migaku", "anki.csv"),
)
DEFAULT_PROFILE_NAME = "Activate Immersion"
PROFILE_ACTION_ADD = "__add_profile__"
PROFILE_ACTION_DELETE = "__delete_profile__"
PROFILE_COLOR_PALETTE = (
    "#38bdf8",
    "#f472b6",
    "#22c55e",
    "#f59e0b",
    "#ef4444",
    "#a855f7",
    "#14b8a6",
    "#eab308",
)
CALENDAR_LEFT_MARGIN = 68
CALENDAR_HEADER_HEIGHT = 52
CALENDAR_MIN_DAY_WIDTH = 120
CALENDAR_SCALE_MINUTES_MIN = 5
CALENDAR_SCALE_MINUTES_MAX = 120
CALENDAR_SCALE_HEIGHT_MIN = 20
CALENDAR_SCALE_HEIGHT_MAX = 100
CALENDAR_PROFILE_ALL = "__calendar_all_profiles__"
LOGS_PROFILE_ALL = "__logs_all_profiles__"
CALENDAR_DAY_PADDING = 4
CALENDAR_BOTTOM_PADDING = 14


def setup_logging(log_path: str) -> None:
    LOGGER.setLevel(logging.DEBUG)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)
    LOGGER.propagate = False


def log_unhandled_exception(exc_type, exc, tb) -> None:
    LOGGER.error("Unhandled exception", exc_info=(exc_type, exc, tb))


def apply_windows_acrylic(hwnd: int, color: QColor, opacity: float) -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        class ACCENT_POLICY(ctypes.Structure):
            _fields_ = [
                ("AccentState", ctypes.c_int),
                ("AccentFlags", ctypes.c_int),
                ("GradientColor", ctypes.c_uint),
                ("AnimationId", ctypes.c_int),
            ]

        class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
            _fields_ = [
                ("Attribute", ctypes.c_int),
                ("Data", ctypes.c_void_p),
                ("SizeOfData", ctypes.c_size_t),
            ]

        accent = ACCENT_POLICY(4, 2, qcolor_to_abgr(color, opacity), 0)
        data = WINDOWCOMPOSITIONATTRIBDATA(
            19, ctypes.addressof(accent), ctypes.sizeof(accent)
        )
        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
    except Exception:
        # Acrylic is best-effort; fall back to Qt blur if unavailable.
        return


class SetTimeDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        hours: int,
        minutes: int,
        *,
        seconds: int = 0,
        title: str = "Set Time",
        super_goal_left_seconds: Optional[int] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self._extra_seconds = max(0, min(59, int(seconds)))
        self._setting_time = False
        self._super_goal_left_seconds = (
            max(0, int(super_goal_left_seconds))
            if super_goal_left_seconds is not None
            else None
        )
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 23)
        self.hours_spin.setValue(hours)
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setValue(minutes)

        form = QFormLayout()
        form.addRow("Hours", self.hours_spin)
        form.addRow("Minutes", self.minutes_spin)

        buttons = QHBoxLayout()
        self.add_super_goal_btn = None
        if self._super_goal_left_seconds is not None:
            self.add_super_goal_btn = QPushButton("Add Super Goal Left")
            self.add_super_goal_btn.clicked.connect(self._add_super_goal_left)
            if self._super_goal_left_seconds <= 0:
                self.add_super_goal_btn.setEnabled(False)
                self.add_super_goal_btn.setToolTip(
                    "No super goal time left to add."
                )
            buttons.addWidget(self.add_super_goal_btn)
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)

        self.hours_spin.valueChanged.connect(self._clear_extra_seconds)
        self.minutes_spin.valueChanged.connect(self._clear_extra_seconds)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(buttons)
        self.setLayout(layout)

    def total_seconds(self) -> int:
        return (
            self.hours_spin.value() * 3600
            + self.minutes_spin.value() * 60
            + self._extra_seconds
        )

    def _clear_extra_seconds(self, _value: int) -> None:
        if self._setting_time:
            return
        self._extra_seconds = 0

    def _set_time_from_seconds(self, total_seconds: int) -> None:
        total_seconds = max(0, int(total_seconds))
        hours_max = self.hours_spin.maximum()
        minutes_max = self.minutes_spin.maximum()
        max_total = hours_max * 3600 + minutes_max * 60 + 59
        total_seconds = min(total_seconds, max_total)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        self._setting_time = True
        try:
            self.hours_spin.setValue(hours)
            self.minutes_spin.setValue(minutes)
            self._extra_seconds = total_seconds % 60
        finally:
            self._setting_time = False

    def _add_super_goal_left(self) -> None:
        if not self._super_goal_left_seconds:
            return
        self._set_time_from_seconds(
            self.total_seconds() + self._super_goal_left_seconds
        )


class AddTimeDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        hours: int = 0,
        minutes: int = 0,
        start_time: Optional[QTime] = None,
        title: str = "Add Time",
        use_24h_time: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 23)
        self.hours_spin.setValue(hours)
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setValue(minutes)
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat(
            "HH:mm" if use_24h_time else "h:mm AP"
        )
        if start_time is None:
            now = QTime.currentTime()
            start_time = QTime(now.hour(), now.minute(), 0)
        self.start_time_edit.setTime(start_time)

        form = QFormLayout()
        form.addRow("Hours", self.hours_spin)
        form.addRow("Minutes", self.minutes_spin)
        form.addRow("Start time", self.start_time_edit)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(buttons)
        self.setLayout(layout)


class SettingsDialog(QDialog):
    def __init__(
        self, parent: QWidget, ui_settings: UiSettings, blur_supported: bool
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self._settings = ui_settings
        self._blur_supported = blur_supported

        self.blur_spin = QSpinBox()
        self.blur_spin.setRange(0, 40)
        self.blur_spin.setValue(ui_settings.blur_radius)
        if not blur_supported:
            self.blur_spin.setValue(0)
            self.blur_spin.setEnabled(False)
            self.blur_spin.setToolTip(
                "Blur is not supported on this platform."
            )

        self.opacity_spin = QDoubleSpinBox()
        self.opacity_spin.setRange(0.3, 1.0)
        self.opacity_spin.setSingleStep(0.05)
        self.opacity_spin.setValue(ui_settings.opacity)

        self.font_spin = QSpinBox()
        self.font_spin.setRange(18, 96)
        self.font_spin.setValue(ui_settings.font_size)

        self.label_spin = QSpinBox()
        self.label_spin.setRange(8, 18)
        self.label_spin.setValue(ui_settings.label_size)

        self.day_time_font_spin = QSpinBox()
        self.day_time_font_spin.setRange(10, 48)
        self.day_time_font_spin.setValue(ui_settings.day_time_font_size)

        self.day_start_hour_spin = QSpinBox()
        self.day_start_hour_spin.setRange(0, 23)
        self.day_start_hour_spin.setValue(ui_settings.day_start_hour)
        self.day_start_minute_spin = QSpinBox()
        self.day_start_minute_spin.setRange(0, 59)
        self.day_start_minute_spin.setValue(ui_settings.day_start_minute)

        self.day_end_hour_spin = QSpinBox()
        self.day_end_hour_spin.setRange(0, 23)
        self.day_end_hour_spin.setValue(ui_settings.day_end_hour)
        self.day_end_minute_spin = QSpinBox()
        self.day_end_minute_spin.setRange(0, 59)
        self.day_end_minute_spin.setValue(ui_settings.day_end_minute)

        self.week_start_combo = QComboBox()
        self.week_end_combo = QComboBox()
        week_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for day_value, label in enumerate(week_days, start=1):
            self.week_start_combo.addItem(label, day_value)
            self.week_end_combo.addItem(label, day_value)
        start_index = self.week_start_combo.findData(ui_settings.week_start_day)
        if start_index < 0:
            start_index = 0
        self.week_start_combo.setCurrentIndex(start_index)
        end_index = self.week_end_combo.findData(ui_settings.week_end_day)
        if end_index < 0:
            end_index = len(week_days) - 1
        self.week_end_combo.setCurrentIndex(end_index)
        self._week_syncing = False
        self.week_start_combo.currentIndexChanged.connect(
            self._on_week_start_changed
        )
        self.week_end_combo.currentIndexChanged.connect(self._on_week_end_changed)
        self._sync_week_end_from_start()

        self.time_format_combo = QComboBox()
        self.time_format_combo.addItem("24 hour", True)
        self.time_format_combo.addItem("12 hour (AM/PM)", False)
        time_index = self.time_format_combo.findData(ui_settings.use_24h_time)
        if time_index < 0:
            time_index = 0
        self.time_format_combo.setCurrentIndex(time_index)

        self.total_today_font_spin = QSpinBox()
        self.total_today_font_spin.setRange(10, 48)
        self.total_today_font_spin.setValue(ui_settings.total_today_font_size)

        self.goal_left_font_spin = QSpinBox()
        self.goal_left_font_spin.setRange(10, 48)
        self.goal_left_font_spin.setValue(ui_settings.goal_left_font_size)

        self.super_goal_bar_width_spin = QSpinBox()
        self.super_goal_bar_width_spin.setRange(40, 400)
        self.super_goal_bar_width_spin.setValue(ui_settings.super_goal_bar_width)

        self.super_goal_bar_height_spin = QSpinBox()
        self.super_goal_bar_height_spin.setRange(4, 40)
        self.super_goal_bar_height_spin.setValue(ui_settings.super_goal_bar_height)

        self.goal_pulse_spin = QDoubleSpinBox()
        self.goal_pulse_spin.setRange(0.2, 10.0)
        self.goal_pulse_spin.setSingleStep(0.1)
        self.goal_pulse_spin.setValue(ui_settings.goal_pulse_seconds)

        self.bg_btn = QPushButton()
        self.text_btn = QPushButton()
        self.accent_btn = QPushButton()
        self.day_time_btn = QPushButton()
        self.heatmap_color_btn = QPushButton()
        self.heatmap_hover_bg_btn = QPushButton()
        self.heatmap_hover_text_btn = QPushButton()
        self.heatmap_hover_cell_btn = QPushButton()
        self.heatmap_size_spin = QSpinBox()
        self.heatmap_size_spin.setRange(
            HEATMAP_CELL_SIZE_MIN, HEATMAP_CELL_SIZE_MAX
        )
        self.heatmap_size_spin.setValue(ui_settings.heatmap_cell_size)
        self.heatmap_month_padding_spin = QSpinBox()
        self.heatmap_month_padding_spin.setRange(0, 20)
        self.heatmap_month_padding_spin.setValue(
            ui_settings.heatmap_month_padding
        )
        self.heatmap_month_label_spin = QSpinBox()
        self.heatmap_month_label_spin.setRange(6, 18)
        self.heatmap_month_label_spin.setValue(
            ui_settings.heatmap_month_label_size
        )
        self.graph_line_btn = QPushButton()
        self.graph_dot_btn = QPushButton()
        self.graph_fill_btn = QPushButton()
        self.graph_grid_btn = QPushButton()
        self.total_today_btn = QPushButton()
        self.goal_left_btn = QPushButton()
        self.super_goal_bar_start_btn = QPushButton()
        self.super_goal_bar_end_btn = QPushButton()
        self.super_goal_bar_bg_btn = QPushButton()
        self._sync_color_btns()

        self.bg_btn.clicked.connect(lambda: self._pick_color("bg"))
        self.text_btn.clicked.connect(lambda: self._pick_color("text"))
        self.accent_btn.clicked.connect(lambda: self._pick_color("accent"))
        self.day_time_btn.clicked.connect(lambda: self._pick_color("day_time"))
        self.heatmap_color_btn.clicked.connect(
            lambda: self._pick_color("heatmap")
        )
        self.heatmap_hover_bg_btn.clicked.connect(
            lambda: self._pick_color("heatmap_hover_bg")
        )
        self.heatmap_hover_text_btn.clicked.connect(
            lambda: self._pick_color("heatmap_hover_text")
        )
        self.heatmap_hover_cell_btn.clicked.connect(
            lambda: self._pick_color("heatmap_hover_cell")
        )
        self.graph_line_btn.clicked.connect(
            lambda: self._pick_color("graph_line")
        )
        self.graph_dot_btn.clicked.connect(lambda: self._pick_color("graph_dot"))
        self.graph_fill_btn.clicked.connect(
            lambda: self._pick_color("graph_fill")
        )
        self.graph_grid_btn.clicked.connect(
            lambda: self._pick_color("graph_grid")
        )
        self.total_today_btn.clicked.connect(
            lambda: self._pick_color("total_today")
        )
        self.goal_left_btn.clicked.connect(lambda: self._pick_color("goal_left"))
        self.super_goal_bar_start_btn.clicked.connect(
            lambda: self._pick_color("super_goal_bar_start")
        )
        self.super_goal_bar_end_btn.clicked.connect(
            lambda: self._pick_color("super_goal_bar_end")
        )
        self.super_goal_bar_bg_btn.clicked.connect(
            lambda: self._pick_color("super_goal_bar_bg")
        )

        def _make_heading(text: str) -> QLabel:
            label = QLabel(text)
            font = label.font()
            font.setBold(True)
            label.setFont(font)
            return label

        def _make_divider() -> QFrame:
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            return line

        ui_tab = QWidget()
        ui_layout = QVBoxLayout()
        window_group = QGroupBox("Window")
        window_form = QFormLayout()
        window_form.addRow("Blur Radius", self.blur_spin)
        window_form.addRow("Opacity", self.opacity_spin)
        window_form.addRow("Background Color", self.bg_btn)
        window_form.addRow("Text Color", self.text_btn)
        window_form.addRow("Accent Color", self.accent_btn)
        window_group.setLayout(window_form)

        typography_group = QGroupBox("Timer and Labels")
        typography_form = QFormLayout()
        typography_form.addRow("Timer Font Size", self.font_spin)
        typography_form.addRow("Label Font Size", self.label_spin)
        typography_group.setLayout(typography_form)

        day_time_ui_group = QGroupBox("Day Time Left")
        day_time_ui_form = QFormLayout()
        day_time_ui_form.addRow("Font Size", self.day_time_font_spin)
        day_time_ui_form.addRow("Color", self.day_time_btn)
        day_time_ui_group.setLayout(day_time_ui_form)

        totals_group = QGroupBox("Totals")
        totals_form = QFormLayout()
        totals_form.addRow("Total Today Font Size", self.total_today_font_spin)
        totals_form.addRow("Total Today Color", self.total_today_btn)
        totals_form.addRow("Super Goal Left Font Size", self.goal_left_font_spin)
        totals_form.addRow("Super Goal Left Color", self.goal_left_btn)
        totals_group.setLayout(totals_form)

        super_goal_bar_group = QGroupBox("Super Goal Bar")
        super_goal_bar_form = QFormLayout()
        super_goal_bar_form.addRow("Width", self.super_goal_bar_width_spin)
        super_goal_bar_form.addRow("Height", self.super_goal_bar_height_spin)
        super_goal_bar_form.addRow("Gradient Start", self.super_goal_bar_start_btn)
        super_goal_bar_form.addRow("Gradient End", self.super_goal_bar_end_btn)
        super_goal_bar_form.addRow("Background", self.super_goal_bar_bg_btn)
        super_goal_bar_group.setLayout(super_goal_bar_form)

        heatmap_group = QGroupBox("Heatmap")
        heatmap_form = QFormLayout()
        heatmap_form.addRow("Cell Size", self.heatmap_size_spin)
        heatmap_form.addRow("Month Padding", self.heatmap_month_padding_spin)
        heatmap_form.addRow("Month Label Size", self.heatmap_month_label_spin)
        heatmap_form.addRow("Heatmap Color", self.heatmap_color_btn)
        heatmap_form.addRow("Hover Cell Color", self.heatmap_hover_cell_btn)
        heatmap_form.addRow("Tooltip Background", self.heatmap_hover_bg_btn)
        heatmap_form.addRow("Tooltip Text", self.heatmap_hover_text_btn)
        heatmap_group.setLayout(heatmap_form)

        graph_colors_group = QGroupBox("Trends Graph")
        graph_colors_form = QFormLayout()
        graph_colors_form.addRow("Line", self.graph_line_btn)
        graph_colors_form.addRow("Dots", self.graph_dot_btn)
        graph_colors_form.addRow("Fill Gradient", self.graph_fill_btn)
        graph_colors_form.addRow("Grid/Ticks", self.graph_grid_btn)
        graph_colors_group.setLayout(graph_colors_form)

        ui_layout.addWidget(_make_heading("Window and Typography"))
        ui_layout.addWidget(window_group)
        ui_layout.addWidget(typography_group)
        ui_layout.addWidget(_make_divider())
        ui_layout.addWidget(_make_heading("Day Display"))
        ui_layout.addWidget(day_time_ui_group)
        ui_layout.addWidget(totals_group)
        ui_layout.addWidget(super_goal_bar_group)
        ui_layout.addWidget(_make_divider())
        ui_layout.addWidget(_make_heading("Heatmap and Trends"))
        ui_layout.addWidget(heatmap_group)
        ui_layout.addWidget(graph_colors_group)
        ui_layout.addStretch(1)
        ui_tab.setLayout(ui_layout)

        day_tab = QWidget()
        day_layout = QVBoxLayout()
        day_time_group = QGroupBox("Day Time Range")
        day_time_form = QFormLayout()
        day_time_form.addRow("Start Hour", self.day_start_hour_spin)
        day_time_form.addRow("Start Minute", self.day_start_minute_spin)
        day_time_form.addRow("End Hour", self.day_end_hour_spin)
        day_time_form.addRow("End Minute", self.day_end_minute_spin)
        day_time_group.setLayout(day_time_form)

        week_range_group = QGroupBox("Week Total Range")
        week_range_form = QFormLayout()
        week_range_form.addRow("Start Day", self.week_start_combo)
        week_range_form.addRow("End Day", self.week_end_combo)
        week_range_group.setLayout(week_range_form)

        time_format_group = QGroupBox("Time Format")
        time_format_form = QFormLayout()
        time_format_form.addRow("Display", self.time_format_combo)
        time_format_group.setLayout(time_format_form)

        pulse_group = QGroupBox("Goal Pulse")
        pulse_form = QFormLayout()
        pulse_form.addRow("Glow Duration (sec)", self.goal_pulse_spin)
        pulse_group.setLayout(pulse_form)

        day_layout.addWidget(_make_heading("Day Time"))
        day_layout.addWidget(day_time_group)
        day_layout.addWidget(_make_divider())
        day_layout.addWidget(_make_heading("Week Totals"))
        day_layout.addWidget(week_range_group)
        day_layout.addWidget(_make_divider())
        day_layout.addWidget(_make_heading("Time Format"))
        day_layout.addWidget(time_format_group)
        day_layout.addWidget(_make_divider())
        day_layout.addWidget(_make_heading("Goal Pulse"))
        day_layout.addWidget(pulse_group)
        day_layout.addStretch(1)
        day_tab.setLayout(day_layout)

        ui_scroll = QScrollArea()
        ui_scroll.setWidgetResizable(True)
        ui_scroll.setFrameShape(QFrame.NoFrame)
        ui_scroll.setWidget(ui_tab)

        day_scroll = QScrollArea()
        day_scroll.setWidgetResizable(True)
        day_scroll.setFrameShape(QFrame.NoFrame)
        day_scroll.setWidget(day_tab)

        tabs = QTabWidget()
        tabs.addTab(day_scroll, "Day")
        tabs.addTab(ui_scroll, "UI")

        buttons = QHBoxLayout()
        ok_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)

        layout = QVBoxLayout()
        layout.addWidget(tabs)
        layout.addLayout(buttons)
        self.setLayout(layout)
        self.resize(520, 480)

    def _sync_color_btns(self) -> None:
        for btn, color in (
            (self.bg_btn, self._settings.bg_color),
            (self.text_btn, self._settings.text_color),
            (self.accent_btn, self._settings.accent_color),
            (self.day_time_btn, self._settings.day_time_color),
            (self.heatmap_color_btn, self._settings.heatmap_color),
            (self.heatmap_hover_cell_btn, self._settings.heatmap_hover_cell_color),
            (self.heatmap_hover_bg_btn, self._settings.heatmap_hover_bg_color),
            (self.heatmap_hover_text_btn, self._settings.heatmap_hover_text_color),
            (self.graph_line_btn, self._settings.graph_line_color),
            (self.graph_dot_btn, self._settings.graph_dot_color),
            (self.graph_fill_btn, self._settings.graph_fill_color),
            (self.graph_grid_btn, self._settings.graph_grid_color),
            (self.total_today_btn, self._settings.total_today_color),
            (self.goal_left_btn, self._settings.goal_left_color),
            (self.super_goal_bar_start_btn, self._settings.super_goal_bar_start),
            (self.super_goal_bar_end_btn, self._settings.super_goal_bar_end),
            (self.super_goal_bar_bg_btn, self._settings.super_goal_bar_bg),
        ):
            btn.setText(color.name())
            btn.setStyleSheet(
                f"background-color: {color.name()};"
                "color: #111; padding: 6px; border-radius: 6px;"
            )

    def _sync_week_end_from_start(self) -> None:
        if self._week_syncing:
            return
        self._week_syncing = True
        start_day = int(self.week_start_combo.currentData())
        end_day = 7 if start_day == 1 else start_day - 1
        end_index = self.week_end_combo.findData(end_day)
        if end_index >= 0:
            self.week_end_combo.setCurrentIndex(end_index)
        self._week_syncing = False

    def _sync_week_start_from_end(self) -> None:
        if self._week_syncing:
            return
        self._week_syncing = True
        end_day = int(self.week_end_combo.currentData())
        start_day = 1 if end_day == 7 else end_day + 1
        start_index = self.week_start_combo.findData(start_day)
        if start_index >= 0:
            self.week_start_combo.setCurrentIndex(start_index)
        self._week_syncing = False

    def _on_week_start_changed(self, index: int) -> None:
        self._sync_week_end_from_start()

    def _on_week_end_changed(self, index: int) -> None:
        self._sync_week_start_from_end()

    def _pick_color(self, key: str) -> None:
        current = {
            "bg": self._settings.bg_color,
            "text": self._settings.text_color,
            "accent": self._settings.accent_color,
            "day_time": self._settings.day_time_color,
            "heatmap": self._settings.heatmap_color,
            "heatmap_hover_bg": self._settings.heatmap_hover_bg_color,
            "heatmap_hover_text": self._settings.heatmap_hover_text_color,
            "heatmap_hover_cell": self._settings.heatmap_hover_cell_color,
            "graph_line": self._settings.graph_line_color,
            "graph_dot": self._settings.graph_dot_color,
            "graph_fill": self._settings.graph_fill_color,
            "graph_grid": self._settings.graph_grid_color,
            "total_today": self._settings.total_today_color,
            "goal_left": self._settings.goal_left_color,
            "super_goal_bar_start": self._settings.super_goal_bar_start,
            "super_goal_bar_end": self._settings.super_goal_bar_end,
            "super_goal_bar_bg": self._settings.super_goal_bar_bg,
        }[key]
        color = QColorDialog.getColor(current, self)
        if not color.isValid():
            return
        if key == "bg":
            self._settings.bg_color = color
        elif key == "text":
            self._settings.text_color = color
        elif key == "day_time":
            self._settings.day_time_color = color
        elif key == "heatmap":
            self._settings.heatmap_color = color
        elif key == "heatmap_hover_bg":
            self._settings.heatmap_hover_bg_color = color
        elif key == "heatmap_hover_text":
            self._settings.heatmap_hover_text_color = color
        elif key == "heatmap_hover_cell":
            self._settings.heatmap_hover_cell_color = color
        elif key == "graph_line":
            self._settings.graph_line_color = color
        elif key == "graph_dot":
            self._settings.graph_dot_color = color
        elif key == "graph_fill":
            self._settings.graph_fill_color = color
        elif key == "graph_grid":
            self._settings.graph_grid_color = color
        elif key == "total_today":
            self._settings.total_today_color = color
        elif key == "goal_left":
            self._settings.goal_left_color = color
        elif key == "super_goal_bar_start":
            self._settings.super_goal_bar_start = color
        elif key == "super_goal_bar_end":
            self._settings.super_goal_bar_end = color
        elif key == "super_goal_bar_bg":
            self._settings.super_goal_bar_bg = color
        else:
            self._settings.accent_color = color
        self._sync_color_btns()

    def updated_settings(self) -> UiSettings:
        blur_radius = self.blur_spin.value() if self._blur_supported else 0
        use_24h_time = bool(self.time_format_combo.currentData())
        return UiSettings(
            blur_radius=blur_radius,
            opacity=self.opacity_spin.value(),
            bg_color=self._settings.bg_color,
            text_color=self._settings.text_color,
            accent_color=self._settings.accent_color,
            font_size=self.font_spin.value(),
            label_size=self.label_spin.value(),
            day_time_color=self._settings.day_time_color,
            day_time_font_size=self.day_time_font_spin.value(),
            day_start_hour=self.day_start_hour_spin.value(),
            day_start_minute=self.day_start_minute_spin.value(),
            day_end_hour=self.day_end_hour_spin.value(),
            day_end_minute=self.day_end_minute_spin.value(),
            heatmap_color=self._settings.heatmap_color,
            heatmap_hover_bg_color=self._settings.heatmap_hover_bg_color,
            heatmap_hover_text_color=self._settings.heatmap_hover_text_color,
            heatmap_hover_cell_color=self._settings.heatmap_hover_cell_color,
            heatmap_cell_size=self.heatmap_size_spin.value(),
            heatmap_month_padding=self.heatmap_month_padding_spin.value(),
            heatmap_month_label_size=self.heatmap_month_label_spin.value(),
            graph_line_color=self._settings.graph_line_color,
            graph_dot_color=self._settings.graph_dot_color,
            graph_fill_color=self._settings.graph_fill_color,
            graph_grid_color=self._settings.graph_grid_color,
            total_today_color=self._settings.total_today_color,
            total_today_font_size=self.total_today_font_spin.value(),
            goal_left_color=self._settings.goal_left_color,
            goal_left_font_size=self.goal_left_font_spin.value(),
            super_goal_bar_start=self._settings.super_goal_bar_start,
            super_goal_bar_end=self._settings.super_goal_bar_end,
            super_goal_bar_bg=self._settings.super_goal_bar_bg,
            super_goal_bar_width=self.super_goal_bar_width_spin.value(),
            super_goal_bar_height=self.super_goal_bar_height_spin.value(),
            goal_pulse_seconds=self.goal_pulse_spin.value(),
            always_on_top=self._settings.always_on_top,
            year_total_display=self._settings.year_total_display,
            week_start_day=int(self.week_start_combo.currentData()),
            week_end_day=int(self.week_end_combo.currentData()),
            show_heatmap=self._settings.show_heatmap,
            show_day_time=self._settings.show_day_time,
            show_total_today=self._settings.show_total_today,
            show_year_total=self._settings.show_year_total,
            show_super_goal_left=self._settings.show_super_goal_left,
            show_status_label=self._settings.show_status_label,
            show_start_button=self._settings.show_start_button,
            show_clock_button=self._settings.show_clock_button,
            show_longest_streak=self._settings.show_longest_streak,
            show_current_streak=self._settings.show_current_streak,
            use_24h_time=use_24h_time,
        )


class ProfileEditorDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        profile_labels: list[str],
        active_profile: str,
        resolved_colors: dict[str, QColor],
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Profile Editor")
        self.setModal(True)
        self._colors = {
            label: QColor(resolved_colors.get(label, QColor()))
            for label in profile_labels
        }
        self._initial_colors = {
            label: qcolor_to_hex(color) for label, color in self._colors.items()
        }

        self.profile_combo = QComboBox()
        for label in profile_labels:
            self.profile_combo.addItem(label, label)
        active_index = self.profile_combo.findData(active_profile)
        if active_index >= 0:
            self.profile_combo.setCurrentIndex(active_index)

        self.color_btn = QPushButton()
        self.color_btn.clicked.connect(self._pick_color)
        self.profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        self._sync_color_button()

        form = QFormLayout()
        form.addRow("Profile", self.profile_combo)
        form.addRow("Color", self.color_btn)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(buttons)
        self.setLayout(layout)
        self.resize(360, 160)

    def _current_label(self) -> Optional[str]:
        data = self.profile_combo.currentData()
        if isinstance(data, str) and data:
            return data
        return None

    def _current_color(self) -> QColor:
        label = self._current_label()
        if label and label in self._colors:
            return self._colors[label]
        return QColor()

    def _sync_color_button(self) -> None:
        color = self._current_color()
        self.color_btn.setText(color.name())
        self.color_btn.setStyleSheet(
            f"background-color: {color.name()};"
            "color: #111; padding: 6px; border-radius: 6px;"
        )

    def _on_profile_changed(self, index: int) -> None:
        self._sync_color_button()

    def _pick_color(self) -> None:
        current = self._current_color()
        color = QColorDialog.getColor(current, self)
        if not color.isValid():
            return
        label = self._current_label()
        if not label:
            return
        self._colors[label] = color
        self._sync_color_button()

    def changed_colors(self) -> dict[str, QColor]:
        changed: dict[str, QColor] = {}
        for label, color in self._colors.items():
            if qcolor_to_hex(color) != self._initial_colors.get(label):
                changed[label] = color
        return changed


class HotkeySettingsDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        hotkey_settings: HotkeySettings,
        gamepad_available: bool,
        gamepad_label: str,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Hotkey Settings")
        self.setModal(True)
        self._settings = hotkey_settings

        self.start_hotkey_edit = QKeySequenceEdit()
        self.start_hotkey_edit.setKeySequence(
            QKeySequence(hotkey_settings.start_hotkey)
        )
        self.clock_hotkey_edit = QKeySequenceEdit()
        self.clock_hotkey_edit.setKeySequence(
            QKeySequence(hotkey_settings.clock_hotkey)
        )

        start_clear = QPushButton("Clear")
        start_clear.clicked.connect(
            lambda: self.start_hotkey_edit.setKeySequence(QKeySequence())
        )
        clock_clear = QPushButton("Clear")
        clock_clear.clicked.connect(
            lambda: self.clock_hotkey_edit.setKeySequence(QKeySequence())
        )

        start_hotkey_row = QHBoxLayout()
        start_hotkey_row.addWidget(self.start_hotkey_edit)
        start_hotkey_row.addWidget(start_clear)

        clock_hotkey_row = QHBoxLayout()
        clock_hotkey_row.addWidget(self.clock_hotkey_edit)
        clock_hotkey_row.addWidget(clock_clear)

        keyboard_group = QGroupBox("Keyboard")
        keyboard_form = QFormLayout()
        keyboard_form.addRow("Start toggle", start_hotkey_row)
        keyboard_form.addRow("Clock toggle", clock_hotkey_row)
        keyboard_group.setLayout(keyboard_form)

        self.start_xinput_combo = QComboBox()
        self.clock_xinput_combo = QComboBox()
        self._populate_xinput_combo(self.start_xinput_combo)
        self._populate_xinput_combo(self.clock_xinput_combo)
        self._set_combo_value(
            self.start_xinput_combo, hotkey_settings.start_xinput_button
        )
        self._set_combo_value(
            self.clock_xinput_combo, hotkey_settings.clock_xinput_button
        )

        gamepad_group = QGroupBox(gamepad_label or "Gamepad")
        gamepad_form = QFormLayout()
        gamepad_form.addRow("Start toggle", self.start_xinput_combo)
        gamepad_form.addRow("Clock toggle", self.clock_xinput_combo)
        gamepad_group.setLayout(gamepad_form)
        if not gamepad_available:
            gamepad_group.setEnabled(False)
            gamepad_group.setToolTip(
                "Gamepad support requires pygame (SDL) on macOS/Linux or XInput on Windows."
            )

        buttons = QHBoxLayout()
        ok_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)

        layout = QVBoxLayout()
        layout.addWidget(keyboard_group)
        layout.addWidget(gamepad_group)
        layout.addLayout(buttons)
        self.setLayout(layout)
        self.resize(420, 260)

    def _populate_xinput_combo(self, combo: QComboBox) -> None:
        combo.addItem("None", "")
        for name in XINPUT_BUTTONS:
            combo.addItem(name, name)

    def _set_combo_value(self, combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index < 0:
            index = 0
        combo.setCurrentIndex(index)

    def updated_settings(self) -> HotkeySettings:
        return HotkeySettings(
            start_hotkey=self.start_hotkey_edit.keySequence().toString(),
            clock_hotkey=self.clock_hotkey_edit.keySequence().toString(),
            start_xinput_button=str(self.start_xinput_combo.currentData() or ""),
            clock_xinput_button=str(self.clock_xinput_combo.currentData() or ""),
        )


class AnimatedToggleButton(QPushButton):
    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        self._active_color = QColor("#6dd3fb")
        self._inactive_color = QColor("#e5e7eb")
        self._bg_color = self._inactive_color
        self._text_color = QColor("#0b0f14")
        self._default_padding_y = 8
        self._default_padding_x = 16
        self._default_radius = 10
        self._default_height = 38
        self._base_padding_y = self._default_padding_y
        self._base_padding_x = self._default_padding_x
        self._radius = self._default_radius
        self._press_value = 0.0
        self._is_active = False

        self._color_anim = QVariantAnimation(self)
        self._color_anim.setDuration(200)
        self._color_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._color_anim.valueChanged.connect(self._on_color_anim)

        self._press_anim = QVariantAnimation(self)
        self._press_anim.setDuration(90)
        self._press_anim.setEasingCurve(QEasingCurve.OutQuad)
        self._press_anim.valueChanged.connect(self._on_press_anim)

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(self._default_height)
        self._update_style()

    def set_colors(self, inactive: QColor, active: QColor) -> None:
        self._inactive_color = inactive
        self._active_color = active
        target = self._active_color if self._is_active else self._inactive_color
        self._bg_color = target
        self._update_style()

    def set_state(self, active: bool, animate: bool = True) -> None:
        if self._is_active == active and not animate:
            return
        self._is_active = active
        target = self._active_color if active else self._inactive_color
        if animate:
            self._animate_to_color(target)
        else:
            self._bg_color = target
            self._update_style()

    def _animate_to_color(self, target: QColor) -> None:
        if self._color_anim.state() == QVariantAnimation.Running:
            self._color_anim.stop()
        self._color_anim.setStartValue(self._bg_color)
        self._color_anim.setEndValue(target)
        self._color_anim.start()

    def _on_color_anim(self, value) -> None:
        if isinstance(value, QColor):
            self._bg_color = value
            self._update_style()

    def _on_press_anim(self, value) -> None:
        self._press_value = float(value)
        self._update_style()

    def _animate_press(self, target: float) -> None:
        if self._press_anim.state() == QVariantAnimation.Running:
            self._press_anim.stop()
        self._press_anim.setStartValue(self._press_value)
        self._press_anim.setEndValue(target)
        self._press_anim.start()

    def _update_style(self) -> None:
        pad_y = max(0, self._base_padding_y - int(self._press_value * 2))
        pad_x = max(0, self._base_padding_x - int(self._press_value * 2))
        self.setStyleSheet(
            f"padding: {pad_y}px {pad_x}px; border-radius: {self._radius}px;"
            f"background-color: {qcolor_to_hex(self._bg_color)};"
            f"color: {qcolor_to_hex(self._text_color)};"
        )

    def set_scale(self, scale: float) -> None:
        scale = max(0.6, min(2.0, float(scale)))
        self._base_padding_y = max(4, int(self._default_padding_y * scale))
        self._base_padding_x = max(6, int(self._default_padding_x * scale))
        self._radius = max(6, int(self._default_radius * scale))
        height = max(28, int(self._default_height * scale))
        self.setFixedHeight(height)
        self._update_style()

    def mousePressEvent(self, event) -> None:
        self._animate_press(1.0)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._animate_press(0.0)
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event) -> None:
        self._animate_press(0.0)
        super().leaveEvent(event)


class ClickableLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class SuperGoalProgressBar(QWidget):
    def __init__(
        self,
        width: int,
        height: int,
        start_color: QColor,
        end_color: QColor,
        bg_color: QColor,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._progress = 0.0
        self._start_color = start_color
        self._end_color = end_color
        self._bg_color = bg_color
        self.setFixedSize(max(1, width), max(1, height))

    def set_colors(
        self, start_color: QColor, end_color: QColor, bg_color: QColor
    ) -> None:
        self._start_color = start_color
        self._end_color = end_color
        self._bg_color = bg_color
        self.update()

    def set_bar_size(self, width: int, height: int) -> None:
        self.setFixedSize(max(1, width), max(1, height))
        self.update()

    def set_progress(self, progress: float) -> None:
        clamped = max(0.0, min(1.0, float(progress)))
        if math.isclose(self._progress, clamped):
            return
        self._progress = clamped
        self.update()

    def paintEvent(self, event) -> None:
        rect = QRectF(self.rect())
        if rect.width() <= 0 or rect.height() <= 0:
            return
        radius = min(rect.height() / 2.0, 6.0)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._bg_color)
        painter.drawRoundedRect(rect, radius, radius)
        if self._progress <= 0:
            return
        painter.save()
        fill_width = rect.width() * self._progress
        painter.setClipRect(QRectF(rect.x(), rect.y(), fill_width, rect.height()))
        gradient = QLinearGradient(rect.topLeft(), rect.topRight())
        gradient.setColorAt(0.0, self._start_color)
        gradient.setColorAt(1.0, self._end_color)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(rect, radius, radius)
        painter.restore()


class GlowFrame(QFrame):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._intensity = 0.0
        self._color = QColor("#ff3b30")
        self._radius = 18
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def set_intensity(self, value: float) -> None:
        value = max(0.0, min(1.0, float(value)))
        if abs(self._intensity - value) < 0.001:
            return
        self._intensity = value
        self.update()

    def paintEvent(self, event) -> None:
        if self._intensity <= 0.0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        base = QColor(self._color)
        layers = [
            (8, 50),
            (5, 90),
            (2, 180),
        ]
        for width, alpha in layers:
            color = QColor(base)
            color.setAlpha(int(alpha * self._intensity))
            pen = QPen(color, width)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            inset = int(width / 2) + 1
            rect = self.rect().adjusted(inset, inset, -inset, -inset)
            painter.drawRoundedRect(rect, self._radius, self._radius)


class CalendarHeaderWidget(QWidget):
    def __init__(
        self,
        ui_settings: UiSettings,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._settings = ui_settings
        self._week_start = QDate.currentDate()
        self._totals: list[int] = [0] * 7
        self.setMinimumHeight(CALENDAR_HEADER_HEIGHT)
        self.setFixedHeight(CALENDAR_HEADER_HEIGHT)
        self.setMinimumWidth(CALENDAR_LEFT_MARGIN + (CALENDAR_MIN_DAY_WIDTH * 7))

    def set_week_start(self, date: QDate) -> None:
        if not date.isValid():
            return
        self._week_start = date
        self.update()

    def set_daily_totals(self, totals: list[int]) -> None:
        if len(totals) != 7:
            return
        self._totals = [max(0, int(value)) for value in totals]
        self.update()

    def _day_width(self) -> float:
        available = max(0.0, self.width() - CALENDAR_LEFT_MARGIN)
        return max(CALENDAR_MIN_DAY_WIDTH, available / 7)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return

        header_bg = QColor(self._settings.bg_color)
        header_bg.setAlpha(200)
        painter.fillRect(rect, header_bg)

        day_width = self._day_width()
        label_color = QColor(self._settings.text_color)
        label_color.setAlpha(220)
        painter.setPen(label_color)
        header_font = QFont(painter.font())
        header_font.setBold(True)
        painter.setFont(header_font)
        totals_font = QFont(painter.font())
        totals_font.setBold(False)
        point_size = totals_font.pointSize()
        if point_size > 0:
            totals_font.setPointSize(max(7, point_size - 2))
        for day_idx in range(7):
            date = self._week_start.addDays(day_idx)
            x = CALENDAR_LEFT_MARGIN + (day_idx * day_width)
            header_rect = QRectF(x, 0, day_width, CALENDAR_HEADER_HEIGHT)
            day_rect = QRectF(x, 0, day_width, CALENDAR_HEADER_HEIGHT * 0.6)
            total_rect = QRectF(
                x,
                CALENDAR_HEADER_HEIGHT * 0.55,
                day_width,
                CALENDAR_HEADER_HEIGHT * 0.45,
            )
            label = date.toString("ddd MMM d")
            painter.setFont(header_font)
            painter.drawText(day_rect, Qt.AlignCenter, label)
            painter.setFont(totals_font)
            total_label = format_duration_hm(self._totals[day_idx])
            painter.drawText(total_rect, Qt.AlignCenter, total_label)

        sep_color = QColor(self._settings.graph_grid_color)
        sep_color.setAlpha(180)
        painter.setPen(QPen(sep_color, 1.2))
        for day_idx in range(8):
            x = CALENDAR_LEFT_MARGIN + (day_idx * day_width)
            painter.drawLine(x, 0, x, CALENDAR_HEADER_HEIGHT)
        painter.drawLine(
            CALENDAR_LEFT_MARGIN,
            CALENDAR_HEADER_HEIGHT - 1,
            CALENDAR_LEFT_MARGIN + (day_width * 7),
            CALENDAR_HEADER_HEIGHT - 1,
        )

        today = QDate.currentDate()
        if self._week_start <= today <= self._week_start.addDays(6):
            day_idx = self._week_start.daysTo(today)
            x = CALENDAR_LEFT_MARGIN + (day_idx * day_width)
            border_rect = QRectF(x + 1, 1, day_width - 2, CALENDAR_HEADER_HEIGHT - 2)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor("#ef4444"), 2))
            painter.drawRect(border_rect)


class CalendarViewWidget(QWidget):
    def __init__(
        self,
        ui_settings: UiSettings,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._settings = ui_settings
        self._entries: list[dict[str, object]] = []
        self._entry_colors: list[QColor] = []
        self._entry_labels: list[str] = []
        self._blocks: list[CalendarBlock] = []
        self._hover_block: Optional[CalendarBlock] = None
        self._week_start = QDate.currentDate()
        self._scale_minutes = 15.0
        self._scale_step_minutes = 15
        self._scale_anim: Optional[QVariantAnimation] = None
        self._profile_color = QColor(ui_settings.accent_color)
        self._left_margin = CALENDAR_LEFT_MARGIN
        self._header_height = 0
        self._day_padding = CALENDAR_DAY_PADDING
        self._bottom_padding = CALENDAR_BOTTOM_PADDING
        self._min_day_width = CALENDAR_MIN_DAY_WIDTH
        self.setMinimumWidth(self._left_margin + (self._min_day_width * 7))
        self.setMouseTracking(True)
        self._update_geometry()

    def set_entries(
        self,
        entries: list[dict[str, object]],
        *,
        profile_color: Optional[QColor] = None,
        entry_colors: Optional[list[QColor]] = None,
        entry_labels: Optional[list[str]] = None,
    ) -> None:
        self._entries = list(entries)
        if profile_color is not None and profile_color.isValid():
            self._profile_color = QColor(profile_color)
        self._entry_colors = (
            [QColor(color) for color in entry_colors]
            if entry_colors is not None
            else []
        )
        self._entry_labels = (
            [str(label) for label in entry_labels]
            if entry_labels is not None
            else []
        )
        self._rebuild_blocks()
        self.update()

    def set_week_start(self, date: QDate) -> None:
        if not date.isValid():
            return
        self._week_start = date
        self._rebuild_blocks()
        self.update()

    def set_profile_color(self, color: QColor) -> None:
        if not color.isValid():
            return
        self._profile_color = QColor(color)
        self.update()

    def set_scale_minutes(self, minutes: int, *, animate: bool = False) -> None:
        minutes = max(5, int(minutes))
        self._scale_step_minutes = minutes
        if math.isclose(minutes, self._scale_minutes):
            return
        if animate:
            self._animate_scale(minutes)
            return
        if self._scale_anim is not None:
            self._scale_anim.stop()
        self._scale_minutes = float(minutes)
        self._update_geometry()
        self.update()

    def _animate_scale(self, minutes: int) -> None:
        start = float(self._scale_minutes)
        end = float(minutes)
        if math.isclose(start, end):
            return
        if self._scale_anim is None:
            self._scale_anim = QVariantAnimation(self)
            self._scale_anim.setEasingCurve(QEasingCurve.InOutCubic)
            self._scale_anim.valueChanged.connect(self._on_scale_animated)
        self._scale_anim.stop()
        self._scale_anim.setStartValue(start)
        self._scale_anim.setEndValue(end)
        self._scale_anim.setDuration(220)
        self._scale_anim.start()

    def _on_scale_animated(self, value: object) -> None:
        try:
            self._scale_minutes = float(value)
        except (TypeError, ValueError):
            return
        self._update_geometry()
        self.update()

    def _update_geometry(self) -> None:
        total_minutes = 24 * 60
        pixels_per_minute = self._pixels_per_minute()
        day_height = total_minutes * pixels_per_minute
        height = day_height + self._bottom_padding
        self.setFixedHeight(int(height))
        self.updateGeometry()

    def _parse_time_value(self, value: object) -> Optional[QTime]:
        if value is None:
            return None
        text = str(value).strip()
        if not text or text.lower() == "n/a":
            return None
        for fmt in ("HH:mm:ss", "HH:mm"):
            time = QTime.fromString(text, fmt)
            if time.isValid():
                return time
        return None

    def _entry_end_time(self, entry: dict[str, object], start: QTime) -> Optional[QTime]:
        end_time = self._parse_time_value(entry.get("end_time"))
        if end_time is not None:
            return end_time
        try:
            duration = int(entry.get("duration_seconds", 0))
        except (TypeError, ValueError):
            duration = 0
        if duration <= 0:
            return None
        return start.addSecs(duration)

    def _rebuild_blocks(self) -> None:
        self._blocks = []
        if not self._entries:
            return
        start_date = self._week_start
        end_date = start_date.addDays(6)
        for idx, entry in enumerate(self._entries):
            date_key = entry.get("date")
            if not date_key:
                continue
            date = QDate.fromString(str(date_key), "yyyy-MM-dd")
            if not date.isValid():
                continue
            if date < start_date or date > end_date:
                continue
            start_time = self._parse_time_value(entry.get("start_time"))
            if start_time is None:
                continue
            end_time = self._entry_end_time(entry, start_time)
            if end_time is None:
                continue
            start_seconds = (
                start_time.hour() * 3600
                + start_time.minute() * 60
                + start_time.second()
            )
            end_seconds = (
                end_time.hour() * 3600
                + end_time.minute() * 60
                + end_time.second()
            )
            if end_seconds <= start_seconds:
                continue
            start_seconds = max(0, min(24 * 3600, start_seconds))
            end_seconds = max(0, min(24 * 3600, end_seconds))
            if end_seconds <= start_seconds:
                continue
            label = f"{self._format_time(start_time)} - {self._format_time(end_time)}"
            color = (
                self._entry_colors[idx]
                if idx < len(self._entry_colors)
                else self._profile_color
            )
            if not color.isValid():
                color = self._profile_color
            profile_label = (
                self._entry_labels[idx] if idx < len(self._entry_labels) else ""
            )
            self._blocks.append(
                CalendarBlock(
                    day_index=start_date.daysTo(date),
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                    label=label,
                    color=color,
                    profile_label=profile_label,
                )
            )
        self._blocks.sort(key=lambda block: (block.day_index, block.start_seconds))

    def _day_width(self) -> float:
        available = max(0.0, self.width() - self._left_margin)
        return max(self._min_day_width, available / 7)

    def _scale_unit_height(self) -> float:
        min_minutes = CALENDAR_SCALE_MINUTES_MIN
        max_minutes = CALENDAR_SCALE_MINUTES_MAX
        min_height = CALENDAR_SCALE_HEIGHT_MIN
        max_height = CALENDAR_SCALE_HEIGHT_MAX
        minutes = max(min_minutes, min(max_minutes, self._scale_minutes))
        if max_minutes <= min_minutes:
            return max_height
        ratio = (minutes - min_minutes) / (max_minutes - min_minutes)
        return max_height + (min_height - max_height) * ratio

    def _pixels_per_minute(self) -> float:
        return self._scale_unit_height() / max(1, self._scale_minutes)

    def _format_duration_seconds(self, seconds: int) -> str:
        seconds = max(0, int(seconds))
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        hours = minutes // 60
        rem = minutes % 60
        if hours <= 0:
            return f"{minutes}m"
        if rem == 0:
            return f"{hours}h"
        return f"{hours}h {rem}m"

    def _format_time(self, time: QTime) -> str:
        if self._settings.use_24h_time:
            return time.toString("HH:mm")
        return time.toString("h:mm AP")

    def _format_hour_label(self, hour: int) -> str:
        time = QTime(hour, 0)
        if self._settings.use_24h_time:
            return time.toString("HH:mm")
        return time.toString("h AP")

    def _text_color_for_block(self, color: QColor) -> QColor:
        luminance = (color.red() * 0.299) + (color.green() * 0.587) + (color.blue() * 0.114)
        return QColor("#111827") if luminance >= 150 else QColor("#f8fafc")

    def _block_rect(self, block: CalendarBlock) -> QRectF:
        day_width = self._day_width()
        pixels_per_minute = self._pixels_per_minute()
        start_y = (block.start_seconds / 60.0) * pixels_per_minute
        end_y = (block.end_seconds / 60.0) * pixels_per_minute
        height = max(6.0, end_y - start_y)
        x = self._left_margin + (block.day_index * day_width) + self._day_padding
        width = day_width - (self._day_padding * 2)
        return QRectF(x, start_y, width, height)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return
        painter.fillRect(rect, self.palette().window())

        day_width = self._day_width()
        total_minutes = 24 * 60
        pixels_per_minute = self._pixels_per_minute()
        day_height = total_minutes * pixels_per_minute
        grid_top = 0
        grid_bottom = day_height

        base_day_color = QColor(self.palette().window().color())
        alt_day_color = QColor(base_day_color)
        if base_day_color.value() > 128:
            alt_day_color = alt_day_color.darker(104)
        else:
            alt_day_color = alt_day_color.lighter(110)
        for day_idx in range(7):
            x = self._left_margin + (day_idx * day_width)
            day_rect = QRectF(x, grid_top, day_width, day_height)
            painter.fillRect(day_rect, alt_day_color if day_idx % 2 else base_day_color)

        grid_color = QColor(self._settings.graph_grid_color)
        grid_color.setAlpha(120)
        minor_pen = QPen(grid_color, 1)
        major_color = QColor(self._settings.graph_grid_color)
        major_color.setAlpha(200)
        major_pen = QPen(major_color, 1.3)
        painter.setPen(minor_pen)
        minute_step = max(1, int(self._scale_step_minutes))
        for minute in range(0, total_minutes + 1, minute_step):
            y = grid_top + (minute * pixels_per_minute)
            painter.drawLine(
                self._left_margin, y, self._left_margin + (day_width * 7), y
            )
        painter.setPen(major_pen)
        for hour in range(0, 25):
            minute = hour * 60
            y = grid_top + (minute * pixels_per_minute)
            painter.drawLine(
                self._left_margin, y, self._left_margin + (day_width * 7), y
            )

        sep_color = QColor(self._settings.graph_grid_color)
        sep_color.setAlpha(180)
        painter.setPen(QPen(sep_color, 1.2))
        for day_idx in range(8):
            x = self._left_margin + (day_idx * day_width)
            painter.drawLine(x, grid_top, x, grid_bottom)

        today = QDate.currentDate()
        if self._week_start <= today <= self._week_start.addDays(6):
            day_idx = self._week_start.daysTo(today)
            x = self._left_margin + (day_idx * day_width)
            border_rect = QRectF(x + 1, grid_top + 1, day_width - 2, grid_bottom - 2)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor("#ef4444"), 2))
            painter.drawRect(border_rect)

        painter.setFont(QFont(painter.font()))
        time_label_font = QFont(painter.font())
        point_size = time_label_font.pointSize()
        if point_size > 0:
            time_label_font.setPointSize(max(7, point_size - 2))
        painter.setFont(time_label_font)
        for minute in range(0, total_minutes + 1, minute_step):
            y = grid_top + (minute * pixels_per_minute)
            label_rect = QRectF(0, y - 8, self._left_margin - 8, 16)
            time = QTime(0, 0).addSecs(minute * 60)
            label = (
                time.toString("HH:mm")
                if self._settings.use_24h_time
                else time.toString("h:mm AP")
            )
            painter.drawText(
                label_rect,
                Qt.AlignRight | Qt.AlignVCenter,
                label,
            )

        for block in self._blocks:
            block_color = QColor(block.color)
            block_fill = QColor(block_color)
            block_fill.setAlpha(170)
            block_pen = QPen(block_color, 1.2)
            text_color = self._text_color_for_block(block_color)
            rect = self._block_rect(block).translated(0, grid_top)
            block_height = rect.height()
            painter.setPen(block_pen)
            painter.setBrush(block_fill)
            painter.drawRoundedRect(rect, 6, 6)
            if block_height >= 18:
                painter.setPen(text_color)
                painter.drawText(
                    rect.adjusted(6, 4, -6, -4),
                    Qt.AlignLeft | Qt.AlignTop,
                    block.label,
                )

        today = QDate.currentDate()
        if self._week_start <= today <= self._week_start.addDays(6):
            day_idx = self._week_start.daysTo(today)
            now = QTime.currentTime()
            now_seconds = (now.hour() * 3600) + (now.minute() * 60) + now.second()
            y = grid_top + ((now_seconds / 60.0) * pixels_per_minute)
            line_color = QColor(self._settings.accent_color)
            line_color.setAlpha(230)
            painter.setPen(QPen(line_color, 1.6))
            x0 = self._left_margin + (day_idx * day_width)
            x1 = x0 + day_width
            painter.drawLine(x0, y, x1, y)
            bubble_text = self._format_time(now)
            metrics = painter.fontMetrics()
            bubble_width = metrics.horizontalAdvance(bubble_text) + 12
            bubble_height = metrics.height() + 6
            bubble_x = x0 + 6
            bubble_y = y - (bubble_height / 2)
            bubble_y = max(grid_top + 2, min(grid_bottom - bubble_height - 2, bubble_y))
            bubble_rect = QRectF(bubble_x, bubble_y, bubble_width, bubble_height)
            painter.setPen(Qt.NoPen)
            painter.setBrush(line_color)
            painter.drawRoundedRect(bubble_rect, 8, 8)
            painter.setPen(self._text_color_for_block(line_color))
            painter.drawText(
                bubble_rect,
                Qt.AlignCenter,
                bubble_text,
            )

        if not self._blocks:
            hint_color = QColor(self._settings.total_today_color)
            hint_color.setAlpha(200)
            painter.setPen(hint_color)
            hint_rect = QRectF(
                self._left_margin,
                grid_top,
                day_width * 7,
                max(0.0, day_height),
            )
            painter.drawText(
                hint_rect,
                Qt.AlignCenter,
                "No entries for this week",
            )

    def mouseMoveEvent(self, event) -> None:
        if not self._blocks:
            if self._hover_block is not None:
                self._hover_block = None
                QToolTip.hideText()
            return
        pos = event.position()
        hovered = None
        for block in self._blocks:
            if self._block_rect(block).contains(pos):
                hovered = block
                break
        if hovered == self._hover_block:
            return
        self._hover_block = hovered
        if hovered is None:
            QToolTip.hideText()
            return
        seconds = hovered.end_seconds - hovered.start_seconds
        tooltip = self._format_duration_seconds(seconds)
        if hovered.profile_label:
            text = f"{hovered.profile_label}\nTotal: {tooltip}"
        else:
            text = f"Total: {tooltip}"
        QToolTip.showText(event.globalPos(), text, self)

    def leaveEvent(self, event) -> None:
        self._hover_block = None
        QToolTip.hideText()
        super().leaveEvent(event)


class CalendarViewDialog(QDialog):
    def __init__(
        self,
        parent: "CountdownWindow",
        ui_settings: UiSettings,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Calendar View")
        self.setModal(True)
        self._parent = parent
        self._settings = ui_settings
        self._scale_options = [5, 10, 15, 30, 60]
        self._entries_by_profile: dict[str, list[dict[str, object]]] = {}

        self.profile_combo = QComboBox()
        self.profile_combo.addItem("All Profiles", CALENDAR_PROFILE_ALL)
        for label in parent._profile_labels():
            self.profile_combo.addItem(label, label)
        self._restore_profile_selection()

        self.week_label = QLabel()
        self.prev_week_btn = QPushButton("Prev")
        self.next_week_btn = QPushButton("Next")
        self.today_btn = QPushButton("This Week")

        self.scale_label = QLabel()
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(0, len(self._scale_options) - 1)
        self._restore_scale_selection()
        self.scale_slider.setTickPosition(QSlider.TicksBelow)
        self.scale_slider.setTickInterval(1)

        self.header_widget = CalendarHeaderWidget(ui_settings)
        self.header_scroll = QScrollArea()
        self.header_scroll.setWidget(self.header_widget)
        self.header_scroll.setWidgetResizable(False)
        self.header_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.header_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.header_scroll.setFixedHeight(CALENDAR_HEADER_HEIGHT)

        self.calendar_widget = CalendarViewWidget(ui_settings)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.calendar_widget)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._week_start = self._monday_for_date(QDate.currentDate())
        self._sync_week_label()
        self._sync_scale_label()
        self._sync_calendar()

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Profile"))
        controls.addWidget(self.profile_combo)
        controls.addSpacing(12)
        controls.addWidget(self.prev_week_btn)
        controls.addWidget(self.week_label)
        controls.addWidget(self.next_week_btn)
        controls.addWidget(self.today_btn)
        controls.addStretch(1)
        controls.addWidget(QLabel("Scale"))
        controls.addWidget(self.scale_slider)
        controls.addWidget(self.scale_label)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(close_btn)

        layout = QVBoxLayout()
        layout.addLayout(controls)
        layout.addWidget(self.header_scroll)
        layout.addWidget(self.scroll_area)
        layout.addLayout(footer)
        self.setLayout(layout)
        self.resize(980, 640)

        self.profile_combo.currentTextChanged.connect(self._sync_calendar)
        self.prev_week_btn.clicked.connect(lambda: self._shift_week(-7))
        self.next_week_btn.clicked.connect(lambda: self._shift_week(7))
        self.today_btn.clicked.connect(self._jump_to_current_week)
        self.scale_slider.valueChanged.connect(self._sync_scale_label)
        self.scale_slider.valueChanged.connect(self._sync_calendar_scale)
        self.scroll_area.horizontalScrollBar().valueChanged.connect(
            self.header_scroll.horizontalScrollBar().setValue
        )
        self.scroll_area.verticalScrollBar().rangeChanged.connect(
            self._sync_header_margin
        )
        self._sync_header_margin()
        self._update_calendar_width()

        self._now_timer = QTimer(self)
        self._now_timer.setInterval(30000)
        self._now_timer.timeout.connect(self.calendar_widget.update)
        self._now_timer.start()

    def _monday_for_date(self, date: QDate) -> QDate:
        if not date.isValid():
            return QDate.currentDate()
        return date.addDays(1 - date.dayOfWeek())

    def _sync_week_label(self) -> None:
        start = self._week_start
        end = start.addDays(6)
        if start.year() == end.year():
            label = f"{start.toString('MMM d')} - {end.toString('MMM d, yyyy')}"
        else:
            label = f"{start.toString('MMM d, yyyy')} - {end.toString('MMM d, yyyy')}"
        self.week_label.setText(label)

    def _sync_scale_label(self) -> None:
        minutes = self._scale_options[self.scale_slider.value()]
        unit = "hour" if minutes >= 60 and minutes % 60 == 0 else "min"
        if unit == "hour":
            hours = minutes // 60
            text = f"{hours} hour" if hours == 1 else f"{hours} hours"
        else:
            text = f"{minutes} min"
        self.scale_label.setText(text)

    def _sync_calendar_scale(self) -> None:
        minutes = self._scale_options[self.scale_slider.value()]
        self.calendar_widget.set_scale_minutes(minutes, animate=True)
        self._update_calendar_width()
        self._save_scale_selection()

    def _sync_calendar_scale_initial(self) -> None:
        minutes = self._scale_options[self.scale_slider.value()]
        self.calendar_widget.set_scale_minutes(minutes, animate=False)
        self._update_calendar_width()

    def _restore_scale_selection(self) -> None:
        settings = get_settings()
        saved = settings.value("calendar/scale_minutes", None)
        if isinstance(saved, str) and saved:
            try:
                saved = int(saved)
            except ValueError:
                saved = None
        if isinstance(saved, (int, float)):
            try:
                index = self._scale_options.index(int(saved))
                self.scale_slider.setValue(index)
                return
            except ValueError:
                pass
        self.scale_slider.setValue(self._scale_options.index(15))

    def _save_scale_selection(self) -> None:
        settings = get_settings()
        minutes = self._scale_options[self.scale_slider.value()]
        settings.setValue("calendar/scale_minutes", int(minutes))
        settings.sync()

    def _sync_header_margin(self) -> None:
        scrollbar = self.scroll_area.verticalScrollBar()
        width = scrollbar.sizeHint().width() if scrollbar.maximum() > 0 else 0
        self.header_scroll.setViewportMargins(0, 0, width, 0)

    def _update_calendar_width(self) -> None:
        viewport_width = self.scroll_area.viewport().width()
        target_width = max(self.calendar_widget.minimumWidth(), viewport_width)
        self.calendar_widget.setFixedWidth(target_width)
        self.header_widget.setFixedWidth(target_width)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_calendar_width()

    def _load_entries_for_profile(self, label: str) -> list[dict[str, object]]:
        if label in self._entries_by_profile:
            return self._entries_by_profile[label]
        path = self._parent._profile_file_path(label)
        fallback_goal = self._parent._load_profile_super_goal_seconds(label)
        entries, _, _ = self._parent._load_log_entries_from_path(
            path, fallback_goal_seconds=fallback_goal
        )
        self._entries_by_profile[label] = entries
        return entries

    def _load_all_profile_entries(
        self,
    ) -> tuple[list[dict[str, object]], list[QColor], list[str]]:
        combined: list[dict[str, object]] = []
        colors: list[QColor] = []
        labels: list[str] = []
        for label in self._parent._profile_labels():
            entries = self._load_entries_for_profile(label)
            color = self._parent._profile_color(label)
            for entry in entries:
                combined.append(entry)
                colors.append(QColor(color))
                labels.append(label)
        return combined, colors, labels

    def _compute_week_totals(self, entries: list[dict[str, object]]) -> list[int]:
        totals = [0] * 7
        start = self._week_start
        end = start.addDays(6)
        for entry in entries:
            date_key = entry.get("date")
            if not date_key:
                continue
            date = QDate.fromString(str(date_key), "yyyy-MM-dd")
            if not date.isValid():
                continue
            if date < start or date > end:
                continue
            try:
                duration = int(entry.get("duration_seconds", 0))
            except (TypeError, ValueError):
                duration = 0
            if duration <= 0:
                continue
            index = start.daysTo(date)
            if 0 <= index < 7:
                totals[index] += duration
        return totals

    def _sync_calendar_all(self) -> None:
        entries, colors, labels = self._load_all_profile_entries()
        self.calendar_widget.set_entries(
            entries,
            profile_color=self._parent.settings.accent_color,
            entry_colors=colors,
            entry_labels=labels,
        )
        self.calendar_widget.set_week_start(self._week_start)
        self.header_widget.set_week_start(self._week_start)
        self.header_widget.set_daily_totals(self._compute_week_totals(entries))
        self._sync_calendar_scale_initial()

    def _sync_calendar(self) -> None:
        profile_data = self.profile_combo.currentData()
        if not profile_data:
            return
        self._save_profile_selection()
        if profile_data == CALENDAR_PROFILE_ALL:
            self._sync_calendar_all()
            return
        if not isinstance(profile_data, str):
            return
        entries = self._load_entries_for_profile(profile_data)
        color = self._parent._profile_color(profile_data)
        self.calendar_widget.set_entries(entries, profile_color=color)
        self.calendar_widget.set_week_start(self._week_start)
        self.header_widget.set_week_start(self._week_start)
        self.header_widget.set_daily_totals(self._compute_week_totals(entries))
        self._sync_calendar_scale_initial()
        self._save_profile_selection()

    def _restore_profile_selection(self) -> None:
        settings = get_settings()
        saved = settings.value("calendar/selected_profile", "")
        if isinstance(saved, str) and saved:
            index = self.profile_combo.findData(saved)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)
                return
        active_index = self.profile_combo.findData(self._parent._active_profile)
        if active_index >= 0:
            self.profile_combo.setCurrentIndex(active_index)

    def _save_profile_selection(self) -> None:
        settings = get_settings()
        value = self.profile_combo.currentData()
        if value is None:
            return
        settings.setValue("calendar/selected_profile", str(value))
        settings.sync()

    def _shift_week(self, days: int) -> None:
        self._week_start = self._week_start.addDays(days)
        self._sync_week_label()
        self._sync_calendar()

    def _jump_to_current_week(self) -> None:
        self._week_start = self._monday_for_date(QDate.currentDate())
        self._sync_week_label()
        self._sync_calendar()


class TrendsGraphWidget(QWidget):
    def __init__(
        self,
        series: list[GraphSeries],
        ui_settings: UiSettings,
        active_label: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._series = list(series)
        self._settings = ui_settings
        self._active_label = active_label
        self._enabled_labels = {entry.label for entry in self._series}
        self._scale = "week"
        self._range_days = 7
        self._points_by_series: dict[str, list[QPointF]] = {}
        self._values_by_series: dict[str, list[int]] = {}
        self._dates: list[QDate] = []
        self._hover_index: Optional[int] = None
        self._point_count = 7
        self._dot_radius = 4
        self.setMinimumHeight(240)
        self.setMinimumWidth(420)
        self.setMouseTracking(True)

    def set_scale(self, scale: str, range_days: int) -> None:
        scale = scale.lower().strip()
        if scale not in ("week", "month", "year"):
            return
        self._scale = scale
        self._range_days = max(1, int(range_days))
        self._point_count = 12 if self._scale == "year" else self._range_days
        self.update()

    def point_count(self) -> int:
        return self._point_count

    def set_enabled_labels(self, labels: set[str]) -> None:
        self._enabled_labels = set(labels)
        self.update()

    def _visible_series(self) -> list[GraphSeries]:
        if not self._enabled_labels:
            return []
        return [s for s in self._series if s.label in self._enabled_labels]

    def _series_order(self) -> list[GraphSeries]:
        series = self._visible_series()
        if not series or not self._active_label:
            return list(series)
        active = [s for s in series if s.label == self._active_label]
        rest = [s for s in series if s.label != self._active_label]
        return rest + active if active else list(series)

    def _build_daily_dates(self, days: int) -> list[QDate]:
        end = QDate.currentDate()
        start = end.addDays(-(days - 1))
        dates: list[QDate] = []
        for offset in range(days):
            date = start.addDays(offset)
            dates.append(date)
        return dates

    def _values_for_dates(
        self, totals: dict[str, int], dates: list[QDate]
    ) -> list[int]:
        values: list[int] = []
        for date in dates:
            value = totals.get(date.toString("yyyy-MM-dd"), 0)
            try:
                values.append(int(value))
            except (TypeError, ValueError):
                values.append(0)
        return values

    def _build_month_dates(self) -> list[QDate]:
        end = QDate.currentDate()
        start = QDate(end.year(), end.month(), 1).addMonths(-11)
        return [start.addMonths(offset) for offset in range(12)]

    def _values_for_months(
        self, totals: dict[str, int], dates: list[QDate]
    ) -> list[int]:
        monthly_totals: dict[tuple[int, int], int] = {}
        for date_key, value in totals.items():
            date = QDate.fromString(date_key, "yyyy-MM-dd")
            if not date.isValid():
                continue
            try:
                seconds = int(value)
            except (TypeError, ValueError):
                continue
            key = (date.year(), date.month())
            monthly_totals[key] = monthly_totals.get(key, 0) + seconds
        values: list[int] = []
        for date in dates:
            values.append(monthly_totals.get((date.year(), date.month()), 0))
        return values

    def _label_indices(self, count: int, show_all: bool) -> range:
        if show_all or count <= 7:
            return range(count)
        step = max(1, int(math.ceil(count / 7)))
        return range(0, count, step)

    def _tooltip_date_label(self, date: QDate) -> str:
        if self._scale == "year":
            return date.toString("MMM yyyy")
        return date.toString("yyyy-MM-dd")

    def _format_duration(self, seconds: int) -> str:
        seconds = max(0, int(seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours} hours {minutes} min {secs} sec"

    def _tooltip_text(self, index: int) -> str:
        if index < 0 or index >= len(self._dates):
            return ""
        date = self._dates[index]
        lines = [f"Date: {self._tooltip_date_label(date)}"]
        entries: list[str] = []
        for series in self._series_order():
            values = self._values_by_series.get(series.label, [])
            seconds = values[index] if index < len(values) else 0
            if seconds <= 0:
                continue
            entries.append(f"{series.label}: {self._format_duration(seconds)}")
        if not entries:
            entries.append("No activity")
        lines.extend(entries)
        return "\n".join(lines)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if self._scale == "year":
            dates = self._build_month_dates()
        else:
            dates = self._build_daily_dates(self._range_days)

        if not dates:
            return
        visible_series = self._visible_series()
        if not visible_series:
            self._points_by_series = {}
            self._values_by_series = {}
            self._dates = dates
            painter.setPen(self._settings.text_color)
            painter.drawText(self.rect(), Qt.AlignCenter, "No profiles selected")
            return

        values_by_series: dict[str, list[int]] = {}
        max_value = 0
        for series in visible_series:
            if self._scale == "year":
                values = self._values_for_months(series.totals, dates)
            else:
                values = self._values_for_dates(series.totals, dates)
            values_by_series[series.label] = values
            if values:
                max_value = max(max_value, max(values))

        scale_limit_seconds = (
            (self._settings.day_end_hour * 3600)
            + (self._settings.day_end_minute * 60)
        )
        scale_seconds = max_value
        if scale_limit_seconds > 0:
            scale_seconds = min(scale_seconds, scale_limit_seconds)
        max_hour_label = int(scale_seconds // 3600) if scale_seconds > 0 else 0
        digit_count = len(str(max(1, max_hour_label)))
        margin_left = max(24, 12 + (digit_count * 8))
        margin_right = 24
        margin_top = 16
        margin_bottom = 36
        plot_rect = self.rect().adjusted(
            margin_left, margin_top, -margin_right, -margin_bottom
        )
        if plot_rect.width() <= 0 or plot_rect.height() <= 0:
            return

        self._points_by_series = {}
        self._values_by_series = values_by_series
        self._dates = dates

        if max_value <= 0:
            painter.setPen(self._settings.text_color)
            painter.drawText(self.rect(), Qt.AlignCenter, "No data for range")
            return
        if scale_seconds <= 0:
            scale_seconds = max_value

        count = len(dates)
        step_x = (
            plot_rect.width() / (count - 1)
            if count > 1
            else 0
        )
        for series in visible_series:
            values = values_by_series.get(series.label, [])
            points: list[QPointF] = []
            for idx, value in enumerate(values):
                clamped_value = min(value, scale_seconds)
                ratio = (
                    clamped_value / scale_seconds if scale_seconds > 0 else 0
                )
                x = plot_rect.left() + (step_x * idx)
                y = plot_rect.bottom() - (ratio * plot_rect.height())
                points.append(QPointF(x, y))
            self._points_by_series[series.label] = points

        max_hours = int(scale_seconds // 3600) if scale_seconds > 0 else 0
        if max_hours == 0:
            max_hours = 1
        grid_color = QColor(self._settings.graph_grid_color)
        grid_start = QColor(grid_color)
        grid_start.setAlpha(0)
        grid_end = QColor(grid_color)
        grid_end.setAlpha(140)
        grid_gradient = QLinearGradient(
            plot_rect.left(), 0, plot_rect.right(), 0
        )
        grid_gradient.setColorAt(0, grid_start)
        grid_gradient.setColorAt(1, grid_end)
        grid_pen = QPen(QBrush(grid_gradient), 1)
        painter.setPen(grid_pen)
        for hour in range(max_hours + 1):
            ratio = hour / max_hours if max_hours > 0 else 0
            y = plot_rect.bottom() - (ratio * plot_rect.height())
            painter.drawLine(plot_rect.left(), y, plot_rect.right(), y)

        tick_color = QColor(self._settings.graph_grid_color)
        tick_color.setAlpha(210)
        painter.setPen(tick_color)
        base_font = QFont(painter.font())
        tick_font = QFont(base_font)
        point_size = tick_font.pointSize()
        if point_size > 0:
            tick_font.setPointSize(max(7, point_size - 2))
        else:
            pixel_size = tick_font.pixelSize()
            if pixel_size > 0:
                tick_font.setPixelSize(max(7, pixel_size - 2))
        painter.setFont(tick_font)
        metrics = painter.fontMetrics()
        tick_width = plot_rect.left() - 6
        for hour in range(max_hours + 1):
            ratio = hour / max_hours if max_hours > 0 else 0
            y = plot_rect.bottom() - (ratio * plot_rect.height())
            label_rect = QRectF(
                0,
                y - (metrics.height() / 2),
                max(0, tick_width),
                metrics.height(),
            )
            painter.drawText(label_rect, Qt.AlignRight | Qt.AlignVCenter, str(hour))

        painter.setFont(base_font)
        axis_color = QColor(self._settings.graph_grid_color)
        axis_color.setAlpha(180)
        painter.setPen(QPen(axis_color, 1.2))
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.bottomRight())

        ordered_series = self._series_order()
        for series in ordered_series:
            values = values_by_series.get(series.label, [])
            points = self._points_by_series.get(series.label, [])
            if not points or (values and max(values) <= 0):
                continue
            if len(points) > 1:
                path = QPainterPath(points[0])
                for idx in range(1, len(points)):
                    path.lineTo(points[idx])

                fill_path = QPainterPath(path)
                fill_path.lineTo(points[-1].x(), plot_rect.bottom())
                fill_path.lineTo(points[0].x(), plot_rect.bottom())
                fill_path.closeSubpath()

                gradient = QLinearGradient(
                    0, plot_rect.top(), 0, plot_rect.bottom()
                )
                fill_top = QColor(series.fill_color)
                fill_bottom = QColor(series.fill_color)
                fill_top.setAlpha(
                    100 if series.label == self._active_label else 70
                )
                fill_bottom.setAlpha(0)
                gradient.setColorAt(0, fill_top)
                gradient.setColorAt(1, fill_bottom)
                painter.fillPath(fill_path, gradient)

        for series in ordered_series:
            values = values_by_series.get(series.label, [])
            points = self._points_by_series.get(series.label, [])
            if not points or (values and max(values) <= 0):
                continue
            if len(points) > 1:
                pen_color = QColor(series.line_color)
                pen_color.setAlpha(
                    230 if series.label == self._active_label else 180
                )
                pen = QPen(
                    pen_color,
                    2.6 if series.label == self._active_label else 2.0,
                )
                pen.setCapStyle(Qt.RoundCap)
                pen.setJoinStyle(Qt.RoundJoin)
                painter.setPen(pen)
                path = QPainterPath(points[0])
                for idx in range(1, len(points)):
                    path.lineTo(points[idx])
                painter.drawPath(path)

        for series in ordered_series:
            values = values_by_series.get(series.label, [])
            points = self._points_by_series.get(series.label, [])
            if not points or (values and max(values) <= 0):
                continue
            dot_color = QColor(series.dot_color)
            dot_color.setAlpha(
                230 if series.label == self._active_label else 180
            )
            painter.setPen(Qt.NoPen)
            painter.setBrush(dot_color)
            dot_radius = self._dot_radius if series.label == self._active_label else 3
            for point in points:
                painter.drawEllipse(point, dot_radius, dot_radius)

        if self._scale == "year":
            labels = [date.toString("MMM") for date in dates]
            indices = self._label_indices(len(labels), True)
        elif self._scale == "week":
            labels = [date.toString("ddd") for date in dates]
            indices = self._label_indices(len(labels), True)
        else:
            labels = [date.toString("d") for date in dates]
            indices = self._label_indices(len(labels), False)

        label_color = QColor(self._settings.text_color)
        label_color.setAlpha(200)
        painter.setPen(label_color)
        metrics = painter.fontMetrics()
        label_y = self.rect().bottom() - 12
        label_points = None
        if self._active_label in self._points_by_series:
            label_points = self._points_by_series[self._active_label]
        elif self._points_by_series:
            label_points = next(iter(self._points_by_series.values()))
        for idx in indices:
            if label_points is None or idx >= len(label_points):
                continue
            text = labels[idx]
            text_width = metrics.horizontalAdvance(text)
            x = label_points[idx].x() - (text_width / 2)
            painter.drawText(int(x), int(label_y), text)

    def mouseMoveEvent(self, event) -> None:
        if not self._points_by_series:
            QToolTip.hideText()
            self._hover_index = None
            return
        closest_index = None
        closest_dist = None
        for points in self._points_by_series.values():
            for idx, point in enumerate(points):
                dist = (point.x() - event.position().x()) ** 2 + (
                    point.y() - event.position().y()
                ) ** 2
                if closest_dist is None or dist < closest_dist:
                    closest_dist = dist
                    closest_index = idx
        hit_radius = (self._dot_radius + 4) ** 2
        if closest_index is None or closest_dist is None or closest_dist > hit_radius:
            if self._hover_index is not None:
                QToolTip.hideText()
            self._hover_index = None
            return
        if self._hover_index == closest_index:
            return
        self._hover_index = closest_index
        QToolTip.showText(
            event.globalPos(),
            self._tooltip_text(closest_index),
            self,
        )

    def leaveEvent(self, event) -> None:
        self._hover_index = None
        QToolTip.hideText()
        super().leaveEvent(event)


class GraphDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        series: list[GraphSeries],
        ui_settings: UiSettings,
        active_label: str,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Trends Graph")
        self.setModal(True)
        self._settings = ui_settings
        self._series = list(series)
        self._legend_checks: dict[str, QCheckBox] = {}

        self.graph = TrendsGraphWidget(self._series, ui_settings, active_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.graph)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setMinimumHeight(self.graph.minimumHeight())
        self.scroll_area.setStyleSheet(
            "QScrollBar:horizontal {"
            "background: #111827; height: 12px; margin: 0 12px;"
            "border-radius: 6px;"
            "}"
            "QScrollBar::handle:horizontal {"
            "background: #4b5563; min-width: 30px; border-radius: 6px;"
            "}"
            "QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {"
            "background: none; width: 0px;"
            "}"
            "QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {"
            "background: #0b0f14;"
            "}"
        )

        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["Week", "Month", "Year"])
        self.range_combo = QComboBox()
        self.range_combo.addItems(["7 days", "30 days"])

        self.scale_combo.currentTextChanged.connect(self._sync_graph)
        self.range_combo.currentTextChanged.connect(self._sync_graph)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Scale"))
        controls.addWidget(self.scale_combo)
        controls.addSpacing(12)
        controls.addWidget(QLabel("Range"))
        controls.addWidget(self.range_combo)
        controls.addStretch(1)

        legend_group = QGroupBox("Legend")
        legend_layout = QGridLayout()
        columns = 3
        for idx, entry in enumerate(self._series):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(6)
            swatch = QFrame()
            swatch.setFixedSize(12, 12)
            swatch.setStyleSheet(
                f"background-color: {qcolor_to_hex(entry.line_color)};"
                "border-radius: 2px;"
            )
            checkbox = QCheckBox(entry.label)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._sync_series_filter)
            row.addWidget(swatch)
            row.addWidget(checkbox)
            row.addStretch(1)
            row_widget = QWidget()
            row_widget.setLayout(row)
            grid_row = idx // columns
            grid_col = idx % columns
            legend_layout.addWidget(row_widget, grid_row, grid_col)
            self._legend_checks[entry.label] = checkbox
        for col in range(columns):
            legend_layout.setColumnStretch(col, 1)
        legend_group.setLayout(legend_layout)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(close_btn)

        layout = QVBoxLayout()
        layout.addLayout(controls)
        layout.addWidget(legend_group)
        layout.addWidget(self.scroll_area)
        layout.addLayout(footer)
        self.setLayout(layout)

        self._sync_series_filter()
        self._sync_graph()

    def _sync_graph(self) -> None:
        scale = self.scale_combo.currentText().lower()
        range_text = self.range_combo.currentText()
        range_days = 7
        if range_text:
            try:
                range_days = int(range_text.split()[0])
            except (TypeError, ValueError):
                range_days = 7
        if scale == "year":
            self.range_combo.setEnabled(False)
            range_days = 365
        else:
            self.range_combo.setEnabled(True)
        self.graph.set_scale(scale, range_days)
        self._update_graph_width()

    def _sync_series_filter(self) -> None:
        enabled = {
            label
            for label, checkbox in self._legend_checks.items()
            if checkbox.isChecked()
        }
        self.graph.set_enabled_labels(enabled)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self._update_graph_width)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_graph_width()

    def _update_graph_width(self) -> None:
        viewport_width = self.scroll_area.viewport().width()
        viewport_height = self.scroll_area.viewport().height()
        if viewport_width <= 0 or viewport_height <= 0:
            return
        point_count = max(1, self.graph.point_count())
        base_width = max(1, viewport_width)
        target_width = (
            base_width
            if point_count <= 7
            else int(base_width * (point_count / 7))
        )
        self.graph.setFixedWidth(target_width)
        self.graph.setFixedHeight(viewport_height)


class LogsCalendarWidget(QCalendarWidget):
    def paintCell(self, painter: QPainter, rect: QRect, date: QDate) -> None:
        super().paintCell(painter, rect, date)
        if date == QDate.currentDate():
            painter.save()
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor("#ef4444"), 2))
            painter.drawRect(rect.adjusted(1, 1, -1, -1))
            painter.restore()


class LogsDialog(QDialog):
    def __init__(
        self,
        parent: "CountdownWindow",
        entries: list[dict[str, object]],
        daily_goals: dict[str, int],
        fallback_goal_seconds: int,
        daily_totals: dict[str, int],
        ui_settings: UiSettings,
        active_profile: str,
        profile_labels: list[str],
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Daily Logs")
        self.setModal(True)
        self._parent = parent
        self._entries = entries
        self._daily_goals = daily_goals
        self._fallback_goal_seconds = fallback_goal_seconds
        self._daily_totals = daily_totals
        self._settings = ui_settings
        self._current_profile = active_profile
        self._profile_labels = list(profile_labels)
        self._profile_cache: dict[
            str, tuple[list[dict[str, object]], dict[str, int], dict[str, int], int]
        ] = {
            active_profile: (
                entries,
                daily_totals,
                daily_goals,
                fallback_goal_seconds,
            )
        }
        self.resize(820, 520)

        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(180)
        self.profile_combo.blockSignals(True)
        self.profile_combo.addItem("All Profiles", LOGS_PROFILE_ALL)
        for label in self._profile_labels:
            self.profile_combo.addItem(label, label)
        self._restore_profile_selection(active_profile)
        self.profile_combo.blockSignals(False)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        calendar = LogsCalendarWidget()
        self.date_edit.setCalendarWidget(calendar)
        self.date_edit.dateChanged.connect(self._refresh_table)

        self.range_combo = QComboBox()
        self.range_combo.addItems(["Day", "Week (7 days)"])
        self.range_combo.currentIndexChanged.connect(self._refresh_table)

        self.goto_today_btn = QPushButton("Go to Today")
        self.goto_today_btn.clicked.connect(self._jump_to_today)

        self.goal_label = QLabel()
        self.week_total_label = QLabel()
        self.week_total_label.setVisible(False)

        self.table = QTableWidget(0, 5)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Profile"))
        controls.addWidget(self.profile_combo)
        controls.addSpacing(12)
        controls.addWidget(QLabel("Date"))
        controls.addWidget(self.date_edit)
        controls.addSpacing(12)
        controls.addWidget(QLabel("Range"))
        controls.addWidget(self.range_combo)
        controls.addSpacing(12)
        controls.addWidget(self.goto_today_btn)
        controls.addStretch(1)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(close_btn)

        layout = QVBoxLayout()
        layout.addLayout(controls)
        layout.addWidget(self.goal_label)
        layout.addWidget(self.week_total_label)
        layout.addWidget(self.table)
        layout.addLayout(footer)
        self.setLayout(layout)

        self.profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        self._sync_selected_profile()
        self._refresh_table()

    def _load_profile_data(
        self, label: str
    ) -> tuple[list[dict[str, object]], dict[str, int], dict[str, int], int]:
        cached = self._profile_cache.get(label)
        if cached is not None:
            return cached
        path = self._parent._profile_file_path(label)
        fallback_goal = self._parent._load_profile_super_goal_seconds(label)
        entries, totals, goals = self._parent._load_log_entries_from_path(
            path, fallback_goal_seconds=fallback_goal
        )
        cached = (entries, totals, goals, fallback_goal)
        self._profile_cache[label] = cached
        return cached

    def _load_all_profile_data(
        self,
    ) -> tuple[list[dict[str, object]], dict[str, int]]:
        cached = self._profile_cache.get(LOGS_PROFILE_ALL)
        if cached is not None:
            entries, totals, _, _ = cached
            return entries, totals
        combined_entries: list[dict[str, object]] = []
        combined_totals: dict[str, int] = {}
        for label in self._profile_labels:
            entries, totals, _, _ = self._load_profile_data(label)
            for entry in entries:
                tagged = dict(entry)
                tagged["profile_label"] = label
                combined_entries.append(tagged)
            for date_key, total in totals.items():
                combined_totals[date_key] = combined_totals.get(date_key, 0) + total
        cached = (combined_entries, combined_totals, {}, 0)
        self._profile_cache[LOGS_PROFILE_ALL] = cached
        return combined_entries, combined_totals

    def _restore_profile_selection(self, fallback: str) -> None:
        settings = get_settings()
        saved = settings.value("logs/selected_profile", "")
        if isinstance(saved, str) and saved:
            index = self.profile_combo.findData(saved)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)
                return
        active_index = self.profile_combo.findData(fallback)
        if active_index >= 0:
            self.profile_combo.setCurrentIndex(active_index)

    def _save_profile_selection(self) -> None:
        settings = get_settings()
        value = self.profile_combo.currentData()
        if value is None:
            return
        settings.setValue("logs/selected_profile", str(value))
        settings.sync()

    def _apply_profile_selection(self, data: str, *, save: bool) -> None:
        if data == self._current_profile:
            return
        if data == LOGS_PROFILE_ALL:
            entries, totals = self._load_all_profile_data()
            self._current_profile = data
            self._entries = entries
            self._daily_totals = totals
            self._daily_goals = {}
            self._fallback_goal_seconds = 0
        else:
            entries, totals, goals, fallback_goal = self._load_profile_data(data)
            self._current_profile = data
            self._entries = entries
            self._daily_totals = totals
            self._daily_goals = goals
            self._fallback_goal_seconds = fallback_goal
        if save:
            self._save_profile_selection()
        self._refresh_table()

    def _sync_selected_profile(self) -> None:
        data = self.profile_combo.currentData()
        if not isinstance(data, str):
            return
        self._apply_profile_selection(data, save=False)

    def _jump_to_today(self) -> None:
        self.date_edit.setDate(QDate.currentDate())
        QTimer.singleShot(0, self._scroll_to_today)

    def _scroll_to_today(self) -> None:
        if self.table.rowCount() <= 0:
            return
        today_key = QDate.currentDate().toString("yyyy-MM-dd")
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None and item.text() == today_key:
                self.table.scrollToItem(item)
                return

    def _on_profile_changed(self, index: int) -> None:
        if index < 0:
            return
        data = self.profile_combo.itemData(index)
        if not isinstance(data, str):
            return
        self._apply_profile_selection(data, save=True)

    def _goal_seconds_for_date(self, date_key: str) -> int:
        if self._current_profile == LOGS_PROFILE_ALL:
            return 0
        return self._daily_goals.get(date_key, self._fallback_goal_seconds)

    def _refresh_table(self) -> None:
        show_profile = self._current_profile == LOGS_PROFILE_ALL
        if show_profile:
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels(
                ["Date", "Profile", "Started", "Paused", "Duration", "% Goal"]
            )
        else:
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(
                ["Date", "Started", "Paused", "Duration", "% Goal"]
            )
        selected_date = self.date_edit.date()
        date_key = selected_date.toString("yyyy-MM-dd")
        if self._current_profile == LOGS_PROFILE_ALL:
            self.goal_label.setText("Daily super goal: varies by profile")
        else:
            goal_seconds = self._goal_seconds_for_date(date_key)
            if goal_seconds > 0:
                self.goal_label.setText(
                    f"Daily super goal: {format_duration_hms(goal_seconds)}"
                )
            else:
                self.goal_label.setText("Daily super goal: not set")
        range_mode = self.range_combo.currentText().lower()
        if range_mode.startswith("week"):
            start_date = selected_date
            end_date = selected_date.addDays(6)
            start_key = start_date.toString("yyyy-MM-dd")
            end_key = end_date.toString("yyyy-MM-dd")
            rows = [
                entry
                for entry in self._entries
                if start_key <= str(entry.get("date", "")) <= end_key
            ]
            total_seconds = 0
            date_cursor = start_date
            while date_cursor <= end_date:
                total_seconds += self._daily_totals.get(
                    date_cursor.toString("yyyy-MM-dd"), 0
                )
                date_cursor = date_cursor.addDays(1)
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            self.week_total_label.setText(
                f"Week total: {hours}:{minutes:02d}:{seconds:02d}"
            )
            self.week_total_label.setToolTip(
                f"{start_date.toString('yyyy-MM-dd')} to "
                f"{end_date.toString('yyyy-MM-dd')}"
            )
            self.week_total_label.setVisible(True)
        else:
            rows = [entry for entry in self._entries if entry["date"] == date_key]
            self.week_total_label.setVisible(False)
        rows.sort(key=lambda entry: (entry.get("date", ""), entry.get("start_time", "")))
        self.table.setRowCount(len(rows))
        for row_idx, entry in enumerate(rows):
            duration_seconds = int(entry["duration_seconds"])
            duration = format_duration_hms(duration_seconds)
            entry_date_key = str(entry.get("date", ""))
            if self._current_profile == LOGS_PROFILE_ALL:
                entry_goal_seconds = int(entry.get("goal_seconds", 0) or 0)
            else:
                entry_goal_seconds = self._goal_seconds_for_date(entry_date_key)
            percent = format_percent(duration_seconds, entry_goal_seconds)
            start_time = entry.get("start_time") or "N/A"
            end_time = entry.get("end_time") or "N/A"
            if show_profile:
                values = [
                    entry["date"],
                    entry.get("profile_label", "Unknown"),
                    start_time,
                    end_time,
                    duration,
                    percent,
                ]
            else:
                values = [entry["date"], start_time, end_time, duration, percent]
            row_color = None
            if show_profile:
                label = entry.get("profile_label")
                if isinstance(label, str) and label:
                    row_color = QColor(self._parent._profile_color(label))
                    row_color.setAlpha(40)
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemIsEnabled)
                if row_color is not None:
                    item.setBackground(QBrush(row_color))
                self.table.setItem(row_idx, col, item)

class CountdownWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Countdown Master")
        self.setMinimumSize(420, 300)
        self._base_window_size = self.minimumSize()
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        init_paths()
        self._data_dir = DATA_DIR or resolve_data_dir()
        self.settings = self._load_settings()
        self.hotkey_settings = self._load_hotkey_settings()
        self._default_profile_files = {label: fname for label, fname in DEFAULT_PROFILES}
        self._custom_profiles = self._load_custom_profiles()
        self._active_profile = self._load_active_profile()
        self._profile_colors = self._load_profile_colors()
        self.super_goal_seconds = self._load_profile_super_goal_seconds(
            self._active_profile
        )
        self._data_file_path = self._profile_file_path(self._active_profile)
        self._migrate_profile_logs()
        (
            self.log_entries,
            self.daily_totals,
            self.daily_goals,
        ) = self._load_log_entries()
        self._last_added_time_entry = None
        self._last_added_time_index = None
        self._active_session_start = None
        self._active_session_seconds = 0
        self._active_session_date_key = None
        self.remaining_seconds = 0
        self.timer_active = False
        self.clock_active = False
        self.clock_elapsed_seconds = 0
        self._clock_offset_seconds = 0
        self._acrylic_enabled = sys.platform == "win32"
        self._is_macos = sys.platform == "darwin"
        self._mac_blur_supported = self._is_macos and QMacVisualEffect is not None
        self._blur_supported = (
            self._acrylic_enabled or self._mac_blur_supported or not self._is_macos
        )
        self._font_family = default_font_family()
        self._heatmap_base_size = self.settings.heatmap_cell_size
        self._heatmap_cell_size = self.settings.heatmap_cell_size
        self._heatmap_month_padding_base = self.settings.heatmap_month_padding
        self._heatmap_month_padding = self.settings.heatmap_month_padding
        self._heatmap_month_label_size_base = self.settings.heatmap_month_label_size
        self._heatmap_month_label_size = self.settings.heatmap_month_label_size
        self._heatmap_label_height = max(
            10, self._heatmap_month_label_size + 6
        )
        self._heatmap_label_spacing_base = 4
        self._heatmap_label_spacing = self._heatmap_label_spacing_base
        self._heatmap_spacing = 2
        self._heatmap_year = QDate.currentDate().year()
        self._always_on_top = self.settings.always_on_top
        self._scale_factor = 1.0
        self._year_total_anim = None
        self._start_shortcut = None
        self._clock_shortcut = None
        self._xinput_reader = GamepadReader()
        self._xinput_timer = QTimer(self)
        self._xinput_timer.setInterval(50)
        self._xinput_timer.timeout.connect(self._poll_xinput)
        self._xinput_prev_buttons = 0
        self._xinput_start_mask = 0
        self._xinput_clock_mask = 0

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

        self.day_time_timer = QTimer(self)
        self.day_time_timer.setInterval(1000)
        self.day_time_timer.timeout.connect(self._update_day_time_label)
        self.day_time_timer.start()

        self._build_ui()
        self._apply_window_flag_defaults()
        self._window_save_timer = QTimer(self)
        self._window_save_timer.setSingleShot(True)
        self._window_save_timer.setInterval(250)
        self._window_save_timer.timeout.connect(self._save_window_geometry)
        self._connected_screens = set()
        self._restore_window_geometry()
        self._ensure_window_visible()
        self._connect_screen_signals()
        self._goal_pulse_anim = QVariantAnimation(self)
        self._goal_pulse_anim.setDuration(2000)
        self._goal_pulse_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._goal_pulse_anim.setStartValue(0.0)
        self._goal_pulse_anim.setEndValue(1.0)
        self._goal_pulse_anim.valueChanged.connect(self._on_goal_pulse_value)
        self._goal_pulse_anim.finished.connect(self._on_goal_pulse_finished)
        self._apply_settings()
        self._apply_hotkey_settings()
        if self._always_on_top:
            self._toggle_always_on_top(True, save=False)

    def _build_ui(self) -> None:
        self.central = QWidget()
        self.central.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCentralWidget(self.central)

        self.background = QFrame()
        self.background.setObjectName("backgroundFrame")

        self.blur_effect = None
        if not self._mac_blur_supported:
            self.blur_effect = QGraphicsBlurEffect()
            self.background.setGraphicsEffect(self.blur_effect)

        self.mac_visual_effect = None
        if self._mac_blur_supported:
            self.mac_visual_effect = QMacVisualEffect()
            self.mac_visual_effect.setAttribute(
                Qt.WA_TransparentForMouseEvents, True
            )

        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setObjectName("timerLabel")

        self.day_time_label = QLabel("Day time left: 00:00:00")
        self.day_time_label.setAlignment(Qt.AlignCenter)
        self.day_time_label.setObjectName("dayTimeLabel")

        self.total_today_label = QLabel("Total today: 00:00:00")
        self.total_today_label.setAlignment(Qt.AlignCenter)
        self.total_today_label.setObjectName("totalTodayLabel")

        self.goal_left_label = QLabel("Super goal left: please set goal")
        self.goal_left_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.goal_left_label.setObjectName("goalLeftLabel")

        self.super_goal_bar = SuperGoalProgressBar(
            self.settings.super_goal_bar_width,
            self.settings.super_goal_bar_height,
            self.settings.super_goal_bar_start,
            self.settings.super_goal_bar_end,
            self.settings.super_goal_bar_bg,
        )

        self.year_total_label = ClickableLabel("Year total: 00:00:00")
        self.year_total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.year_total_label.setObjectName("yearTotalLabel")
        self.year_total_label.setCursor(Qt.PointingHandCursor)
        self.year_total_label.clicked.connect(self._cycle_year_total_display)

        self.status_label = QLabel("Right click to set goal time")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("statusLabel")

        self.longest_streak_label = QLabel("Longest streak: 0 days")
        self.longest_streak_label.setAlignment(Qt.AlignCenter)
        self.longest_streak_label.setObjectName("longestStreakLabel")

        self.current_streak_label = QLabel("Current streak: 0 days")
        self.current_streak_label.setAlignment(Qt.AlignCenter)
        self.current_streak_label.setObjectName("currentStreakLabel")

        self.heatmap_widget = self._build_heatmap()

        self.profile_label = QLabel("Profile")
        self.profile_label.setObjectName("profileLabel")
        self.profile_combo = QComboBox()
        self.profile_combo.setObjectName("profileCombo")
        self.profile_combo.setMinimumWidth(180)
        self._populate_profile_combo()
        self.profile_combo.currentIndexChanged.connect(self._on_profile_changed)

        self.toggle_btn = AnimatedToggleButton("Start")
        self.toggle_btn.clicked.connect(self._toggle_timer)
        self.clock_btn = AnimatedToggleButton("Clock On")
        self.clock_btn.clicked.connect(self._toggle_clock)

        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        button_row.addStretch(1)
        button_row.addWidget(self.toggle_btn)
        button_row.addWidget(self.clock_btn)
        button_row.addStretch(1)

        content = QWidget()
        content_layout = QVBoxLayout()
        profile_row = QHBoxLayout()
        profile_row.setContentsMargins(0, 0, 0, 0)
        profile_row.setSpacing(8)
        profile_row.addWidget(self.profile_label)
        profile_row.addWidget(self.profile_combo)
        profile_row.addStretch(1)
        content_layout.addLayout(profile_row)
        content_layout.addStretch(1)
        content_layout.addWidget(self.timer_label)
        content_layout.addWidget(self.day_time_label)
        content_layout.addWidget(self.total_today_label)
        goal_row = QWidget()
        goal_row_layout = QHBoxLayout()
        goal_row_layout.setContentsMargins(0, 0, 0, 0)
        goal_row_layout.setSpacing(12)
        self.goal_left_group = QWidget()
        goal_left_layout = QHBoxLayout()
        goal_left_layout.setContentsMargins(0, 0, 0, 0)
        goal_left_layout.setSpacing(8)
        goal_left_layout.addWidget(self.goal_left_label)
        goal_left_layout.addWidget(self.super_goal_bar)
        self.goal_left_group.setLayout(goal_left_layout)
        goal_row_layout.addWidget(self.goal_left_group)
        goal_row_layout.addStretch(1)
        goal_row_layout.addWidget(self.year_total_label)
        goal_row.setLayout(goal_row_layout)
        content_layout.addWidget(goal_row)
        content_layout.addWidget(self.heatmap_widget, alignment=Qt.AlignCenter)
        streak_row = QWidget()
        streak_layout = QHBoxLayout()
        streak_layout.setContentsMargins(0, 0, 0, 0)
        streak_layout.setSpacing(16)
        streak_layout.addStretch(1)
        streak_layout.addWidget(self.longest_streak_label)
        streak_layout.addWidget(self.current_streak_label)
        streak_layout.addStretch(1)
        streak_row.setLayout(streak_layout)
        content_layout.addWidget(streak_row)
        content_layout.addWidget(self.status_label)
        content_layout.addLayout(button_row)
        content_layout.addStretch(1)
        content.setLayout(content_layout)

        self.glow_frame = GlowFrame()

        self.stack_layout = QStackedLayout()
        self.stack_layout.setStackingMode(QStackedLayout.StackAll)
        self.stack_layout.setContentsMargins(18, 18, 18, 18)
        if self.mac_visual_effect is not None:
            self.stack_layout.addWidget(self.mac_visual_effect)
        self.stack_layout.addWidget(self.background)
        self.stack_layout.addWidget(content)
        self.stack_layout.addWidget(self.glow_frame)
        self.central.setLayout(self.stack_layout)

    def _show_context_menu(self, pos) -> None:
        menu = self._build_context_menu()
        menu.exec(self.mapToGlobal(pos))

    def _build_context_menu(self):
        menu = QMenu(self)
        set_time = QAction("Set Current Goal", self)
        add_time = QAction("Add to time", self)
        undo_add_time = QAction("Undo added time", self)
        undo_add_time.setEnabled(self._last_added_time_entry is not None)
        set_super_goal = QAction("Set Daily Super Goal", self)
        logs = QAction("Logs", self)
        calendar_view = QAction("Calendar View", self)
        trends_graph = QAction("Trends Graph", self)
        profile_editor = QAction("Profile Editor", self)
        always_on_top = QAction("Always On Top", self)
        always_on_top.setCheckable(True)
        always_on_top.setChecked(self._always_on_top)
        reset_clock = QAction("Clock reset", self)
        reset_time = QAction("Reset Timer", self)
        settings = QAction("Settings", self)
        hotkey_settings = QAction("Hotkey Settings", self)
        quit_action = QAction("Quit", self)
        set_time.triggered.connect(self._open_set_time)
        add_time.triggered.connect(self._open_add_time)
        undo_add_time.triggered.connect(self._undo_added_time)
        set_super_goal.triggered.connect(self._open_set_super_goal)
        logs.triggered.connect(self._open_logs)
        calendar_view.triggered.connect(self._open_calendar_view)
        trends_graph.triggered.connect(self._open_trends_graph)
        profile_editor.triggered.connect(self._open_profile_editor)
        always_on_top.toggled.connect(self._toggle_always_on_top)
        reset_clock.triggered.connect(self._reset_clock)
        reset_time.triggered.connect(self._reset_timer)
        settings.triggered.connect(self._open_settings)
        hotkey_settings.triggered.connect(self._open_hotkey_settings)
        quit_action.triggered.connect(self._quit_app)
        visibility_menu = menu.addMenu("Show/Hide UI")
        self._add_visibility_action(
            visibility_menu, "Heat map", "show_heatmap"
        )
        self._add_visibility_action(
            visibility_menu, "Day time left", "show_day_time"
        )
        self._add_visibility_action(
            visibility_menu, "Total today", "show_total_today"
        )
        self._add_visibility_action(
            visibility_menu, "Year total (week/avg)", "show_year_total"
        )
        self._add_visibility_action(
            visibility_menu, "Super goal left", "show_super_goal_left"
        )
        self._add_visibility_action(
            visibility_menu, "Status text (set goal time)", "show_status_label"
        )
        self._add_visibility_action(
            visibility_menu, "Start button", "show_start_button"
        )
        self._add_visibility_action(
            visibility_menu, "Clock button", "show_clock_button"
        )
        self._add_visibility_action(
            visibility_menu, "Longest streak", "show_longest_streak"
        )
        self._add_visibility_action(
            visibility_menu, "Current streak", "show_current_streak"
        )
        visibility_menu.addSeparator()
        reset_visibility = QAction("Reset UI Visibility", self)
        reset_visibility.triggered.connect(self._reset_ui_visibility)
        visibility_menu.addAction(reset_visibility)
        time_menu = menu.addMenu("Time")
        time_menu.addAction(set_time)
        time_menu.addAction(add_time)
        time_menu.addAction(undo_add_time)
        time_menu.addAction(set_super_goal)
        time_menu.addSeparator()
        time_menu.addAction(reset_clock)
        time_menu.addAction(reset_time)

        data_menu = menu.addMenu("Data")
        data_menu.addAction(calendar_view)
        data_menu.addAction(logs)
        data_menu.addAction(trends_graph)

        menu.addAction(always_on_top)
        menu.addAction(profile_editor)

        settings_menu = menu.addMenu("Settings")
        settings_menu.addAction(settings)
        settings_menu.addAction(hotkey_settings)

        menu.addSeparator()
        menu.addAction(quit_action)
        return menu

    def _open_set_time(self) -> None:
        hours, minutes = self._seconds_to_hm(self.remaining_seconds)
        seconds = self.remaining_seconds % 60
        super_goal_left_seconds = self._super_goal_left_seconds()
        dialog = SetTimeDialog(
            self,
            hours,
            minutes,
            seconds=seconds,
            super_goal_left_seconds=super_goal_left_seconds,
        )
        if dialog.exec() != QDialog.Accepted:
            return
        self.remaining_seconds = dialog.total_seconds()
        self._update_timer_label()
        self.status_label.setText("Goal time set")

    def _open_add_time(self) -> None:
        dialog = AddTimeDialog(self, use_24h_time=self.settings.use_24h_time)
        if dialog.exec() != QDialog.Accepted:
            return
        hours = dialog.hours_spin.value()
        minutes = dialog.minutes_spin.value()
        duration = hours * 3600 + minutes * 60
        if duration <= 0:
            self.status_label.setText("Add time needs hours or minutes")
            return
        date_key = self._date_key(QDate.currentDate())
        start_time = dialog.start_time_edit.time()
        start_time = QTime(start_time.hour(), start_time.minute(), 0)
        start_time_str = start_time.toString("HH:mm:ss")
        end_time_str = start_time.addSecs(duration).toString("HH:mm:ss")
        goal_seconds = self._goal_seconds_for_date(date_key)
        self.daily_goals[date_key] = goal_seconds
        self._append_log_entry(
            date_key, start_time_str, end_time_str, duration, goal_seconds
        )
        entry = {
            "date": date_key,
            "start_time": start_time_str,
            "end_time": end_time_str,
            "duration_seconds": duration,
            "goal_seconds": goal_seconds,
        }
        self.log_entries.append(entry)
        self._last_added_time_entry = entry
        self._last_added_time_index = len(self.log_entries) - 1
        self.daily_totals[date_key] = self.daily_totals.get(date_key, 0) + duration
        if QDate.currentDate().year() != self._heatmap_year:
            self._refresh_heatmap()
        self._update_heatmap_cell(date_key)
        self._update_total_today_label()
        self.status_label.setText("Added time to today")

    def _undo_added_time(self) -> None:
        if self._last_added_time_entry is None or self._last_added_time_index is None:
            self.status_label.setText("No added time to undo")
            return
        entry = self._last_added_time_entry
        index = self._last_added_time_index
        removed = False
        if 0 <= index < len(self.log_entries) and self.log_entries[index] is entry:
            self.log_entries.pop(index)
            removed = True
        else:
            for i, existing in enumerate(self.log_entries):
                if existing is entry:
                    self.log_entries.pop(i)
                    removed = True
                    break
            if not removed:
                for i, existing in enumerate(self.log_entries):
                    if existing == entry:
                        self.log_entries.pop(i)
                        removed = True
                        break
        self._last_added_time_entry = None
        self._last_added_time_index = None
        if not removed:
            self.status_label.setText("Undo failed: entry not found")
            return
        date_key = str(entry.get("date"))
        try:
            duration = int(entry.get("duration_seconds", 0))
        except (TypeError, ValueError):
            duration = 0
        if date_key:
            updated = max(0, self.daily_totals.get(date_key, 0) - duration)
            if updated <= 0:
                self.daily_totals.pop(date_key, None)
            else:
                self.daily_totals[date_key] = updated
            self._update_heatmap_cell(date_key)
        self._rewrite_log_file(self.log_entries, self.daily_goals)
        self._update_total_today_label()
        self.status_label.setText("Undid added time")

    def _open_set_super_goal(self) -> None:
        hours, minutes = self._seconds_to_hm(self.super_goal_seconds)
        dialog = SetTimeDialog(
            self, hours, minutes, title="Set Daily Super Goal"
        )
        if dialog.exec() != QDialog.Accepted:
            return
        hours = dialog.hours_spin.value()
        minutes = dialog.minutes_spin.value()
        self.super_goal_seconds = hours * 3600 + minutes * 60
        self._save_super_goal()
        self._set_daily_goal(QDate.currentDate(), self.super_goal_seconds, True)
        self._refresh_heatmap()
        self._update_goal_left_label()
        self.status_label.setText("Daily super goal set")

    def _open_logs(self) -> None:
        dialog = LogsDialog(
            self,
            self.log_entries,
            self.daily_goals,
            self.super_goal_seconds,
            self.daily_totals,
            self.settings,
            self._active_profile,
            self._profile_labels(),
        )
        dialog.exec()

    def _open_calendar_view(self) -> None:
        dialog = CalendarViewDialog(self, self.settings)
        dialog.exec()

    def _graph_series(self) -> list[GraphSeries]:
        series: list[GraphSeries] = []
        for label in self._profile_labels():
            if label == self._active_profile:
                totals = dict(self.daily_totals)
            else:
                goal_seconds = self._load_profile_super_goal_seconds(label)
                _, totals, _ = self._load_log_entries_from_path(
                    self._profile_file_path(label),
                    fallback_goal_seconds=goal_seconds,
                )
            series.append(
                GraphSeries(
                    label=label,
                    totals=totals,
                    line_color=self._profile_color(label),
                    dot_color=self._profile_dot_color(label),
                    fill_color=self._profile_fill_color(label),
                )
            )
        return series

    def _open_trends_graph(self) -> None:
        dialog = GraphDialog(
            self, self._graph_series(), self.settings, self._active_profile
        )
        dialog.exec()

    def _open_profile_editor(self) -> None:
        labels = self._profile_labels()
        if not labels:
            self.status_label.setText("No profiles found")
            return
        resolved = {label: self._profile_color(label) for label in labels}
        dialog = ProfileEditorDialog(self, labels, self._active_profile, resolved)
        if dialog.exec() != QDialog.Accepted:
            return
        changed = dialog.changed_colors()
        if not changed:
            return
        for label, color in changed.items():
            fallback = self._profile_fallback_color(label)
            if qcolor_to_hex(color) == qcolor_to_hex(fallback):
                self._clear_profile_color(label)
            else:
                self._set_profile_color(label, color)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(
            self, UiSettings(**self.settings.__dict__), self._blur_supported
        )
        if dialog.exec() != QDialog.Accepted:
            return
        self.settings = dialog.updated_settings()
        self._apply_settings()
        self._save_settings()

    def _open_hotkey_settings(self) -> None:
        dialog = HotkeySettingsDialog(
            self,
            HotkeySettings(**self.hotkey_settings.__dict__),
            self._xinput_reader.available,
            self._xinput_reader.group_label,
        )
        if dialog.exec() != QDialog.Accepted:
            return
        self.hotkey_settings = dialog.updated_settings()
        self._apply_hotkey_settings()
        self._save_hotkey_settings()

    def _quit_app(self) -> None:
        self.close()

    def _reset_timer(self) -> None:
        if self.timer.isActive():
            self.timer.stop()
        self.timer_active = False
        self.clock_active = False
        self._finalize_session()
        self.remaining_seconds = 0
        self.clock_elapsed_seconds = 0
        self._clock_offset_seconds = 0
        self._update_timer_label()
        self.toggle_btn.setText("Start")
        self.toggle_btn.set_state(False)
        self.clock_btn.setText("Clock On")
        self.clock_btn.set_state(False)
        self._update_total_today_label()
        self.status_label.setText("Timer reset")

    def _apply_hotkey_settings(self) -> None:
        self._start_shortcut = self._update_shortcut(
            self._start_shortcut,
            self.hotkey_settings.start_hotkey,
            self._toggle_timer,
        )
        self._clock_shortcut = self._update_shortcut(
            self._clock_shortcut,
            self.hotkey_settings.clock_hotkey,
            self._toggle_clock,
        )
        self._xinput_start_mask = XINPUT_BUTTONS.get(
            self.hotkey_settings.start_xinput_button, 0
        )
        self._xinput_clock_mask = XINPUT_BUTTONS.get(
            self.hotkey_settings.clock_xinput_button, 0
        )
        if (
            self._xinput_reader.available
            and (self._xinput_start_mask or self._xinput_clock_mask)
        ):
            if not self._xinput_timer.isActive():
                self._xinput_prev_buttons = 0
                self._xinput_timer.start()
        else:
            if self._xinput_timer.isActive():
                self._xinput_timer.stop()
            self._xinput_prev_buttons = 0

    def _update_shortcut(
        self,
        shortcut: Optional[QShortcut],
        sequence: str,
        handler,
    ) -> Optional[QShortcut]:
        if not sequence:
            if shortcut is not None:
                shortcut.setEnabled(False)
            return shortcut
        if shortcut is None:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(handler)
            return shortcut
        shortcut.setKey(QKeySequence(sequence))
        shortcut.setEnabled(True)
        return shortcut

    def _poll_xinput(self) -> None:
        buttons = self._xinput_reader.read_buttons()
        if buttons is None:
            self._xinput_prev_buttons = 0
            return
        new_presses = buttons & ~self._xinput_prev_buttons
        self._xinput_prev_buttons = buttons
        if self._xinput_start_mask and (new_presses & self._xinput_start_mask):
            self._toggle_timer()
        if self._xinput_clock_mask and (new_presses & self._xinput_clock_mask):
            self._toggle_clock()

    def _apply_settings(self) -> None:
        blur_radius = self.settings.blur_radius if self._blur_supported else 0
        if self._acrylic_enabled:
            self.setWindowOpacity(1.0)
            if self.blur_effect is not None:
                self.blur_effect.setBlurRadius(0)
            apply_windows_acrylic(
                int(self.winId()), self.settings.bg_color, self.settings.opacity
            )
        elif self._is_macos:
            self.setWindowOpacity(1.0)
            if self.blur_effect is not None:
                self.blur_effect.setBlurRadius(0)
            if self.mac_visual_effect is not None:
                self.mac_visual_effect.setVisible(blur_radius > 0)
        else:
            self.setWindowOpacity(self.settings.opacity)
            if self.blur_effect is not None:
                self.blur_effect.setBlurRadius(blur_radius)

        self.timer_label.setStyleSheet(
            f"color: {qcolor_to_hex(self.settings.text_color)};"
        )
        self.status_label.setStyleSheet(
            f"color: {qcolor_to_hex(self.settings.accent_color)};"
        )
        self.day_time_label.setStyleSheet(
            f"color: {qcolor_to_hex(self.settings.day_time_color)};"
        )
        self.total_today_label.setStyleSheet(
            f"color: {qcolor_to_hex(self.settings.total_today_color)};"
        )
        self.profile_label.setStyleSheet(
            f"color: {qcolor_to_hex(self.settings.total_today_color)};"
        )
        self.goal_left_label.setStyleSheet(
            f"color: {qcolor_to_hex(self.settings.goal_left_color)};"
        )
        self.year_total_label.setStyleSheet(
            f"color: {qcolor_to_hex(self.settings.total_today_color)};"
        )
        self.super_goal_bar.set_colors(
            self.settings.super_goal_bar_start,
            self.settings.super_goal_bar_end,
            self.settings.super_goal_bar_bg,
        )
        self.longest_streak_label.setStyleSheet(
            f"color: {qcolor_to_hex(self.settings.total_today_color)};"
        )
        self.current_streak_label.setStyleSheet(
            f"color: {qcolor_to_hex(self.settings.total_today_color)};"
        )
        self._goal_pulse_anim.setDuration(
            max(200, int(self.settings.goal_pulse_seconds * 1000))
        )
        self.setStyleSheet(
            "QToolTip {"
            f"background-color: {qcolor_to_hex(self.settings.heatmap_hover_bg_color)};"
            f"color: {qcolor_to_hex(self.settings.heatmap_hover_text_color)};"
            f"border: 1px solid {qcolor_to_hex(self.settings.heatmap_hover_text_color)};"
            "padding: 4px;"
            "}"
        )
        self.toggle_btn.set_colors(
            self.settings.accent_color, self.settings.text_color
        )
        self.toggle_btn.set_state(self.timer_active, animate=False)
        self.clock_btn.set_colors(
            self.settings.accent_color, self.settings.text_color
        )
        self.clock_btn.set_state(self.clock_active, animate=False)
        self._heatmap_base_size = self.settings.heatmap_cell_size
        self._heatmap_month_padding_base = self.settings.heatmap_month_padding
        self._heatmap_month_label_size_base = self.settings.heatmap_month_label_size
        resized = self._apply_scaled_metrics()
        if not resized:
            self._refresh_heatmap()
        self._update_day_time_label()
        self._update_total_today_label()
        self._update_goal_left_label()
        self._apply_visibility_settings()

        if self._acrylic_enabled:
            border_color = self.settings.text_color
            self.background.setStyleSheet(
                "#backgroundFrame {"
                "background-color: rgba(0, 0, 0, 0);"
                "border-radius: 18px;"
                f"border: 1px solid rgba({border_color.red()},"
                f"{border_color.green()},{border_color.blue()},40);"
                "}"
            )
        else:
            if self._is_macos:
                bg = qcolor_to_rgba(self.settings.bg_color, self.settings.opacity)
            else:
                bg = qcolor_to_hex(self.settings.bg_color)
            self.background.setStyleSheet(
                "#backgroundFrame {"
                f"background-color: {bg};"
                "border-radius: 18px;"
                "}"
            )

    def _apply_scaled_metrics(self) -> bool:
        self._update_scale_factor()
        scale = self._scale_factor
        timer_size = max(10, int(self.settings.font_size * scale))
        label_size = max(8, int(self.settings.label_size * scale))
        day_time_size = max(8, int(self.settings.day_time_font_size * scale))
        total_today_size = max(8, int(self.settings.total_today_font_size * scale))
        goal_left_size = max(8, int(self.settings.goal_left_font_size * scale))
        self.timer_label.setFont(
            QFont(self._font_family, timer_size, QFont.Bold)
        )
        self.status_label.setFont(QFont(self._font_family, label_size))
        self.day_time_label.setFont(QFont(self._font_family, day_time_size))
        self.total_today_label.setFont(
            QFont(self._font_family, total_today_size)
        )
        self.profile_label.setFont(QFont(self._font_family, label_size))
        self.profile_combo.setFont(QFont(self._font_family, label_size))
        self.profile_combo.setMinimumWidth(max(150, int(180 * scale)))
        self.goal_left_label.setFont(
            QFont(self._font_family, goal_left_size)
        )
        self.year_total_label.setFont(
            QFont(self._font_family, goal_left_size)
        )
        bar_width = max(20, int(self.settings.super_goal_bar_width * scale))
        bar_height = max(4, int(self.settings.super_goal_bar_height * scale))
        self.super_goal_bar.set_bar_size(bar_width, bar_height)
        self.longest_streak_label.setFont(
            QFont(self._font_family, label_size)
        )
        self.current_streak_label.setFont(
            QFont(self._font_family, label_size)
        )
        self.toggle_btn.set_scale(scale)
        self.clock_btn.set_scale(scale)
        self._heatmap_month_label_size = max(
            6, int(self._heatmap_month_label_size_base * scale)
        )
        self._heatmap_label_height = max(
            10, self._heatmap_month_label_size + 6
        )
        self._heatmap_label_spacing = max(
            0, int(round(self._heatmap_label_spacing_base * scale))
        )
        if self.heatmap_container_layout is not None:
            self.heatmap_container_layout.setSpacing(
                self._heatmap_label_spacing
            )
        resized = self._apply_scaled_heatmap_size()
        self._update_month_label_style()
        return resized

    def _update_scale_factor(self) -> None:
        base_width = max(1, self._base_window_size.width())
        base_height = max(1, self._base_window_size.height())
        scale = min(self.width() / base_width, self.height() / base_height)
        self._scale_factor = max(0.75, min(2.0, scale))

    def _apply_visibility_settings(self) -> None:
        self.heatmap_widget.setVisible(self.settings.show_heatmap)
        self.day_time_label.setVisible(self.settings.show_day_time)
        self.total_today_label.setVisible(self.settings.show_total_today)
        self.year_total_label.setVisible(self.settings.show_year_total)
        self.goal_left_group.setVisible(self.settings.show_super_goal_left)
        self.status_label.setVisible(self.settings.show_status_label)
        self.toggle_btn.setVisible(self.settings.show_start_button)
        self.clock_btn.setVisible(self.settings.show_clock_button)
        self.longest_streak_label.setVisible(self.settings.show_longest_streak)
        self.current_streak_label.setVisible(self.settings.show_current_streak)
        self._apply_stack_margins()
        self._update_minimum_size_for_visibility()

    def _apply_stack_margins(self) -> None:
        if not hasattr(self, "stack_layout"):
            return
        if self._all_ui_visible():
            margins = 18
        else:
            margins = 8
        self.stack_layout.setContentsMargins(margins, margins, margins, margins)

    def _all_ui_visible(self) -> bool:
        return (
            self.settings.show_heatmap
            and self.settings.show_day_time
            and self.settings.show_total_today
            and self.settings.show_year_total
            and self.settings.show_super_goal_left
            and self.settings.show_status_label
            and self.settings.show_start_button
            and self.settings.show_clock_button
            and self.settings.show_longest_streak
            and self.settings.show_current_streak
        )

    def _visibility_minimum_size(self) -> QSize:
        if self._all_ui_visible():
            return self._base_window_size
        return QSize(240, 170)

    def _update_minimum_size_for_visibility(self) -> None:
        target_size = self._visibility_minimum_size()
        self.setMinimumSize(target_size)
        if self.width() < target_size.width() or self.height() < target_size.height():
            self.resize(
                max(self.width(), target_size.width()),
                max(self.height(), target_size.height()),
            )

    def _apply_scaled_heatmap_size(self) -> bool:
        scaled_size = int(round(self._heatmap_base_size * self._scale_factor))
        scaled_padding = int(
            round(self._heatmap_month_padding_base * self._scale_factor)
        )
        return self._apply_heatmap_geometry(scaled_size, scaled_padding)

    def _update_month_label_style(self) -> None:
        if not hasattr(self, "month_label_widgets"):
            return
        font = QFont(self._font_family, self._heatmap_month_label_size)
        color = qcolor_to_hex(self.settings.day_time_color)
        for label in self.month_label_widgets:
            label.setFont(font)
            label.setStyleSheet(f"color: {color};")
        if getattr(self, "month_labels_widget", None) is not None:
            self.month_labels_widget.setFixedHeight(
                self._heatmap_label_height
            )
        if (
            getattr(self, "heatmap_grid_widget", None) is not None
            and getattr(self, "heatmap_widget", None) is not None
        ):
            total_height = (
                self.heatmap_grid_widget.height()
                + self._heatmap_label_height
                + self._heatmap_label_spacing
            )
            self.heatmap_widget.setFixedHeight(total_height)

    def _toggle_timer(self) -> None:
        if self.clock_active:
            self._stop_clock("Clock off")
        if self.timer_active:
            self._stop_countdown("Paused")
            return
        if self.remaining_seconds <= 0:
            self.status_label.setText("Set a goal time first")
            return
        self._update_timer_label()
        self.timer.start()
        self.timer_active = True
        self._begin_session()
        self.toggle_btn.setText("Pause")
        self.toggle_btn.set_state(True)
        self.status_label.setText("Counting down")

    def _toggle_clock(self) -> None:
        if self.clock_active:
            self._stop_clock("Clock off")
            return
        if self.timer_active:
            self._stop_countdown("Paused")
        self.clock_elapsed_seconds = self._clock_display_seconds()
        self._update_timer_label(self.clock_elapsed_seconds)
        self.timer.start()
        self.timer_active = False
        self.clock_active = True
        self._begin_session()
        self.clock_btn.setText("Clock Off")
        self.clock_btn.set_state(True)
        self.status_label.setText("Clocking")

    def _stop_countdown(self, status_text: str) -> None:
        if not self.timer_active:
            return
        if self.timer.isActive():
            self.timer.stop()
        self.timer_active = False
        self._finalize_session()
        self.toggle_btn.setText("Start")
        self.toggle_btn.set_state(False)
        self.status_label.setText(status_text)

    def _stop_clock(self, status_text: str) -> None:
        if not self.clock_active:
            return
        if self.timer.isActive():
            self.timer.stop()
        self.clock_active = False
        self._finalize_session()
        self.clock_btn.setText("Clock On")
        self.clock_btn.set_state(False)
        self.status_label.setText(status_text)

    def _reset_clock(self) -> None:
        today_key = self._date_key(QDate.currentDate())
        self._clock_offset_seconds = self._total_seconds_for_day(today_key)
        self.clock_elapsed_seconds = 0
        if self.clock_active or not self.timer_active:
            self._update_timer_label(self.clock_elapsed_seconds)
        self.status_label.setText("Clock reset")

    def _tick(self) -> None:
        if self.clock_active:
            self._record_super_goal_progress(1)
            self.clock_elapsed_seconds = self._clock_display_seconds()
            self._update_timer_label(self.clock_elapsed_seconds)
            return
        if self.remaining_seconds <= 0:
            self._handle_time_up()
            return
        self.remaining_seconds -= 1
        self._record_super_goal_progress(1)
        self._update_timer_label()
        if self.remaining_seconds <= 0:
            self._handle_time_up()

    def _update_timer_label(self, total_seconds: Optional[int] = None) -> None:
        if total_seconds is None:
            total_seconds = self.remaining_seconds
        total_seconds = max(0, int(total_seconds))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        self.timer_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def _handle_time_up(self) -> None:
        self.timer.stop()
        self.timer_active = False
        self.status_label.setText("Time's up!")
        self._finalize_session()
        self.toggle_btn.setText("Start")
        self.toggle_btn.set_state(False)
        self._trigger_goal_pulse()
        self._trigger_attention()

    def _trigger_goal_pulse(self) -> None:
        if self.settings.goal_pulse_seconds <= 0:
            return
        if self._goal_pulse_anim.state() == QVariantAnimation.Running:
            self._goal_pulse_anim.stop()
        self._goal_pulse_anim.start()

    def _trigger_attention(self) -> None:
        if sys.platform not in ("win32", "darwin"):
            return
        duration_ms = max(
            200, int(max(0.0, self.settings.goal_pulse_seconds) * 1000)
        )
        if duration_ms == 0:
            duration_ms = 2000
        try:
            QApplication.alert(self, duration_ms)
        except Exception:
            LOGGER.exception("Failed to request OS attention")

    def _on_goal_pulse_value(self, value) -> None:
        try:
            t = float(value)
        except (TypeError, ValueError):
            return
        intensity = math.sin(math.pi * t)
        self.glow_frame.set_intensity(intensity)

    def _on_goal_pulse_finished(self) -> None:
        self.glow_frame.set_intensity(0.0)

    def _update_day_time_label(self) -> None:
        now = QDateTime.currentDateTime()
        start_time = QTime(self.settings.day_start_hour, self.settings.day_start_minute)
        end_time = QTime(self.settings.day_end_hour, self.settings.day_end_minute)
        start_dt = QDateTime(now.date(), start_time)
        end_dt = QDateTime(now.date(), end_time)
        if not end_dt.isValid() or not start_dt.isValid() or end_dt <= start_dt:
            remaining_seconds = 0
        elif now < start_dt or now >= end_dt:
            remaining_seconds = 0
        else:
            remaining_seconds = max(0, int(now.secsTo(end_dt)))
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = remaining_seconds % 60
        self.day_time_label.setText(
            f"Day time left: {hours:02d}:{minutes:02d}:{seconds:02d}"
        )

    def _update_total_today_label(self) -> None:
        date_key = self._date_key(QDate.currentDate())
        total_seconds = self._total_seconds_for_day(date_key)
        self.total_today_label.setText(
            f"Total today: {total_seconds // 3600:02d}:"
            f"{(total_seconds % 3600) // 60:02d}:"
            f"{total_seconds % 60:02d}"
        )
        self._update_goal_left_label()
        self._update_year_total_label()
        self._update_streak_labels()

    def _update_goal_left_label(self) -> None:
        date_key = self._date_key(QDate.currentDate())
        goal_seconds = self._goal_seconds_for_date(date_key)
        if goal_seconds <= 0:
            self.goal_left_label.setText("Super goal left: please set goal")
            self.super_goal_bar.set_progress(0.0)
            return
        total_seconds = self._total_seconds_for_day(date_key)
        remaining = max(0, goal_seconds - total_seconds)
        self.goal_left_label.setText(
            f"Super goal left: {remaining // 3600:02d}:"
            f"{(remaining % 3600) // 60:02d}:"
            f"{remaining % 60:02d}"
        )
        self.super_goal_bar.set_progress(total_seconds / goal_seconds)

    def _super_goal_left_seconds(self) -> int:
        date_key = self._date_key(QDate.currentDate())
        goal_seconds = self._goal_seconds_for_date(date_key)
        if goal_seconds <= 0:
            return 0
        total_seconds = self._total_seconds_for_day(date_key)
        return max(0, goal_seconds - total_seconds)

    def _cycle_year_total_display(self) -> None:
        try:
            index = YEAR_TOTAL_DISPLAY_MODES.index(self.settings.year_total_display)
        except ValueError:
            index = 0
        next_index = (index + 1) % len(YEAR_TOTAL_DISPLAY_MODES)
        self.settings.year_total_display = YEAR_TOTAL_DISPLAY_MODES[next_index]
        self._update_year_total_label()
        QTimer.singleShot(0, self._animate_year_total_label)
        self._save_settings()

    def _year_total_tooltip(self, display: str) -> str:
        if display == "hours":
            return "Click to show days"
        if display == "days":
            return "Click to show week total"
        if display == "week":
            return "Click to show avg/week"
        return "Click to show total hours"

    def _week_range_for_date(self, date: QDate) -> tuple[QDate, QDate]:
        end_day = max(1, min(7, int(self.settings.week_end_day)))
        delta = (date.dayOfWeek() - end_day) % 7
        end = date.addDays(-delta)
        start = end.addDays(-6)
        return start, end

    def _animate_year_total_label(self) -> None:
        if self.year_total_label is None:
            return
        if self._year_total_anim is None:
            self._year_total_anim = QPropertyAnimation(
                self.year_total_label, b"pos", self
            )
            self._year_total_anim.setDuration(240)
            self._year_total_anim.setEasingCurve(QEasingCurve.OutBounce)
        else:
            self._year_total_anim.stop()
        base_pos = self.year_total_label.pos()
        start_pos = QPoint(base_pos.x(), base_pos.y() - 10)
        self._year_total_anim.setStartValue(start_pos)
        self._year_total_anim.setEndValue(base_pos)
        self._year_total_anim.start()

    def _update_year_total_label(self) -> None:
        current_year = QDate.currentDate().year()
        year_prefix = f"{current_year}-"
        total_seconds = sum(
            seconds
            for date_key, seconds in self.daily_totals.items()
            if date_key.startswith(year_prefix)
        )
        if (
            self._active_session_date_key
            and self._active_session_date_key.startswith(year_prefix)
        ):
            total_seconds += self._active_session_seconds
        display = self.settings.year_total_display
        if display not in YEAR_TOTAL_DISPLAY_MODES:
            display = "hours"
            self.settings.year_total_display = display
        if display == "days":
            days = total_seconds // 86400
            remainder = total_seconds % 86400
            hours = remainder // 3600
            minutes = (remainder % 3600) // 60
            seconds = remainder % 60
            text = f"Year total: {days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
        elif display == "week":
            today = QDate.currentDate()
            start_of_week, end_of_week = self._week_range_for_date(today)
            week_seconds = 0
            date = start_of_week
            while date <= end_of_week:
                week_seconds += self._total_seconds_for_day(self._date_key(date))
                date = date.addDays(1)
            hours = week_seconds // 3600
            minutes = (week_seconds % 3600) // 60
            seconds = week_seconds % 60
            text = f"Week total: {hours}:{minutes:02d}:{seconds:02d}"
        elif display == "avg_week":
            start_of_year = QDate(current_year, 1, 1)
            days_elapsed = start_of_year.daysTo(QDate.currentDate()) + 1
            days_elapsed = max(1, days_elapsed)
            avg_week_seconds = int(round(total_seconds * 7 / days_elapsed))
            hours = avg_week_seconds // 3600
            minutes = (avg_week_seconds % 3600) // 60
            seconds = avg_week_seconds % 60
            text = f"Year avg/week: {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            text = f"Year total: {hours}:{minutes:02d}:{seconds:02d}"
        self.year_total_label.setText(text)
        self.year_total_label.setToolTip(self._year_total_tooltip(display))

    def _update_streak_labels(self) -> None:
        longest, current = self._calculate_streaks()
        longest_label = "day" if longest == 1 else "days"
        current_label = "day" if current == 1 else "days"
        self.longest_streak_label.setText(
            f"Longest streak: {longest} {longest_label}"
        )
        self.current_streak_label.setText(
            f"Current streak: {current} {current_label}"
        )

    def _toggle_always_on_top(self, enabled: bool, save: bool = True) -> None:
        try:
            LOGGER.debug("Always on top toggled: %s", enabled)
            self._always_on_top = enabled
            self.settings.always_on_top = enabled
            flags = self.windowFlags()
            if enabled:
                flags |= Qt.WindowStaysOnTopHint
            else:
                flags &= ~Qt.WindowStaysOnTopHint
            flags = self._normalized_window_flags(flags)
            self.setWindowFlags(flags)
            if save:
                self._save_settings()
            QTimer.singleShot(0, lambda: self._restore_after_toggle(enabled))
        except Exception:
            LOGGER.exception("Failed to toggle always on top")

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if (
            event.type() == QEvent.WindowStateChange
            and self._always_on_top
            and self.isMinimized()
        ):
            LOGGER.debug("Window minimized while always on top; restoring.")
            self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
            self.showNormal()
            self.raise_()
            self.activateWindow()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_scaled_metrics()
        self._schedule_window_save()

    def moveEvent(self, event) -> None:
        super().moveEvent(event)
        self._schedule_window_save()

    def closeEvent(self, event) -> None:
        self._save_window_geometry()
        super().closeEvent(event)

    def eventFilter(self, obj, event) -> bool:
        if (
            event.type() == QEvent.Wheel
            and self._is_heatmap_wheel_target(obj)
        ):
            if self._handle_heatmap_wheel(event):
                return True
        return super().eventFilter(obj, event)

    def _is_heatmap_wheel_target(self, obj) -> bool:
        if obj is self.heatmap_widget:
            return True
        if obj is self.heatmap_grid_widget:
            return True
        if obj is self.month_labels_widget:
            return True
        if isinstance(obj, QWidget) and obj.objectName() == "heatmapCell":
            return True
        return False

    def _handle_heatmap_wheel(self, event) -> bool:
        delta = event.angleDelta().y()
        if delta == 0:
            return False
        step = 1 if delta > 0 else -1
        self._set_base_heatmap_cell_size(
            self._heatmap_base_size + step, save=True
        )
        return True

    def _restore_after_toggle(self, enabled: bool) -> None:
        if self.isMinimized():
            self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
        self.showNormal()
        self.show()
        if enabled:
            self.raise_()
            self.activateWindow()

    def _add_visibility_action(
        self, menu: QMenu, label: str, setting_key: str
    ) -> QAction:
        action = QAction(label, self)
        action.setCheckable(True)
        action.setChecked(getattr(self.settings, setting_key))
        action.toggled.connect(
            lambda checked, key=setting_key: self._toggle_ui_setting(key, checked)
        )
        menu.addAction(action)
        return action

    def _toggle_ui_setting(self, setting_key: str, enabled: bool) -> None:
        setattr(self.settings, setting_key, enabled)
        self._apply_visibility_settings()
        self._save_settings()

    def _reset_ui_visibility(self) -> None:
        self.settings.show_heatmap = True
        self.settings.show_day_time = True
        self.settings.show_total_today = True
        self.settings.show_year_total = True
        self.settings.show_super_goal_left = True
        self.settings.show_status_label = True
        self.settings.show_start_button = True
        self.settings.show_clock_button = True
        self.settings.show_longest_streak = True
        self.settings.show_current_streak = True
        self._apply_visibility_settings()
        self._save_settings()

    def _apply_window_flag_defaults(self) -> None:
        flags = self._normalized_window_flags(self.windowFlags())
        if flags != self.windowFlags():
            self.setWindowFlags(flags)

    def _normalized_window_flags(self, flags: Qt.WindowFlags) -> Qt.WindowFlags:
        if sys.platform != "win32":
            return flags
        required = (
            Qt.WindowTitleHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowMinMaxButtonsHint
            | Qt.WindowCloseButtonHint
        )
        return flags | required

    def _seconds_to_hm(self, total_seconds: int) -> tuple[int, int]:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return hours, minutes

    def _date_key(self, date: QDate) -> str:
        return date.toString("yyyy-MM-dd")

    def _goal_seconds_for_date(self, date_key: str) -> int:
        if date_key in self.daily_goals:
            return self.daily_goals[date_key]
        if date_key == self._date_key(QDate.currentDate()):
            return self.super_goal_seconds
        return 0

    def _set_daily_goal(self, date: QDate, goal_seconds: int, record: bool) -> None:
        date_key = self._date_key(date)
        if self.daily_goals.get(date_key) == goal_seconds:
            return
        self.daily_goals[date_key] = goal_seconds
        if record:
            self._append_goal_update(date_key, goal_seconds)

    def _begin_session(self) -> None:
        self._active_session_start = QDateTime.currentDateTime()
        self._active_session_seconds = 0
        self._active_session_date_key = self._date_key(
            self._active_session_start.date()
        )

    def _finalize_session(self) -> None:
        if self._active_session_start is None:
            return
        if self._active_session_seconds <= 0:
            self._active_session_start = None
            self._active_session_seconds = 0
            self._active_session_date_key = None
            return
        if not self._active_session_date_key:
            self._active_session_start = None
            self._active_session_seconds = 0
            self._active_session_date_key = None
            return
        date_key = self._active_session_date_key
        start_time = self._active_session_start.time().toString("HH:mm:ss")
        end_time = QDateTime.currentDateTime().time().toString("HH:mm:ss")
        duration = self._active_session_seconds
        goal_seconds = self.super_goal_seconds
        self.daily_goals[date_key] = goal_seconds
        self._append_log_entry(
            date_key, start_time, end_time, duration, goal_seconds
        )
        self.log_entries.append(
            {
                "date": date_key,
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": duration,
                "goal_seconds": goal_seconds,
            }
        )
        self.daily_totals[date_key] = self.daily_totals.get(date_key, 0) + duration
        self._active_session_start = None
        self._active_session_seconds = 0
        self._active_session_date_key = None
        self._update_heatmap_cell(date_key)
        self._update_total_today_label()

    def _total_seconds_for_day(self, date_key: str) -> int:
        total = self.daily_totals.get(date_key, 0)
        if self._active_session_date_key == date_key:
            total += self._active_session_seconds
        return total

    def _clock_display_seconds(self) -> int:
        today_key = self._date_key(QDate.currentDate())
        total_seconds = self._total_seconds_for_day(today_key)
        return max(0, total_seconds - self._clock_offset_seconds)

    def _goal_met_on_date(self, date_key: str) -> bool:
        goal_seconds = self.daily_goals.get(date_key, 0)
        if goal_seconds <= 0:
            return False
        return self._total_seconds_for_day(date_key) >= goal_seconds

    def _calculate_streaks(self) -> tuple[int, int]:
        goal_dates: list[QDate] = []
        for date_key, goal_seconds in self.daily_goals.items():
            if goal_seconds <= 0:
                continue
            date = QDate.fromString(date_key, "yyyy-MM-dd")
            if date.isValid():
                goal_dates.append(date)
        goal_dates.sort(key=lambda date: date.toJulianDay())

        longest = 0
        running = 0
        prev_date = None
        for date in goal_dates:
            met = self._goal_met_on_date(self._date_key(date))
            if met:
                if prev_date is not None and prev_date.addDays(1) == date:
                    running += 1
                else:
                    running = 1
                longest = max(longest, running)
            else:
                running = 0
            prev_date = date

        today = QDate.currentDate()
        latest_met = None
        for date in reversed(goal_dates):
            if self._goal_met_on_date(self._date_key(date)):
                latest_met = date
                break

        if latest_met is None:
            return longest, 0
        if latest_met < today.addDays(-1):
            return longest, 0

        current_streak = 0
        date = latest_met
        while self._goal_met_on_date(self._date_key(date)):
            current_streak += 1
            date = date.addDays(-1)

        return longest, current_streak

    def _record_super_goal_progress(self, seconds: int) -> None:
        if seconds <= 0:
            return
        if self._active_session_start is None:
            self._begin_session()
        current_date = QDate.currentDate()
        current_key = self._date_key(current_date)
        if self._active_session_date_key != current_key:
            self._finalize_session()
            self._begin_session()
            self._clock_offset_seconds = 0
        if current_date.year() != self._heatmap_year:
            self._refresh_heatmap()
        self._active_session_seconds += seconds
        self._update_heatmap_cell(current_key)
        self._update_total_today_label()

    def _load_settings(self) -> UiSettings:
        settings = get_settings()
        ui = UiSettings()
        ui.blur_radius = int(settings.value("blur/radius", ui.blur_radius))
        ui.opacity = float(settings.value("blur/opacity", ui.opacity))
        ui.bg_color = hex_to_qcolor(
            settings.value("colors/background", qcolor_to_hex(ui.bg_color)), ui.bg_color
        )
        ui.text_color = hex_to_qcolor(
            settings.value("colors/text", qcolor_to_hex(ui.text_color)), ui.text_color
        )
        ui.accent_color = hex_to_qcolor(
            settings.value("colors/accent", qcolor_to_hex(ui.accent_color)),
            ui.accent_color,
        )
        ui.day_time_color = hex_to_qcolor(
            settings.value("colors/day_time", qcolor_to_hex(ui.day_time_color)),
            ui.day_time_color,
        )
        ui.heatmap_color = hex_to_qcolor(
            settings.value("colors/heatmap", qcolor_to_hex(ui.heatmap_color)),
            ui.heatmap_color,
        )
        ui.heatmap_hover_bg_color = hex_to_qcolor(
            settings.value(
                "colors/heatmap_hover_bg", qcolor_to_hex(ui.heatmap_hover_bg_color)
            ),
            ui.heatmap_hover_bg_color,
        )
        ui.heatmap_hover_text_color = hex_to_qcolor(
            settings.value(
                "colors/heatmap_hover_text", qcolor_to_hex(ui.heatmap_hover_text_color)
            ),
            ui.heatmap_hover_text_color,
        )
        ui.heatmap_hover_cell_color = hex_to_qcolor(
            settings.value(
                "colors/heatmap_hover_cell",
                qcolor_to_hex(ui.heatmap_hover_cell_color),
            ),
            ui.heatmap_hover_cell_color,
        )
        ui.graph_line_color = hex_to_qcolor(
            settings.value(
                "colors/graph_line", qcolor_to_hex(ui.graph_line_color)
            ),
            ui.graph_line_color,
        )
        ui.graph_dot_color = hex_to_qcolor(
            settings.value("colors/graph_dot", qcolor_to_hex(ui.graph_dot_color)),
            ui.graph_dot_color,
        )
        ui.graph_fill_color = hex_to_qcolor(
            settings.value(
                "colors/graph_fill", qcolor_to_hex(ui.graph_fill_color)
            ),
            ui.graph_fill_color,
        )
        ui.graph_grid_color = hex_to_qcolor(
            settings.value(
                "colors/graph_grid", qcolor_to_hex(ui.graph_grid_color)
            ),
            ui.graph_grid_color,
        )
        ui.heatmap_cell_size = int(
            settings.value("heatmap/cell_size", ui.heatmap_cell_size)
        )
        ui.heatmap_cell_size = max(
            HEATMAP_CELL_SIZE_MIN,
            min(HEATMAP_CELL_SIZE_MAX, ui.heatmap_cell_size),
        )
        ui.heatmap_month_padding = int(
            settings.value("heatmap/month_padding", ui.heatmap_month_padding)
        )
        ui.heatmap_month_padding = max(0, ui.heatmap_month_padding)
        ui.heatmap_month_label_size = int(
            settings.value(
                "heatmap/month_label_size", ui.heatmap_month_label_size
            )
        )
        ui.heatmap_month_label_size = max(6, ui.heatmap_month_label_size)
        ui.total_today_color = hex_to_qcolor(
            settings.value("colors/total_today", qcolor_to_hex(ui.total_today_color)),
            ui.total_today_color,
        )
        ui.goal_left_color = hex_to_qcolor(
            settings.value("colors/goal_left", qcolor_to_hex(ui.goal_left_color)),
            ui.goal_left_color,
        )
        ui.super_goal_bar_start = hex_to_qcolor(
            settings.value(
                "colors/super_goal_bar_start",
                qcolor_to_hex(ui.super_goal_bar_start),
            ),
            ui.super_goal_bar_start,
        )
        ui.super_goal_bar_end = hex_to_qcolor(
            settings.value(
                "colors/super_goal_bar_end",
                qcolor_to_hex(ui.super_goal_bar_end),
            ),
            ui.super_goal_bar_end,
        )
        ui.super_goal_bar_bg = hex_to_qcolor(
            settings.value(
                "colors/super_goal_bar_bg",
                qcolor_to_hex(ui.super_goal_bar_bg),
            ),
            ui.super_goal_bar_bg,
        )
        ui.font_size = int(settings.value("fonts/timer", ui.font_size))
        ui.label_size = int(settings.value("fonts/label", ui.label_size))
        ui.day_time_font_size = int(
            settings.value("fonts/day_time", ui.day_time_font_size)
        )
        ui.total_today_font_size = int(
            settings.value("fonts/total_today", ui.total_today_font_size)
        )
        ui.goal_left_font_size = int(
            settings.value("fonts/goal_left", ui.goal_left_font_size)
        )
        ui.super_goal_bar_width = int(
            settings.value("super_goal_bar/width", ui.super_goal_bar_width)
        )
        ui.super_goal_bar_height = int(
            settings.value("super_goal_bar/height", ui.super_goal_bar_height)
        )
        ui.super_goal_bar_width = max(40, ui.super_goal_bar_width)
        ui.super_goal_bar_height = max(4, ui.super_goal_bar_height)
        ui.goal_pulse_seconds = float(
            settings.value("goal_pulse/seconds", ui.goal_pulse_seconds)
        )
        ui.always_on_top = parse_bool(
            settings.value("window/always_on_top", ui.always_on_top),
            ui.always_on_top,
        )
        ui.day_start_hour = int(
            settings.value("day_time/start_hour", ui.day_start_hour)
        )
        ui.day_start_minute = int(
            settings.value("day_time/start_minute", ui.day_start_minute)
        )
        ui.day_end_hour = int(settings.value("day_time/end_hour", ui.day_end_hour))
        ui.day_end_minute = int(
            settings.value("day_time/end_minute", ui.day_end_minute)
        )
        try:
            week_start_day = int(
                settings.value("totals/week_start_day", ui.week_start_day)
            )
        except (TypeError, ValueError):
            week_start_day = ui.week_start_day
        try:
            week_end_day = int(
                settings.value("totals/week_end_day", ui.week_end_day)
            )
        except (TypeError, ValueError):
            week_end_day = ui.week_end_day
        ui.week_start_day = max(1, min(7, week_start_day))
        ui.week_end_day = max(1, min(7, week_end_day))
        expected_end = 7 if ui.week_start_day == 1 else ui.week_start_day - 1
        if ui.week_end_day != expected_end:
            ui.week_end_day = expected_end
        year_total_display = settings.value(
            "totals/year_display", ui.year_total_display
        )
        if isinstance(year_total_display, str):
            year_total_display = year_total_display.strip().lower()
        if year_total_display not in YEAR_TOTAL_DISPLAY_MODES:
            year_total_display = ui.year_total_display
        ui.year_total_display = year_total_display
        ui.show_heatmap = parse_bool(
            settings.value("ui/show_heatmap", ui.show_heatmap), ui.show_heatmap
        )
        ui.show_day_time = parse_bool(
            settings.value("ui/show_day_time", ui.show_day_time), ui.show_day_time
        )
        ui.show_total_today = parse_bool(
            settings.value("ui/show_total_today", ui.show_total_today),
            ui.show_total_today,
        )
        ui.show_year_total = parse_bool(
            settings.value("ui/show_year_total", ui.show_year_total),
            ui.show_year_total,
        )
        ui.show_super_goal_left = parse_bool(
            settings.value("ui/show_super_goal_left", ui.show_super_goal_left),
            ui.show_super_goal_left,
        )
        ui.show_status_label = parse_bool(
            settings.value("ui/show_status_label", ui.show_status_label),
            ui.show_status_label,
        )
        ui.show_start_button = parse_bool(
            settings.value("ui/show_start_button", ui.show_start_button),
            ui.show_start_button,
        )
        ui.show_clock_button = parse_bool(
            settings.value("ui/show_clock_button", ui.show_clock_button),
            ui.show_clock_button,
        )
        ui.show_longest_streak = parse_bool(
            settings.value("ui/show_longest_streak", ui.show_longest_streak),
            ui.show_longest_streak,
        )
        ui.show_current_streak = parse_bool(
            settings.value("ui/show_current_streak", ui.show_current_streak),
            ui.show_current_streak,
        )
        ui.use_24h_time = parse_bool(
            settings.value("ui/use_24h_time", ui.use_24h_time),
            ui.use_24h_time,
        )
        return ui

    def _load_hotkey_settings(self) -> HotkeySettings:
        settings = get_settings()
        hotkeys = HotkeySettings()
        hotkeys.start_hotkey = str(
            settings.value("hotkeys/start", hotkeys.start_hotkey) or ""
        )
        hotkeys.clock_hotkey = str(
            settings.value("hotkeys/clock", hotkeys.clock_hotkey) or ""
        )
        hotkeys.start_xinput_button = str(
            settings.value("xinput/start_button", hotkeys.start_xinput_button)
            or ""
        )
        hotkeys.clock_xinput_button = str(
            settings.value("xinput/clock_button", hotkeys.clock_xinput_button)
            or ""
        )
        return hotkeys

    def _legacy_super_goal_seconds(
        self, settings: Optional[QSettings] = None
    ) -> int:
        if settings is None:
            settings = get_settings()
        hours = self._read_int_setting(settings, "super_goal/hours", 2) or 0
        minutes = self._read_int_setting(settings, "super_goal/minutes", 0) or 0
        return max(0, hours * 3600 + minutes * 60)

    def _profile_super_goal_key(self, label: str) -> str:
        clean = label.strip().lower()
        if not clean:
            return "default"
        for sep in ("/", "\\", ":"):
            clean = clean.replace(sep, "_")
        return clean

    def _profile_super_goal_settings_base(self, label: str) -> str:
        return f"super_goal/profiles/{self._profile_super_goal_key(label)}"

    def _load_profile_super_goal_seconds(self, label: str) -> int:
        settings = get_settings()
        base = self._profile_super_goal_settings_base(label)
        hours_key = f"{base}/hours"
        minutes_key = f"{base}/minutes"
        if settings.contains(hours_key) or settings.contains(minutes_key):
            hours = self._read_int_setting(settings, hours_key, 0) or 0
            minutes = self._read_int_setting(settings, minutes_key, 0) or 0
            return max(0, hours * 3600 + minutes * 60)
        legacy = self._legacy_super_goal_seconds(settings)
        self._save_profile_super_goal_seconds(
            label, legacy, settings=settings, sync=False
        )
        settings.sync()
        return legacy

    def _save_profile_super_goal_seconds(
        self,
        label: str,
        seconds: int,
        *,
        settings: Optional[QSettings] = None,
        sync: bool = True,
    ) -> None:
        if settings is None:
            settings = get_settings()
        total = max(0, int(seconds))
        base = self._profile_super_goal_settings_base(label)
        settings.setValue(f"{base}/hours", total // 3600)
        settings.setValue(f"{base}/minutes", (total % 3600) // 60)
        if sync:
            settings.sync()

    def _clear_profile_super_goal(self, label: str) -> None:
        settings = get_settings()
        settings.remove(self._profile_super_goal_settings_base(label))
        settings.sync()

    def _ensure_data_file_path(self, path: str) -> None:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            with open(path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    ["date", "start_time", "end_time", "duration_seconds", "goal_seconds"]
                )

    def _ensure_data_file(self) -> None:
        self._ensure_data_file_path(self._data_file_path)

    def _migrate_profile_logs(self) -> None:
        for label in self._profile_labels():
            fallback_goal = self._load_profile_super_goal_seconds(label)
            self._load_log_entries_from_path(
                self._profile_file_path(label),
                fallback_goal_seconds=fallback_goal,
            )

    def _load_log_entries(
        self,
    ) -> tuple[list[dict[str, object]], dict[str, int], dict[str, int]]:
        return self._load_log_entries_from_path(self._data_file_path)

    def _load_log_entries_from_path(
        self, path: str, *, fallback_goal_seconds: Optional[int] = None
    ) -> tuple[list[dict[str, object]], dict[str, int], dict[str, int]]:
        self._ensure_data_file_path(path)
        entries: list[dict[str, object]] = []
        totals: dict[str, int] = {}
        daily_goals: dict[str, int] = {}
        with open(path, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                return entries, totals, daily_goals
            has_start_time = "start_time" in reader.fieldnames
            has_end_time = "end_time" in reader.fieldnames
            has_goal_seconds = "goal_seconds" in reader.fieldnames
            needs_migration = (
                "time" in reader.fieldnames
                or not has_start_time
                or not has_end_time
                or not has_goal_seconds
            )
            if fallback_goal_seconds is None:
                fallback_goal_seconds = self.super_goal_seconds
            fallback_goal = fallback_goal_seconds if fallback_goal_seconds > 0 else 0
            for row in reader:
                date_key = row.get("date")
                duration_str = row.get("duration_seconds")
                if not date_key or duration_str is None:
                    continue
                goal_value = row.get("goal_seconds") if has_goal_seconds else None
                try:
                    goal_seconds = int(goal_value) if goal_value else fallback_goal
                except (TypeError, ValueError):
                    goal_seconds = fallback_goal
                daily_goals[date_key] = goal_seconds
                try:
                    duration = int(duration_str)
                except (TypeError, ValueError):
                    continue
                start_time = (
                    row.get("start_time")
                    if has_start_time
                    else row.get("time")
                )
                end_time = row.get("end_time") if has_end_time else None
                if not start_time:
                    start_time = "N/A"
                if not end_time and start_time not in ("N/A", ""):
                    end_time = self._compute_end_time(start_time, duration)
                if not end_time:
                    end_time = "N/A"
                if duration <= 0:
                    continue
                entries.append(
                    {
                        "date": date_key,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_seconds": duration,
                        "goal_seconds": goal_seconds,
                    }
                )
                totals[date_key] = totals.get(date_key, 0) + duration
        if needs_migration:
            self._rewrite_log_file(entries, daily_goals, path=path)
        return entries, totals, daily_goals

    def _profile_color_key(self, label: str) -> str:
        return f"profiles/colors/{label.strip().lower()}"

    def _palette_profile_color(self, label: str) -> QColor:
        if not PROFILE_COLOR_PALETTE:
            return QColor("#6dd3fb")
        seed = sum(ord(ch) for ch in label.strip().lower())
        return QColor(PROFILE_COLOR_PALETTE[seed % len(PROFILE_COLOR_PALETTE)])

    def _profile_fallback_color(self, label: str) -> QColor:
        if label == self._active_profile:
            return QColor(self.settings.graph_line_color)
        return self._palette_profile_color(label)

    def _profile_color(self, label: str) -> QColor:
        color = self._profile_colors.get(label)
        if isinstance(color, QColor) and color.isValid():
            return QColor(color)
        return self._profile_fallback_color(label)

    def _profile_dot_color(self, label: str) -> QColor:
        color = self._profile_colors.get(label)
        if isinstance(color, QColor) and color.isValid():
            return QColor(color)
        if label == self._active_profile:
            return QColor(self.settings.graph_dot_color)
        return self._palette_profile_color(label)

    def _profile_fill_color(self, label: str) -> QColor:
        color = self._profile_colors.get(label)
        if isinstance(color, QColor) and color.isValid():
            return QColor(color)
        if label == self._active_profile:
            return QColor(self.settings.graph_fill_color)
        return self._palette_profile_color(label)

    def _load_profile_colors(self) -> dict[str, QColor]:
        settings = get_settings()
        colors: dict[str, QColor] = {}
        for label in self._profile_labels():
            key = self._profile_color_key(label)
            value = settings.value(key, "")
            if isinstance(value, str) and value:
                color = QColor(value)
                if color.isValid():
                    colors[label] = color
        return colors

    def _set_profile_color(self, label: str, color: QColor) -> None:
        if not color.isValid():
            return
        self._profile_colors[label] = color
        settings = get_settings()
        settings.setValue(self._profile_color_key(label), qcolor_to_hex(color))
        settings.sync()

    def _clear_profile_color(self, label: str) -> None:
        self._profile_colors.pop(label, None)
        settings = get_settings()
        settings.remove(self._profile_color_key(label))
        settings.sync()

    def _compute_end_time(self, start_time: str, duration: int) -> str:
        time = QTime.fromString(start_time, "HH:mm:ss")
        if not time.isValid():
            time = QTime.fromString(start_time, "HH:mm")
        if not time.isValid():
            return "N/A"
        return time.addSecs(duration).toString("HH:mm:ss")

    def _append_log_entry(
        self,
        date_key: str,
        start_time: str,
        end_time: str,
        duration: int,
        goal_seconds: int,
    ) -> None:
        self._ensure_data_file()
        with open(self._data_file_path, "a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow([date_key, start_time, end_time, duration, goal_seconds])

    def _append_goal_update(self, date_key: str, goal_seconds: int) -> None:
        self._append_log_entry(date_key, "goal", "goal", 0, goal_seconds)

    def _rewrite_log_file(
        self,
        entries: list[dict[str, object]],
        daily_goals: dict[str, int],
        *,
        path: Optional[str] = None,
    ) -> None:
        target_path = path or self._data_file_path
        with open(target_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["date", "start_time", "end_time", "duration_seconds", "goal_seconds"]
            )
            for entry in entries:
                date_key = entry["date"]
                goal_seconds = entry.get("goal_seconds")
                if goal_seconds is None:
                    goal_seconds = daily_goals.get(date_key, 0)
                writer.writerow(
                    [
                        date_key,
                        entry.get("start_time", "N/A"),
                        entry.get("end_time", "N/A"),
                        entry["duration_seconds"],
                        goal_seconds,
                    ]
                )

    def _read_int_setting(
        self,
        settings: QSettings,
        key: str,
        fallback: Optional[int],
    ) -> Optional[int]:
        value = settings.value(key, fallback)
        if value is None:
            return fallback
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    def _load_custom_profiles(self) -> list[str]:
        settings = get_settings()
        value = settings.value("profiles/custom", [])
        if isinstance(value, str):
            raw = [item.strip() for item in value.split("|")]
        elif isinstance(value, (list, tuple)):
            raw = [str(item).strip() for item in value]
        else:
            raw = []
        labels: list[str] = []
        seen = set()
        for label in raw:
            if not label:
                continue
            if self._is_profile_label_reserved(label):
                continue
            key = label.strip().lower()
            if key in seen:
                continue
            if label in self._default_profile_files:
                continue
            seen.add(key)
            labels.append(label)
        return labels

    def _load_active_profile(self) -> str:
        settings = get_settings()
        active = settings.value("profiles/active", DEFAULT_PROFILE_NAME)
        if not isinstance(active, str):
            active = DEFAULT_PROFILE_NAME
        active = active.strip() or DEFAULT_PROFILE_NAME
        if active not in self._profile_labels():
            active = DEFAULT_PROFILE_NAME
        return active

    def _save_profile_settings(self) -> None:
        settings = get_settings()
        settings.setValue("profiles/active", self._active_profile)
        settings.setValue("profiles/custom", self._custom_profiles)
        settings.sync()

    def _profile_labels(self) -> list[str]:
        return list(self._default_profile_files.keys()) + list(self._custom_profiles)

    def _profile_filename(self, label: str) -> str:
        if label in self._default_profile_files:
            return self._default_profile_files[label]
        clean = label.strip()
        if clean.lower().endswith(".csv"):
            clean = clean[:-4]
        return f"{clean}.csv"

    def _profile_file_path(self, label: str) -> str:
        return os.path.join(self._data_dir, self._profile_filename(label))

    def _is_profile_label_reserved(self, label: str) -> bool:
        return label.strip().lower() in ("add profile", "delete profile")

    def _profile_exists(self, label: str) -> bool:
        return any(
            existing.lower() == label.strip().lower()
            for existing in self._profile_labels()
        )

    def _populate_profile_combo(self) -> None:
        if not hasattr(self, "profile_combo"):
            return
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        for label in self._profile_labels():
            self.profile_combo.addItem(label, label)
        self.profile_combo.insertSeparator(self.profile_combo.count())
        self.profile_combo.addItem("Add profile", PROFILE_ACTION_ADD)
        self.profile_combo.addItem("Delete profile", PROFILE_ACTION_DELETE)
        self._restore_profile_selection()
        self.profile_combo.blockSignals(False)

    def _restore_profile_selection(self) -> None:
        if not hasattr(self, "profile_combo"):
            return
        for index in range(self.profile_combo.count()):
            if self.profile_combo.itemData(index) == self._active_profile:
                self.profile_combo.setCurrentIndex(index)
                return

    def _profile_change_locked(self) -> bool:
        return self.timer_active or self.clock_active

    def _deny_profile_change(self) -> None:
        if self.clock_active:
            message = "Turn off the clock to change profile"
        else:
            message = "Pause the timer to change profile"
        self.status_label.setText(message)
        if hasattr(self, "profile_combo"):
            self.profile_combo.blockSignals(True)
            self._restore_profile_selection()
            self.profile_combo.blockSignals(False)

    def _on_profile_changed(self, index: int) -> None:
        if index < 0:
            return
        if self._profile_change_locked():
            self._deny_profile_change()
            return
        data = self.profile_combo.itemData(index)
        if data == PROFILE_ACTION_ADD:
            self._prompt_add_profile()
            return
        if data == PROFILE_ACTION_DELETE:
            self._prompt_delete_profile()
            return
        if isinstance(data, str) and data:
            if data == self._active_profile:
                return
            self._switch_profile(data)

    def _prompt_add_profile(self) -> None:
        name, ok = QInputDialog.getText(
            self, "Add Profile", "Profile name"
        )
        if not ok:
            self._restore_profile_selection()
            return
        label = name.strip()
        if label.lower().endswith(".csv"):
            label = label[:-4].strip()
        if not label:
            self.status_label.setText("Profile name cannot be empty")
            self._restore_profile_selection()
            return
        if any(sep in label for sep in ("/", "\\", ":")):
            self.status_label.setText("Profile name cannot include path separators")
            self._restore_profile_selection()
            return
        if self._is_profile_label_reserved(label) or self._profile_exists(label):
            self.status_label.setText("Profile already exists")
            self._restore_profile_selection()
            return
        self._custom_profiles.append(label)
        self._save_profile_super_goal_seconds(label, self.super_goal_seconds)
        self._active_profile = label
        self._data_file_path = self._profile_file_path(label)
        self._save_profile_settings()
        self._populate_profile_combo()
        self._switch_profile(label)

    def _prompt_delete_profile(self) -> None:
        options = list(self._custom_profiles)
        if not options:
            self.status_label.setText("No custom profiles to delete")
            self._restore_profile_selection()
            return
        selected, ok = QInputDialog.getItem(
            self, "Delete Profile", "Select profile", options, 0, False
        )
        if not ok or not selected:
            self._restore_profile_selection()
            return
        label = str(selected)
        was_active = label == self._active_profile
        if label in self._custom_profiles:
            self._custom_profiles.remove(label)
        path = self._profile_file_path(label)
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                LOGGER.exception("Failed to delete profile file")
        self._clear_profile_color(label)
        self._clear_profile_super_goal(label)
        if was_active:
            self._active_profile = DEFAULT_PROFILE_NAME
        self._save_profile_settings()
        self._populate_profile_combo()
        if was_active:
            self._switch_profile(self._active_profile)
        else:
            self._restore_profile_selection()

    def _switch_profile(self, label: str) -> None:
        if self.timer_active:
            self._stop_countdown("Paused")
        if self.clock_active:
            self._stop_clock("Clock off")
        self._active_profile = label
        self.super_goal_seconds = self._load_profile_super_goal_seconds(label)
        self._data_file_path = self._profile_file_path(label)
        self._last_added_time_entry = None
        self._last_added_time_index = None
        self._active_session_start = None
        self._active_session_seconds = 0
        self._active_session_date_key = None
        self._clock_offset_seconds = 0
        (
            self.log_entries,
            self.daily_totals,
            self.daily_goals,
        ) = self._load_log_entries()
        self._refresh_heatmap()
        self._update_total_today_label()
        self._update_timer_label()
        self.status_label.setText(f"Profile: {label}")
        self._save_profile_settings()

    def _restore_window_geometry(self) -> None:
        settings = get_settings()
        self.setMinimumSize(self._visibility_minimum_size())
        width = self._read_int_setting(settings, "window/width", None)
        height = self._read_int_setting(settings, "window/height", None)
        if width is not None and height is not None:
            width = max(width, self.minimumWidth())
            height = max(height, self.minimumHeight())
            self.resize(width, height)
        pos_x = self._read_int_setting(settings, "window/x", None)
        pos_y = self._read_int_setting(settings, "window/y", None)
        if pos_x is not None and pos_y is not None:
            self.move(pos_x, pos_y)

    def _connect_screen_signals(self) -> None:
        app = QApplication.instance()
        if app is None:
            return
        app.screenAdded.connect(self._on_screen_added)
        app.screenRemoved.connect(self._on_screen_removed)
        for screen in app.screens():
            self._attach_screen_signals(screen)

    def _attach_screen_signals(self, screen) -> None:
        if screen in self._connected_screens:
            return
        self._connected_screens.add(screen)
        screen.availableGeometryChanged.connect(self._ensure_window_visible)
        screen.geometryChanged.connect(self._ensure_window_visible)

    def _on_screen_added(self, screen) -> None:
        self._attach_screen_signals(screen)
        self._ensure_window_visible()

    def _on_screen_removed(self, screen) -> None:
        if screen in self._connected_screens:
            self._connected_screens.remove(screen)
        self._ensure_window_visible()

    def _ensure_window_visible(self) -> None:
        screens = QApplication.screens()
        if not screens:
            return
        window_rect = self.frameGeometry()
        for screen in screens:
            if screen.availableGeometry().intersects(window_rect):
                return
        primary = QApplication.primaryScreen() or screens[0]
        available = primary.availableGeometry()
        width = min(self.width(), available.width())
        height = min(self.height(), available.height())
        width = max(width, self.minimumWidth())
        height = max(height, self.minimumHeight())
        self.resize(width, height)
        x = available.x() + max(0, (available.width() - self.width()) // 2)
        y = available.y() + max(0, (available.height() - self.height()) // 2)
        self.move(x, y)
        self._save_window_geometry()

    def _save_window_geometry(self) -> None:
        settings = get_settings()
        rect = self.geometry()
        settings.setValue("window/x", rect.x())
        settings.setValue("window/y", rect.y())
        settings.setValue("window/width", rect.width())
        settings.setValue("window/height", rect.height())
        settings.sync()

    def _schedule_window_save(self) -> None:
        if self._window_save_timer is None:
            return
        self._window_save_timer.start()

    def _save_settings(self) -> None:
        settings = get_settings()
        settings.setValue("blur/radius", self.settings.blur_radius)
        settings.setValue("blur/opacity", self.settings.opacity)
        settings.setValue("colors/background", qcolor_to_hex(self.settings.bg_color))
        settings.setValue("colors/text", qcolor_to_hex(self.settings.text_color))
        settings.setValue("colors/accent", qcolor_to_hex(self.settings.accent_color))
        settings.setValue("colors/day_time", qcolor_to_hex(self.settings.day_time_color))
        settings.setValue("colors/heatmap", qcolor_to_hex(self.settings.heatmap_color))
        settings.setValue(
            "colors/heatmap_hover_bg",
            qcolor_to_hex(self.settings.heatmap_hover_bg_color),
        )
        settings.setValue(
            "colors/heatmap_hover_text",
            qcolor_to_hex(self.settings.heatmap_hover_text_color),
        )
        settings.setValue(
            "colors/heatmap_hover_cell",
            qcolor_to_hex(self.settings.heatmap_hover_cell_color),
        )
        settings.setValue(
            "colors/graph_line", qcolor_to_hex(self.settings.graph_line_color)
        )
        settings.setValue(
            "colors/graph_dot", qcolor_to_hex(self.settings.graph_dot_color)
        )
        settings.setValue(
            "colors/graph_fill", qcolor_to_hex(self.settings.graph_fill_color)
        )
        settings.setValue(
            "colors/graph_grid", qcolor_to_hex(self.settings.graph_grid_color)
        )
        settings.setValue("heatmap/cell_size", self.settings.heatmap_cell_size)
        settings.setValue(
            "heatmap/month_padding", self.settings.heatmap_month_padding
        )
        settings.setValue(
            "heatmap/month_label_size", self.settings.heatmap_month_label_size
        )
        settings.setValue(
            "colors/total_today",
            qcolor_to_hex(self.settings.total_today_color),
        )
        settings.setValue(
            "colors/goal_left",
            qcolor_to_hex(self.settings.goal_left_color),
        )
        settings.setValue(
            "colors/super_goal_bar_start",
            qcolor_to_hex(self.settings.super_goal_bar_start),
        )
        settings.setValue(
            "colors/super_goal_bar_end",
            qcolor_to_hex(self.settings.super_goal_bar_end),
        )
        settings.setValue(
            "colors/super_goal_bar_bg",
            qcolor_to_hex(self.settings.super_goal_bar_bg),
        )
        settings.setValue("fonts/timer", self.settings.font_size)
        settings.setValue("fonts/label", self.settings.label_size)
        settings.setValue("fonts/day_time", self.settings.day_time_font_size)
        settings.setValue("fonts/total_today", self.settings.total_today_font_size)
        settings.setValue("fonts/goal_left", self.settings.goal_left_font_size)
        settings.setValue("super_goal_bar/width", self.settings.super_goal_bar_width)
        settings.setValue("super_goal_bar/height", self.settings.super_goal_bar_height)
        settings.setValue("goal_pulse/seconds", self.settings.goal_pulse_seconds)
        settings.setValue("window/always_on_top", int(self.settings.always_on_top))
        settings.setValue("day_time/start_hour", self.settings.day_start_hour)
        settings.setValue("day_time/start_minute", self.settings.day_start_minute)
        settings.setValue("day_time/end_hour", self.settings.day_end_hour)
        settings.setValue("day_time/end_minute", self.settings.day_end_minute)
        settings.setValue("totals/year_display", self.settings.year_total_display)
        settings.setValue("totals/week_start_day", self.settings.week_start_day)
        settings.setValue("totals/week_end_day", self.settings.week_end_day)
        settings.setValue("ui/show_heatmap", int(self.settings.show_heatmap))
        settings.setValue("ui/show_day_time", int(self.settings.show_day_time))
        settings.setValue("ui/show_total_today", int(self.settings.show_total_today))
        settings.setValue("ui/show_year_total", int(self.settings.show_year_total))
        settings.setValue(
            "ui/show_super_goal_left", int(self.settings.show_super_goal_left)
        )
        settings.setValue("ui/show_status_label", int(self.settings.show_status_label))
        settings.setValue(
            "ui/show_start_button", int(self.settings.show_start_button)
        )
        settings.setValue(
            "ui/show_clock_button", int(self.settings.show_clock_button)
        )
        settings.setValue(
            "ui/show_longest_streak", int(self.settings.show_longest_streak)
        )
        settings.setValue(
            "ui/show_current_streak", int(self.settings.show_current_streak)
        )
        settings.setValue("ui/use_24h_time", int(self.settings.use_24h_time))
        settings.sync()

    def _save_hotkey_settings(self) -> None:
        settings = get_settings()
        settings.setValue("hotkeys/start", self.hotkey_settings.start_hotkey)
        settings.setValue("hotkeys/clock", self.hotkey_settings.clock_hotkey)
        settings.setValue(
            "xinput/start_button", self.hotkey_settings.start_xinput_button
        )
        settings.setValue(
            "xinput/clock_button", self.hotkey_settings.clock_xinput_button
        )
        settings.sync()

    def _save_super_goal(self) -> None:
        self._save_profile_super_goal_seconds(
            self._active_profile, self.super_goal_seconds
        )

    def _apply_heatmap_geometry(self, size: int, month_padding: int) -> bool:
        clamped = max(HEATMAP_CELL_SIZE_MIN, min(HEATMAP_CELL_SIZE_MAX, int(size)))
        padding = max(0, int(month_padding))
        if (
            clamped == self._heatmap_cell_size
            and padding == self._heatmap_month_padding
        ):
            return False
        self._heatmap_cell_size = clamped
        self._heatmap_month_padding = padding
        self._clear_heatmap()
        self._populate_heatmap_cells(self._heatmap_year)
        self._refresh_heatmap()
        return True

    def _set_base_heatmap_cell_size(self, size: int, save: bool = True) -> bool:
        clamped = max(HEATMAP_CELL_SIZE_MIN, min(HEATMAP_CELL_SIZE_MAX, int(size)))
        if clamped == self._heatmap_base_size:
            if save and self.settings.heatmap_cell_size != clamped:
                self.settings.heatmap_cell_size = clamped
                self._save_settings()
            return self._apply_scaled_heatmap_size()
        self._heatmap_base_size = clamped
        self.settings.heatmap_cell_size = clamped
        resized = self._apply_scaled_heatmap_size()
        if save:
            self._save_settings()
        return resized

    def _build_heatmap(self) -> QWidget:
        self.heatmap_cells: dict[str, QFrame] = {}
        self.heatmap_placeholder_cells: list[QFrame] = []
        self.month_label_widgets: list[QLabel] = []
        self.month_label_spacers: list[QFrame] = []
        self.month_labels_layout = QGridLayout()
        self.month_labels_layout.setContentsMargins(0, 0, 0, 0)
        self.month_labels_layout.setHorizontalSpacing(self._heatmap_spacing)
        self.month_labels_layout.setVerticalSpacing(0)
        self.month_labels_widget = QWidget()
        self.month_labels_widget.setObjectName("heatmapMonthLabels")
        self.month_labels_widget.setLayout(self.month_labels_layout)
        self.month_labels_widget.installEventFilter(self)

        self.heatmap_layout = QGridLayout()
        self.heatmap_layout.setContentsMargins(0, 0, 0, 0)
        self.heatmap_layout.setHorizontalSpacing(self._heatmap_spacing)
        self.heatmap_layout.setVerticalSpacing(self._heatmap_spacing)

        self.heatmap_grid_widget = QWidget()
        self.heatmap_grid_widget.setObjectName("heatmapGrid")
        self.heatmap_grid_widget.setLayout(self.heatmap_layout)
        self.heatmap_grid_widget.installEventFilter(self)

        self.heatmap_widget = QWidget()
        self.heatmap_widget.setObjectName("heatmapWidget")
        self.heatmap_container_layout = QVBoxLayout()
        self.heatmap_container_layout.setContentsMargins(0, 0, 0, 0)
        self.heatmap_container_layout.setSpacing(self._heatmap_label_spacing)
        self.heatmap_container_layout.addWidget(self.month_labels_widget)
        self.heatmap_container_layout.addWidget(self.heatmap_grid_widget)
        self.heatmap_widget.setLayout(self.heatmap_container_layout)
        self.heatmap_widget.installEventFilter(self)
        self._populate_heatmap_cells(self._heatmap_year)
        return self.heatmap_widget

    def _populate_heatmap_cells(self, year: int) -> None:
        for idx in range(self.month_labels_layout.columnCount()):
            self.month_labels_layout.setColumnMinimumWidth(idx, 0)
        for idx in range(self.heatmap_layout.columnCount()):
            self.heatmap_layout.setColumnMinimumWidth(idx, 0)

        month_names = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        label_font = QFont(self._font_family, self._heatmap_month_label_size)
        label_color = qcolor_to_hex(self.settings.day_time_color)
        col = 0
        spacer_count = 0
        column_widths: list[int] = []

        self.heatmap_cells.clear()
        self.heatmap_placeholder_cells.clear()
        for month in range(1, 13):
            first_date = QDate(year, month, 1)
            if not first_date.isValid():
                continue
            days_in_month = first_date.daysInMonth()
            leading_blanks = first_date.dayOfWeek() - 1
            total_cells = leading_blanks + days_in_month
            trailing_blanks = (7 - (total_cells % 7)) % 7
            weeks = (total_cells + trailing_blanks) // 7

            label = QLabel(month_names[month - 1])
            label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            label.setFont(label_font)
            label.setStyleSheet(f"color: {label_color};")
            label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self.month_labels_layout.addWidget(
                label, 0, col, 1, weeks, Qt.AlignHCenter | Qt.AlignVCenter
            )
            self.month_label_widgets.append(label)

            for week in range(weeks):
                column_widths.append(self._heatmap_cell_size)
                label_placeholder = QFrame()
                label_placeholder.setAttribute(
                    Qt.WA_TransparentForMouseEvents, True
                )
                label_placeholder.setFixedSize(
                    self._heatmap_cell_size, 0
                )
                self.month_labels_layout.addWidget(
                    label_placeholder, 1, col + week
                )
                self.month_label_spacers.append(label_placeholder)
                for row in range(7):
                    day_index = week * 7 + row - leading_blanks
                    cell = QFrame()
                    cell.setObjectName("heatmapCell")
                    cell.setFixedSize(
                        self._heatmap_cell_size, self._heatmap_cell_size
                    )
                    cell.installEventFilter(self)
                    self.heatmap_layout.addWidget(cell, row, col + week)
                    if day_index < 0 or day_index >= days_in_month:
                        self._apply_placeholder_style(cell)
                        self.heatmap_placeholder_cells.append(cell)
                    else:
                        date = first_date.addDays(day_index)
                        self.heatmap_cells[self._date_key(date)] = cell
            col += weeks

            if self._heatmap_month_padding > 0 and month < 12:
                spacer = QFrame()
                spacer.setAttribute(Qt.WA_TransparentForMouseEvents, True)
                spacer.setFixedWidth(self._heatmap_month_padding)
                self.heatmap_layout.addWidget(spacer, 0, col, 7, 1)
                self.month_label_spacers.append(spacer)
                spacer_label = QFrame()
                spacer_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
                spacer_label.setFixedWidth(self._heatmap_month_padding)
                self.month_labels_layout.addWidget(spacer_label, 0, col)
                self.month_label_spacers.append(spacer_label)
                spacer_anchor = QFrame()
                spacer_anchor.setAttribute(
                    Qt.WA_TransparentForMouseEvents, True
                )
                spacer_anchor.setFixedSize(self._heatmap_month_padding, 0)
                self.month_labels_layout.addWidget(spacer_anchor, 1, col)
                self.month_label_spacers.append(spacer_anchor)
                column_widths.append(self._heatmap_month_padding)
                spacer_count += 1
                col += 1

        total_columns = len(column_widths)
        for idx, width in enumerate(column_widths):
            self.month_labels_layout.setColumnMinimumWidth(idx, width)
            self.heatmap_layout.setColumnMinimumWidth(idx, width)

        cell_columns = total_columns - spacer_count
        width = (
            cell_columns * self._heatmap_cell_size
            + spacer_count * self._heatmap_month_padding
            + (total_columns - 1) * self._heatmap_spacing
        )
        height = 7 * self._heatmap_cell_size + 6 * self._heatmap_spacing
        total_height = height + self._heatmap_label_height
        if self._heatmap_label_spacing > 0:
            total_height += self._heatmap_label_spacing
        if self.heatmap_grid_widget is not None:
            self.heatmap_grid_widget.setFixedSize(width, height)
        if self.month_labels_widget is not None:
            self.month_labels_widget.setFixedSize(
                width, self._heatmap_label_height
            )
        if self.heatmap_widget is not None:
            self.heatmap_widget.setFixedSize(width, total_height)

    def _clear_heatmap(self) -> None:
        while self.heatmap_layout.count():
            item = self.heatmap_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        while self.month_labels_layout.count():
            item = self.month_labels_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.heatmap_cells.clear()
        self.heatmap_placeholder_cells.clear()
        self.month_label_widgets.clear()
        self.month_label_spacers.clear()

    def _refresh_heatmap(self) -> None:
        current_year = QDate.currentDate().year()
        if current_year != self._heatmap_year:
            self._heatmap_year = current_year
            self._clear_heatmap()
            self._populate_heatmap_cells(current_year)
        for cell in self.heatmap_placeholder_cells:
            self._apply_placeholder_style(cell)
        for key in self.heatmap_cells:
            self._update_heatmap_cell(key)

    def _apply_placeholder_style(self, cell: QFrame) -> None:
        cell.setStyleSheet(
            "QFrame#heatmapCell {"
            "border-radius: 2px;"
            "background-color: rgba(0, 0, 0, 0);"
            "}"
        )

    def _heatmap_base_color(self, date_key: str) -> QColor:
        date = QDate.fromString(date_key, "yyyy-MM-dd")
        base = self.settings.heatmap_color
        if date.isValid() and date.month() % 2 == 0:
            return base.lighter(125)
        return base

    def _heatmap_cell_stylesheet(self, base: QColor, alpha: int) -> str:
        hover_bg = qcolor_to_hex(self.settings.heatmap_hover_cell_color)
        return (
            "QFrame#heatmapCell {"
            "border-radius: 2px;"
            f"background-color: rgba({base.red()}, {base.green()}, {base.blue()},"
            f"{alpha});"
            "}"
            "QFrame#heatmapCell:hover {"
            f"background-color: {hover_bg};"
            "}"
        )

    def _update_heatmap_cell(self, date_key: str) -> None:
        cell = self.heatmap_cells.get(date_key)
        if cell is None:
            return
        base = self._heatmap_base_color(date_key)
        seconds = self._total_seconds_for_day(date_key)
        goal_seconds = self._goal_seconds_for_date(date_key)
        if goal_seconds > 0:
            if seconds >= goal_seconds:
                alpha = 220
            elif seconds > 0:
                alpha = 120
            else:
                alpha = 40
        else:
            alpha = 120 if seconds > 0 else 40
        percent = format_percent(seconds, goal_seconds)
        tooltip = (
            f"Date: {date_key}\n"
            f"Time: {format_duration_hms(seconds)}\n"
            f"Super goal: {percent}"
        )
        cell.setStyleSheet(self._heatmap_cell_stylesheet(base, alpha))
        cell.setToolTip(tooltip)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._acrylic_enabled:
            apply_windows_acrylic(
                int(self.winId()), self.settings.bg_color, self.settings.opacity
            )


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setQuitOnLastWindowClosed(True)
    app.setStyle("Fusion")
    init_paths()
    data_dir = DATA_DIR or resolve_data_dir()
    log_path = os.path.join(data_dir, "debug.log")
    setup_logging(log_path)
    sys.excepthook = log_unhandled_exception
    window = CountdownWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
