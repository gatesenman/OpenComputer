"""
Resource cleanup page: clean up Docker containers and E2B sandboxes.
"""

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from worker import CmdWorker


class CleanupPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._init_ui()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 20, 30, 20)

        title = QLabel("资源清理")
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        subtitle = QLabel(
            "清理评估过程中残留的 Docker 容器和 E2B 沙盒实例，释放系统资源。"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        outer.addWidget(subtitle)

        cards = QHBoxLayout()

        # Docker cleanup
        grp_docker = QGroupBox("Docker 容器清理")
        form_d = QVBoxLayout()
        self.chk_docker_force = QCheckBox("强制清理（不确认）")
        form_d.addWidget(self.chk_docker_force)

        self.cb_docker_state = QComboBox()
        self.cb_docker_state.addItems(["全部状态", "running", "exited", "created", "paused", "dead"])
        fl = QFormLayout()
        fl.addRow(QLabel("容器状态:"), self.cb_docker_state)
        form_d.addLayout(fl)

        btn_row_d = QHBoxLayout()
        btn_list_d = QPushButton("列出容器")
        btn_list_d.setObjectName("btnSecondary")
        btn_list_d.clicked.connect(self._list_docker)
        btn_row_d.addWidget(btn_list_d)

        btn_clean_d = QPushButton("清理容器")
        btn_clean_d.setObjectName("btnDanger")
        btn_clean_d.clicked.connect(self._clean_docker)
        btn_row_d.addWidget(btn_clean_d)
        form_d.addLayout(btn_row_d)

        grp_docker.setLayout(form_d)
        cards.addWidget(grp_docker)

        # E2B cleanup
        grp_e2b = QGroupBox("E2B 沙盒清理")
        form_e = QVBoxLayout()
        self.chk_e2b_force = QCheckBox("强制清理（不确认）")
        form_e.addWidget(self.chk_e2b_force)

        self.cb_e2b_state = QComboBox()
        self.cb_e2b_state.addItems(["全部状态", "running", "paused"])
        fl2 = QFormLayout()
        fl2.addRow(QLabel("沙盒状态:"), self.cb_e2b_state)
        form_e.addLayout(fl2)

        btn_row_e = QHBoxLayout()
        btn_list_e = QPushButton("列出沙盒")
        btn_list_e.setObjectName("btnSecondary")
        btn_list_e.clicked.connect(self._list_e2b)
        btn_row_e.addWidget(btn_list_e)

        btn_clean_e = QPushButton("清理沙盒")
        btn_clean_e.setObjectName("btnDanger")
        btn_clean_e.clicked.connect(self._clean_e2b)
        btn_row_e.addWidget(btn_clean_e)
        form_e.addLayout(btn_row_e)

        grp_e2b.setLayout(form_e)
        cards.addWidget(grp_e2b)

        outer.addLayout(cards)

        # Stop button
        btn_stop = QPushButton("停止当前操作")
        btn_stop.setObjectName("btnDanger")
        btn_stop.clicked.connect(self._stop)
        outer.addWidget(btn_stop)

        # Log
        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("操作日志...")
        outer.addWidget(self.log_area, 1)

    def _run(self, cmd):
        if self._worker and self._worker.isRunning():
            return
        self.log_area.appendPlainText(f">>> {' '.join(cmd)}\n")
        self._worker = CmdWorker(cmd)
        self._worker.log.connect(lambda t: self.log_area.appendPlainText(t))
        self._worker.finished.connect(
            lambda c: self.log_area.appendPlainText(f"\n--- 结束 (退出码: {c}) ---\n")
        )
        self._worker.start()

    def _list_docker(self):
        cmd = [sys.executable, "-m", "computer_env.backends.docker.cleanup_containers", "--json"]
        state = self.cb_docker_state.currentText()
        if state != "全部状态":
            cmd.extend(["--state", state])
        self._run(cmd)

    def _clean_docker(self):
        cmd = [sys.executable, "-m", "computer_env.backends.docker.cleanup_containers"]
        if self.chk_docker_force.isChecked():
            cmd.append("--force")
        state = self.cb_docker_state.currentText()
        if state != "全部状态":
            cmd.extend(["--state", state])
        self._run(cmd)

    def _list_e2b(self):
        cmd = [sys.executable, "-m", "computer_env.backends.e2b.cleanup_sandboxes", "--json"]
        state = self.cb_e2b_state.currentText()
        if state != "全部状态":
            cmd.extend(["--state", state])
        self._run(cmd)

    def _clean_e2b(self):
        cmd = [sys.executable, "-m", "computer_env.backends.e2b.cleanup_sandboxes"]
        if self.chk_e2b_force.isChecked():
            cmd.append("--force")
        state = self.cb_e2b_state.currentText()
        if state != "全部状态":
            cmd.extend(["--state", state])
        self._run(cmd)

    def _stop(self):
        if self._worker:
            self._worker.cancel()
