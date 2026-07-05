"""
Interactive sandbox page: launch a sandbox for manual testing / debugging.
"""

import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from worker import CmdWorker, project_root


def _list_apps():
    """List apps from evaluation/apps/specs/."""
    specs_dir = project_root() / "evaluation" / "apps" / "specs"
    apps = []
    if specs_dir.exists():
        for f in sorted(specs_dir.iterdir()):
            if f.suffix == ".py" and f.name != "__init__.py":
                apps.append(f.stem)
    return apps


class SandboxPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._init_ui()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 20, 30, 20)

        title = QLabel("交互式沙盒")
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        subtitle = QLabel(
            "启动一个交互式桌面沙盒，可以手动测试应用、调试验证器，或验证任务配置。"
            "沙盒会打开一个远程桌面链接。"
        )
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        # Config
        config_row = QHBoxLayout()

        grp = QGroupBox("沙盒配置")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        self.cb_app = QComboBox()
        self.cb_app.addItem("(不指定应用)")
        apps = _list_apps()
        self.cb_app.addItems(apps)
        self.cb_app.setToolTip("选择要在沙盒中启动的应用（可选）")
        form.addRow(QLabel("应用:"), self.cb_app)

        self.cb_backend = QComboBox()
        self.cb_backend.addItems(["e2b", "docker"])
        self.cb_backend.setToolTip("沙盒运行后端")
        form.addRow(QLabel("后端:"), self.cb_backend)

        self.sp_timeout = QSpinBox()
        self.sp_timeout.setRange(60, 7200)
        self.sp_timeout.setValue(3600)
        self.sp_timeout.setSuffix(" 秒")
        self.sp_timeout.setToolTip("沙盒存活时间")
        form.addRow(QLabel("超时时间:"), self.sp_timeout)

        grp.setLayout(form)
        config_row.addWidget(grp)
        config_row.addStretch()
        outer.addLayout(config_row)

        # Buttons
        btn_row = QHBoxLayout()

        self.btn_launch = QPushButton("启动沙盒")
        self.btn_launch.setObjectName("btnSuccess")
        self.btn_launch.setMinimumHeight(40)
        self.btn_launch.clicked.connect(self._launch)
        btn_row.addWidget(self.btn_launch)

        self.btn_stop = QPushButton("关闭沙盒")
        self.btn_stop.setObjectName("btnDanger")
        self.btn_stop.setMinimumHeight(40)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop)
        btn_row.addWidget(self.btn_stop)

        btn_row.addStretch()
        outer.addLayout(btn_row)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        outer.addWidget(self.progress)

        # Connection info
        self.lbl_info = QLabel("")
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_info.setStyleSheet(
            "background:#ffffff;border:1px solid #dfe6e9;border-radius:8px;"
            "padding:16px;font-size:14px;"
        )
        self.lbl_info.setVisible(False)
        outer.addWidget(self.lbl_info)

        # Log
        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("沙盒日志...")
        outer.addWidget(self.log_area, 1)

    def _launch(self):
        if self._worker and self._worker.isRunning():
            return

        cmd = [sys.executable, "evaluation/interactive_sandbox.py"]

        app = self.cb_app.currentText()
        if app and app != "(不指定应用)":
            cmd.extend(["--app", app])

        cmd.extend(["--env-backend", self.cb_backend.currentText()])
        cmd.extend(["--timeout", str(self.sp_timeout.value())])

        self.log_area.clear()
        self.log_area.appendPlainText(f">>> {' '.join(cmd)}\n")
        self.progress.setVisible(True)
        self.btn_launch.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_info.setVisible(False)

        self._worker = CmdWorker(cmd)
        self._worker.log.connect(self._on_log)
        self._worker.finished.connect(self._on_done)
        self._worker.start()

    def _on_log(self, text):
        self.log_area.appendPlainText(text)
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )
        # Try to extract stream URL
        lower = text.lower()
        if "stream" in lower or "url" in lower or "http" in lower or "vnc" in lower:
            if "http" in text:
                import re
                urls = re.findall(r'https?://[^\s\'"]+', text)
                if urls:
                    self.lbl_info.setText(
                        f"<b>沙盒已启动!</b><br/>"
                        f"远程桌面链接: <a href='{urls[0]}'>{urls[0]}</a><br/>"
                        f"<span style='color:#636e72'>点击链接在浏览器中打开远程桌面</span>"
                    )
                    self.lbl_info.setOpenExternalLinks(True)
                    self.lbl_info.setVisible(True)
                    self.progress.setVisible(False)

    def _stop(self):
        if self._worker:
            self._worker.cancel()

    def _on_done(self, code):
        self.progress.setVisible(False)
        self.btn_launch.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.log_area.appendPlainText(f"\n--- 沙盒已关闭 (退出码 {code}) ---")
        self._worker = None
