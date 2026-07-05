"""
Repair loop page: run the iterative verifier-script repair pipeline on specific tasks.
"""

import json
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
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from worker import CmdWorker, project_root


def _list_apps_with_tasks():
    tasks_dir = project_root() / "task_generator" / "tasks"
    apps = set()
    if tasks_dir.exists():
        for td in tasks_dir.iterdir():
            if td.is_dir() and (td / "task.json").exists():
                try:
                    data = json.loads((td / "task.json").read_text(encoding="utf-8"))
                    app = data.get("app")
                    if app:
                        apps.add(app)
                except Exception:
                    pass
    return sorted(apps)


def _list_tasks_for_app(app_name):
    tasks_dir = project_root() / "task_generator" / "tasks"
    tasks = []
    if not tasks_dir.exists():
        return tasks
    for td in sorted(tasks_dir.iterdir()):
        if not td.is_dir():
            continue
        tf = td / "task.json"
        if tf.exists():
            try:
                data = json.loads(tf.read_text(encoding="utf-8"))
                if data.get("app") == app_name:
                    tasks.append(data.get("id", td.name))
            except Exception:
                pass
    return tasks


def _list_repair_runs():
    runs_dir = project_root() / "evaluation" / "repair" / "runs"
    runs = []
    if not runs_dir.exists():
        return runs
    for d in sorted(runs_dir.iterdir(), reverse=True):
        if d.is_dir():
            solved = d / "SOLVED.md"
            runs.append({
                "name": d.name,
                "dir": str(d),
                "has_solved": solved.exists(),
            })
    return runs


class RepairPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._init_ui()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 20, 30, 20)

        title = QLabel("修复循环")
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        subtitle = QLabel(
            "对已完成的评估任务运行修复循环：代理执行任务 → LLM 评判 → "
            "验证器对比 → 自动修复验证器/任务。用于提升验证器准确性。"
        )
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        # Config
        config_row = QHBoxLayout()

        grp = QGroupBox("修复配置")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        self.cb_app = QComboBox()
        apps = _list_apps_with_tasks()
        self.cb_app.addItems(apps)
        self.cb_app.currentTextChanged.connect(self._on_app_changed)
        form.addRow(QLabel("应用:"), self.cb_app)

        self.cb_task = QComboBox()
        self.cb_task.setToolTip("选择要修复的具体任务")
        form.addRow(QLabel("任务:"), self.cb_task)

        self.sp_rounds = QSpinBox()
        self.sp_rounds.setRange(1, 10)
        self.sp_rounds.setValue(3)
        self.sp_rounds.setToolTip("最大修复轮数")
        form.addRow(QLabel("最大轮数:"), self.sp_rounds)

        self.sp_iterations = QSpinBox()
        self.sp_iterations.setRange(10, 200)
        self.sp_iterations.setValue(60)
        self.sp_iterations.setToolTip("代理最大操作步数")
        form.addRow(QLabel("最大步数:"), self.sp_iterations)

        grp.setLayout(form)
        config_row.addWidget(grp)

        # History
        grp_hist = QGroupBox("修复历史")
        hist_layout = QVBoxLayout()
        self.cb_history = QComboBox()
        self.cb_history.setMinimumWidth(300)
        self.cb_history.currentTextChanged.connect(self._on_history_selected)
        hist_layout.addWidget(self.cb_history)
        self.btn_refresh_hist = QPushButton("刷新历史")
        self.btn_refresh_hist.setObjectName("btnSecondary")
        self.btn_refresh_hist.clicked.connect(self._refresh_history)
        hist_layout.addWidget(self.btn_refresh_hist)
        grp_hist.setLayout(hist_layout)
        config_row.addWidget(grp_hist)

        outer.addLayout(config_row)

        # Buttons
        btn_row = QHBoxLayout()

        self.btn_run = QPushButton("开始修复")
        self.btn_run.setObjectName("btnSuccess")
        self.btn_run.setMinimumHeight(40)
        self.btn_run.clicked.connect(self._start)
        btn_row.addWidget(self.btn_run)

        self.btn_stop = QPushButton("停止")
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

        # Splitter: log + solved report
        splitter = QSplitter(Qt.Vertical)

        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("修复循环日志...")
        splitter.addWidget(self.log_area)

        self.solved_view = QTextBrowser()
        self.solved_view.setPlaceholderText("修复报告 (SOLVED.md) 将在此显示...")
        splitter.addWidget(self.solved_view)

        splitter.setSizes([400, 200])
        outer.addWidget(splitter, 1)

        # Init
        if apps:
            self._on_app_changed(apps[0])
        self._refresh_history()

    def _on_app_changed(self, app):
        self.cb_task.clear()
        if app:
            self.cb_task.addItems(_list_tasks_for_app(app))

    def _refresh_history(self):
        self.cb_history.clear()
        runs = _list_repair_runs()
        if not runs:
            self.cb_history.addItem("暂无修复记录")
            return
        for r in runs:
            tag = " [有报告]" if r["has_solved"] else ""
            self.cb_history.addItem(f"{r['name']}{tag}")

    def _on_history_selected(self, name):
        if not name or name == "暂无修复记录":
            self.solved_view.clear()
            return
        clean_name = name.replace(" [有报告]", "")
        runs_dir = project_root() / "evaluation" / "repair" / "runs"
        solved = runs_dir / clean_name / "SOLVED.md"
        if solved.exists():
            self.solved_view.setMarkdown(solved.read_text(encoding="utf-8", errors="replace"))
        else:
            self.solved_view.setPlainText(f"无 SOLVED.md: {solved}")

    def _start(self):
        if self._worker and self._worker.isRunning():
            return
        task = self.cb_task.currentText()
        if not task:
            return

        cmd = [
            sys.executable, "evaluation/repair/repair_loop.py",
            "--task", task,
            "--max-rounds", str(self.sp_rounds.value()),
            "--max-iterations", str(self.sp_iterations.value()),
        ]

        app = self.cb_app.currentText()
        if app:
            cmd.extend(["--app", app])

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
        self.log_area.appendPlainText(f"\n--- 修复循环{status} ---")
        self._worker = None
        self._refresh_history()
