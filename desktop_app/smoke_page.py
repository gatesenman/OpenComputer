"""
Smoke test page: run verifier smoke tests per app with live log output.
"""

import json
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from worker import CmdWorker, project_root


def _list_apps_with_verifiers():
    v_dir = project_root() / "verifiers"
    apps = []
    if v_dir.exists():
        for d in sorted(v_dir.iterdir()):
            if d.is_dir() and (d / f"{d.name}.py").exists():
                apps.append(d.name)
    return apps


def _list_smoke_runs(app_name=None):
    runs_dir = project_root() / "smoke" / "runs"
    runs = []
    if not runs_dir.exists():
        return runs
    for d in sorted(runs_dir.iterdir(), reverse=True):
        if d.is_dir():
            if app_name and not d.name.startswith(app_name):
                continue
            report = d / "REPORT.md"
            runs.append({
                "name": d.name,
                "dir": str(d),
                "has_report": report.exists(),
            })
    return runs


class SmokePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._init_ui()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 20, 30, 20)

        title = QLabel("Smoke 测试")
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        subtitle = QLabel(
            "验证器冒烟测试：在真实沙盒中运行简单任务，确认验证器端点正常工作。"
            "在生成正式任务之前运行此测试。"
        )
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        # Config
        config_row = QHBoxLayout()

        grp = QGroupBox("测试配置")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        self.cb_app = QComboBox()
        apps = _list_apps_with_verifiers()
        self.cb_app.addItems(apps)
        self.cb_app.setToolTip("选择要进行冒烟测试的应用")
        form.addRow(QLabel("应用:"), self.cb_app)

        self.sp_max_tasks = QSpinBox()
        self.sp_max_tasks.setRange(1, 50)
        self.sp_max_tasks.setValue(20)
        self.sp_max_tasks.setToolTip("生成的最大冒烟任务数")
        form.addRow(QLabel("最大任务数:"), self.sp_max_tasks)

        self.sp_max_rounds = QSpinBox()
        self.sp_max_rounds.setRange(1, 10)
        self.sp_max_rounds.setValue(3)
        self.sp_max_rounds.setToolTip("每个任务的最大修复轮数")
        form.addRow(QLabel("最大修复轮数:"), self.sp_max_rounds)

        self.chk_gen_only = QCheckBox("仅生成（不运行）")
        self.chk_gen_only.setToolTip("只生成冒烟任务，不实际运行")
        form.addRow(QLabel(""), self.chk_gen_only)

        self.chk_run_only = QCheckBox("仅运行（已有任务）")
        self.chk_run_only.setToolTip("运行已存在的冒烟任务，不重新生成")
        form.addRow(QLabel(""), self.chk_run_only)

        grp.setLayout(form)
        config_row.addWidget(grp)
        config_row.addStretch()
        outer.addLayout(config_row)

        # Buttons
        btn_row = QHBoxLayout()

        self.btn_run = QPushButton("开始 Smoke 测试")
        self.btn_run.setObjectName("btnSuccess")
        self.btn_run.setMinimumHeight(38)
        self.btn_run.clicked.connect(self._start)
        btn_row.addWidget(self.btn_run)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.setObjectName("btnDanger")
        self.btn_stop.setMinimumHeight(38)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop)
        btn_row.addWidget(self.btn_stop)

        self.btn_view_report = QPushButton("查看最新报告")
        self.btn_view_report.setObjectName("btnSecondary")
        self.btn_view_report.setMinimumHeight(38)
        self.btn_view_report.clicked.connect(self._view_report)
        btn_row.addWidget(self.btn_view_report)

        btn_row.addStretch()
        outer.addLayout(btn_row)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        outer.addWidget(self.progress)

        # Splitter: log + report
        splitter = QSplitter(Qt.Vertical)

        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("Smoke 测试日志...")
        splitter.addWidget(self.log_area)

        self.report_view = QTextBrowser()
        self.report_view.setPlaceholderText("测试报告将在此显示...")
        splitter.addWidget(self.report_view)

        splitter.setSizes([400, 200])
        outer.addWidget(splitter, 1)

    def _start(self):
        if self._worker and self._worker.isRunning():
            return
        app = self.cb_app.currentText()
        if not app:
            return

        cmd = [sys.executable, "smoke/smoke_loop.py", "--app", app]
        cmd.extend(["--max-tasks", str(self.sp_max_tasks.value())])
        cmd.extend(["--max-rounds", str(self.sp_max_rounds.value())])

        if self.chk_gen_only.isChecked():
            cmd.append("--generate-only")
        if self.chk_run_only.isChecked():
            cmd.append("--run-only")

        self.log_area.clear()
        self.log_area.appendPlainText(f">>> {' '.join(cmd)}\n")
        self.progress.setVisible(True)
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self._worker = CmdWorker(cmd)
        self._worker.log.connect(lambda t: (
            self.log_area.appendPlainText(t),
            self.log_area.verticalScrollBar().setValue(
                self.log_area.verticalScrollBar().maximum()
            ),
        ))
        self._worker.finished.connect(self._on_done)
        self._worker.start()

    def _stop(self):
        if self._worker:
            self._worker.cancel()

    def _on_done(self, code):
        self.progress.setVisible(False)
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        status = "完成" if code == 0 else f"结束 (退出码 {code})"
        self.log_area.appendPlainText(f"\n--- Smoke 测试{status} ---\n")
        self._worker = None
        self._view_report()

    def _view_report(self):
        app = self.cb_app.currentText()
        runs = _list_smoke_runs(app)
        if not runs:
            self.report_view.setPlainText("暂无测试报告。")
            return
        latest = runs[0]
        report_path = Path(latest["dir"]) / "REPORT.md"
        if report_path.exists():
            content = report_path.read_text(encoding="utf-8", errors="replace")
            self.report_view.setMarkdown(content)
        else:
            self.report_view.setPlainText(f"报告文件不存在: {report_path}")
