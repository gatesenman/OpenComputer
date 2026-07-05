"""
Re-run evaluation page: replay tasks from a previous run with a different model.
Wraps evaluation/run_eval_from_run.py.
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
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from worker import CmdWorker, project_root


MODELS = [
    "kimi-k2.6", "kimi-k2.5",
    "claude-sonnet-4-6", "claude-sonnet-4-5", "claude-sonnet-4",
    "claude-opus-4", "claude-opus-4-1", "claude-opus-4-5", "claude-opus-4-6",
    "claude-3-7-sonnet",
    "gpt-5.4", "gpt-5", "chatgpt", "computer-use-preview",
    "gemini-3-flash", "gemini-3-flash-preview", "gemini-2.5-computer-use",
    "qwen3-vl", "qwen2.5-vl-72b",
    "qwen3.5-35b-a3b", "qwen3.5-27b", "qwen3.5-9b", "qwen3.5-4b",
    "evocua-s1", "evocua-s2",
    "mano", "opencua", "dart",
    "gui-owl-1.5", "holo-3.1",
    "azure-chatgpt", "azure-gpt-5.4",
]


def _list_runs():
    runs_dir = project_root() / "evaluation" / "runs"
    runs = []
    if not runs_dir.exists():
        return runs
    seen = set()
    for trajs_root in runs_dir.rglob("trajectories"):
        if not trajs_root.is_dir():
            continue
        run_dir = trajs_root.parent
        try:
            run_id = run_dir.relative_to(runs_dir).as_posix()
        except ValueError:
            continue
        if run_id not in seen:
            seen.add(run_id)
            runs.append(run_id)
    return sorted(runs, reverse=True)


class RerunPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._init_ui()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 20, 30, 20)

        title = QLabel("重新评估")
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        subtitle = QLabel(
            "从已有的评估运行中选择任务，用不同的模型重新运行。"
            "适合对比不同模型在相同任务上的表现，或重新测试之前失败的任务。"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        outer.addWidget(subtitle)

        config_row = QHBoxLayout()

        # Left: source run & model
        grp_source = QGroupBox("来源配置")
        form_source = QFormLayout()
        form_source.setLabelAlignment(Qt.AlignRight)
        form_source.setSpacing(10)

        self.cb_source_run = QComboBox()
        self.cb_source_run.setMinimumWidth(300)
        runs = _list_runs()
        if runs:
            self.cb_source_run.addItems(runs)
        else:
            self.cb_source_run.addItem("暂无评估记录")
        form_source.addRow(QLabel("源运行:"), self.cb_source_run)

        self.cb_model = QComboBox()
        self.cb_model.setEditable(True)
        self.cb_model.addItems(MODELS)
        form_source.addRow(QLabel("新模型:"), self.cb_model)

        self.sp_tasks_per_app = QSpinBox()
        self.sp_tasks_per_app.setRange(1, 100)
        self.sp_tasks_per_app.setValue(5)
        form_source.addRow(QLabel("每应用任务数:"), self.sp_tasks_per_app)

        grp_source.setLayout(form_source)
        config_row.addWidget(grp_source)

        # Middle: filters
        grp_filter = QGroupBox("任务过滤")
        form_filter = QFormLayout()
        form_filter.setLabelAlignment(Qt.AlignRight)
        form_filter.setSpacing(10)

        self.chk_only_failed = QCheckBox("仅失败任务")
        self.chk_only_failed.setToolTip("仅选择源运行中未通过的任务")
        form_filter.addRow(QLabel(""), self.chk_only_failed)

        self.chk_only_passed = QCheckBox("仅成功任务")
        self.chk_only_passed.setToolTip("仅选择源运行中已通过的任务")
        form_filter.addRow(QLabel(""), self.chk_only_passed)

        self.chk_include_errors = QCheckBox("包含错误任务")
        self.chk_include_errors.setToolTip("包含源运行中因错误终止的任务")
        form_filter.addRow(QLabel(""), self.chk_include_errors)

        self.chk_dry_run = QCheckBox("仅预览 (不运行)")
        self.chk_dry_run.setToolTip("只列出将要运行的任务，不实际执行")
        form_filter.addRow(QLabel(""), self.chk_dry_run)

        grp_filter.setLayout(form_filter)
        config_row.addWidget(grp_filter)

        # Right: run params
        grp_params = QGroupBox("运行参数")
        form_params = QFormLayout()
        form_params.setLabelAlignment(Qt.AlignRight)
        form_params.setSpacing(10)

        self.sp_max_iter = QSpinBox()
        self.sp_max_iter.setRange(1, 500)
        self.sp_max_iter.setValue(100)
        form_params.addRow(QLabel("最大步数:"), self.sp_max_iter)

        self.sp_timeout = QSpinBox()
        self.sp_timeout.setRange(60, 7200)
        self.sp_timeout.setValue(3600)
        self.sp_timeout.setSuffix(" 秒")
        form_params.addRow(QLabel("超时时间:"), self.sp_timeout)

        self.sp_parallel = QSpinBox()
        self.sp_parallel.setRange(1, 32)
        self.sp_parallel.setValue(1)
        form_params.addRow(QLabel("并行数:"), self.sp_parallel)

        self.le_endpoint = QLineEdit()
        self.le_endpoint.setPlaceholderText("http://localhost:8001/v1")
        form_params.addRow(QLabel("自定义端点:"), self.le_endpoint)

        grp_params.setLayout(form_params)
        config_row.addWidget(grp_params)

        outer.addLayout(config_row)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_run = QPushButton("开始重新评估")
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

        btn_refresh = QPushButton("刷新运行列表")
        btn_refresh.setObjectName("btnSecondary")
        btn_refresh.setMinimumHeight(40)
        btn_refresh.clicked.connect(self._refresh_runs)
        btn_row.addWidget(btn_refresh)

        btn_clear = QPushButton("清空日志")
        btn_clear.setObjectName("btnSecondary")
        btn_clear.setMinimumHeight(40)
        btn_clear.clicked.connect(lambda: self.log_area.clear())
        btn_row.addWidget(btn_clear)

        btn_row.addStretch()
        outer.addLayout(btn_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        outer.addWidget(self.progress)

        self.lbl_status = QLabel("就绪")
        self.lbl_status.setObjectName("statusOk")
        outer.addWidget(self.lbl_status)

        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("重新评估日志...")
        outer.addWidget(self.log_area, 1)

    def _refresh_runs(self):
        self.cb_source_run.clear()
        runs = _list_runs()
        if runs:
            self.cb_source_run.addItems(runs)
        else:
            self.cb_source_run.addItem("暂无评估记录")

    def _start(self):
        source = self.cb_source_run.currentText()
        if not source or source == "暂无评估记录":
            return

        cmd = [
            sys.executable, "evaluation/run_eval_from_run.py",
            "--source-run", source,
            "--model", self.cb_model.currentText(),
            "--tasks-per-app", str(self.sp_tasks_per_app.value()),
            "--max-iterations", str(self.sp_max_iter.value()),
            "--sandbox-timeout", str(self.sp_timeout.value()),
            "--parallel", str(self.sp_parallel.value()),
        ]

        if self.chk_only_failed.isChecked():
            cmd.append("--only-failed")
        if self.chk_only_passed.isChecked():
            cmd.append("--only-passed")
        if self.chk_include_errors.isChecked():
            cmd.append("--include-errors")
        if self.chk_dry_run.isChecked():
            cmd.append("--dry-run")

        endpoint = self.le_endpoint.text().strip()
        if endpoint:
            cmd.extend(["--endpoint-url", endpoint])

        if self._worker and self._worker.isRunning():
            return
        self.log_area.appendPlainText(f">>> {' '.join(cmd)}\n")
        self._worker = CmdWorker(cmd)
        self._worker.log.connect(lambda t: (
            self.log_area.appendPlainText(t),
            self.log_area.verticalScrollBar().setValue(
                self.log_area.verticalScrollBar().maximum()
            ),
        ))
        self._worker.finished.connect(self._on_finished)
        self._worker.start()
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress.setVisible(True)
        self.lbl_status.setText("运行中...")
        self.lbl_status.setStyleSheet("color:#fdcb6e;font-weight:bold;")

    def _stop(self):
        if self._worker:
            self._worker.cancel()

    def _on_finished(self, code):
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress.setVisible(False)
        if code == 0:
            self.lbl_status.setText("完成")
            self.lbl_status.setStyleSheet("color:#00b894;font-weight:bold;")
        else:
            self.lbl_status.setText(f"结束 (退出码: {code})")
            self.lbl_status.setStyleSheet("color:#d63031;font-weight:bold;")
        self.log_area.appendPlainText(f"\n--- 结束 (退出码: {code}) ---\n")
        self._worker = None
