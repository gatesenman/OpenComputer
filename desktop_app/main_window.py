"""
Main window: premium sidebar navigation with all pipeline pages.
"""

import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from dashboard_page import DashboardPage
from setup_page import SetupPage
from settings_page import SettingsPage
from verifier_page import VerifierPage
from smoke_page import SmokePage
from taskgen_page import TaskGenPage
from tasks_page import TasksPage
from eval_page import EvalPage
from rerun_page import RerunPage
from results_page import ResultsPage
from repair_page import RepairPage
from sandbox_page import SandboxPage
from cleanup_page import CleanupPage


NAV_ITEMS = [
    ("首页",         "overview",   "◉"),
    ("环境安装",     "setup",      "⚙"),
    ("设置",         "settings",   "⊙"),
    (None, None, None),  # separator
    ("验证器管理",   "verifiers",  "☑"),
    ("Smoke 测试",   "smoke",      "⚡"),
    ("任务生成",     "taskgen",    "✦"),
    ("任务浏览",     "tasks",      "≡"),
    (None, None, None),  # separator
    ("运行评估",     "eval",       "▶"),
    ("重新评估",     "rerun",      "⟲"),
    ("评估结果",     "results",    "◫"),
    (None, None, None),  # separator
    ("修复循环",     "repair",     "⟳"),
    ("交互沙盒",     "sandbox",    "◻"),
    ("资源清理",     "cleanup",    "✕"),
]

PAGE_BUILDERS = [
    DashboardPage, SetupPage, SettingsPage,
    VerifierPage, SmokePage, TaskGenPage, TasksPage,
    EvalPage, RerunPage, ResultsPage,
    RepairPage, SandboxPage, CleanupPage,
]


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OpenComputer - 桌面端")
        self.resize(1280, 860)
        self.setMinimumSize(960, 640)
        self._nav_buttons = []
        self._nav_index_map = {}
        self._init_ui()
        self._switch_page(0)

    def _init_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Logo area
        logo_widget = QWidget()
        logo_widget.setStyleSheet("background: transparent;")
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(16, 20, 16, 6)
        logo_layout.setSpacing(10)

        # Icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
        if os.path.exists(icon_path):
            icon_lbl = QLabel()
            pm = QPixmap(icon_path).scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_lbl.setPixmap(pm)
            icon_lbl.setFixedSize(36, 36)
            logo_layout.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        logo_lbl = QLabel("OpenComputer")
        logo_lbl.setStyleSheet("font-size:16px;font-weight:bold;color:#ffffff;background:transparent;")
        title_col.addWidget(logo_lbl)
        tag = QLabel("端到端桌面客户端")
        tag.setStyleSheet("font-size:10px;color:rgba(180,200,220,0.5);background:transparent;")
        title_col.addWidget(tag)
        logo_layout.addLayout(title_col)
        logo_layout.addStretch()

        sb_layout.addWidget(logo_widget)

        # Separator line under logo
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(255,255,255,0.08); margin: 8px 16px;")
        sb_layout.addWidget(sep)

        # Nav buttons
        page_idx = 0
        for label, key, icon in NAV_ITEMS:
            if label is None:
                # Separator
                s = QWidget()
                s.setFixedHeight(1)
                s.setStyleSheet("background: rgba(255,255,255,0.05); margin: 6px 16px;")
                sb_layout.addWidget(s)
                continue

            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            idx = page_idx
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            sb_layout.addWidget(btn)
            self._nav_buttons.append(btn)
            self._nav_index_map[page_idx] = len(self._nav_buttons) - 1
            page_idx += 1

        sb_layout.addStretch()

        # Version badge
        ver_widget = QWidget()
        ver_widget.setStyleSheet("background: transparent;")
        ver_layout = QVBoxLayout(ver_widget)
        ver_layout.setContentsMargins(16, 8, 16, 14)
        ver = QLabel("v3.0.0")
        ver.setStyleSheet(
            "color:rgba(180,200,220,0.35);font-size:11px;background:transparent;"
        )
        ver_layout.addWidget(ver)
        sb_layout.addWidget(ver_widget)

        root.addWidget(sidebar)

        # ── Content ──
        self.stack = QStackedWidget()
        self.stack.setObjectName("contentArea")

        for builder in PAGE_BUILDERS:
            self.stack.addWidget(builder())

        root.addWidget(self.stack, 1)

    def _switch_page(self, idx):
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == self._nav_index_map.get(idx, -1))
        self.stack.setCurrentIndex(idx)
