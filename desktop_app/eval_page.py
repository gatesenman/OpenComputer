"""
Evaluation runner page: full-featured evaluation with all options, real-time log, progress.
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
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from worker import CmdWorker, project_root


def _list_apps():
    tasks_dir = project_root() / "task_generator" / "tasks"
    apps = set()
    if tasks_dir.exists():
        for td in tasks_dir.iterdir():
            if not td.is_dir():
                continue
            tf = td / "task.json"
            if tf.exists():
                try:
                    data = json.loads(tf.read_text(encoding="utf-8"))
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
    "azure-chatgpt", "azure-gpt-5.4", "azure-computer-use-preview",
]


class EvalPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._init_ui()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 20, 30, 20)

        title = QLabel("运行评估")
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        subtitle = QLabel("选择应用、模型和参数，一键启动评估任务。运行日志将实时显示在下方。")
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        # ── Config section ──
        config_row = QHBoxLayout()

        # Left: app & model
        grp_basic = QGroupBox("基本配置")
        form_basic = QFormLayout()
        form_basic.setLabelAlignment(Qt.AlignRight)
        form_basic.setSpacing(10)

        self.cb_app = QComboBox()
        self.cb_app.addItem("全部应用")
        self.cb_app.addItems(_list_apps())
        self.cb_app.currentTextChanged.connect(self._on_app_changed)
        form_basic.addRow(QLabel("应用:"), self.cb_app)

        self.cb_task = QComboBox()
        self.cb_task.addItem("全部任务")
        form_basic.addRow(QLabel("任务:"), self.cb_task)

        self.cb_model = QComboBox()
        self.cb_model.setEditable(True)
        self.cb_model.addItems(MODELS)
        form_basic.addRow(QLabel("模型:"), self.cb_model)

        self.cb_backend = QComboBox()
        self.cb_backend.addItems(["e2b", "docker", "remote_docker"])
        form_basic.addRow(QLabel("后端:"), self.cb_backend)

        grp_basic.setLayout(form_basic)
        config_row.addWidget(grp_basic)

        # Middle: parameters
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

        self.sp_tasks_per_app = QSpinBox()
        self.sp_tasks_per_app.setRange(0, 100)
        self.sp_tasks_per_app.setValue(0)
        self.sp_tasks_per_app.setSpecialValueText("全部")
        form_params.addRow(QLabel("每应用任务数:"), self.sp_tasks_per_app)

        grp_params.setLayout(form_params)
        config_row.addWidget(grp_params)

        # Right: advanced
        grp_adv = QGroupBox("高级选项")
        form_adv = QFormLayout()
        form_adv.setLabelAlignment(Qt.AlignRight)
        form_adv.setSpacing(10)

        self.le_resume = QLineEdit()
        self.le_resume.setPlaceholderText("留空则新建运行")
        self.le_resume.setToolTip("填入 run_id 以恢复之前中断的评估")
        form_adv.addRow(QLabel("恢复运行 ID:"), self.le_resume)

        self.le_endpoint = QLineEdit()
        self.le_endpoint.setPlaceholderText("http://localhost:8001/v1")
        self.le_endpoint.setToolTip("自定义 OpenAI 兼容 API 端点（本地模型部署）")
        form_adv.addRow(QLabel("自定义端点:"), self.le_endpoint)

        self.sp_endpoint_port = QSpinBox()
        self.sp_endpoint_port.setRange(0, 65535)
        self.sp_endpoint_port.setValue(0)
        self.sp_endpoint_port.setSpecialValueText("不设置")
        self.sp_endpoint_port.setToolTip("本地模型端口号（会覆盖自定义端点）")
        form_adv.addRow(QLabel("端点端口:"), self.sp_endpoint_port)

        self.le_skip_app = QLineEdit()
        self.le_skip_app.setPlaceholderText("例: zoom,thunderbird")
        self.le_skip_app.setToolTip("跳过指定应用（逗号分隔）")
        form_adv.addRow(QLabel("跳过应用:"), self.le_skip_app)

        self.chk_keep_alive = QCheckBox("保持沙盒存活")
        form_adv.addRow(QLabel(""), self.chk_keep_alive)

        self.chk_ready_only = QCheckBox("仅检查就绪")
        self.chk_ready_only.setToolTip("只启动应用并检查就绪状态，不运行代理")
        form_adv.addRow(QLabel(""), self.chk_ready_only)

        grp_adv.setLayout(form_adv)
        config_row.addWidget(grp_adv)

        outer.addLayout(config_row)

        # ── Action buttons ──
        btn_row = QHBoxLayout()

        self.btn_run = QPushButton("开始评估")
        self.btn_run.setObjectName("btnSuccess")
        self.btn_run.setMinimumHeight(40)
        self.btn_run.clicked.connect(self._start_eval)
        btn_row.addWidget(self.btn_run)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.setObjectName("btnDanger")
        self.btn_stop.setMinimumHeight(40)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_eval)
        btn_row.addWidget(self.btn_stop)

        self.btn_list_apps = QPushButton("查看可用应用")
        self.btn_list_apps.setObjectName("btnSecondary")
        self.btn_list_apps.setMinimumHeight(40)
        self.btn_list_apps.clicked.connect(self._list_apps_cmd)
        btn_row.addWidget(self.btn_list_apps)

        self.btn_list_models = QPushButton("查看可用模型")
        self.btn_list_models.setObjectName("btnSecondary")
        self.btn_list_models.setMinimumHeight(40)
        self.btn_list_models.clicked.connect(self._list_models_cmd)
        btn_row.addWidget(self.btn_list_models)

        self.btn_clear = QPushButton("清空日志")
        self.btn_clear.setObjectName("btnSecondary")
        self.btn_clear.setMinimumHeight(40)
        self.btn_clear.clicked.connect(lambda: self.log_area.clear())
        btn_row.addWidget(self.btn_clear)

        btn_row.addStretch()
        outer.addLayout(btn_row)

        # ── Progress + Status ──
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        outer.addWidget(self.progress)

        self.lbl_status = QLabel("就绪 — 选择配置后点击「开始评估」")
        self.lbl_status.setObjectName("statusOk")
        outer.addWidget(self.lbl_status)

        # ── Log output ──
        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("评估日志将在此显示...")
        outer.addWidget(self.log_area, 1)

    def _on_app_changed(self, text):
        self.cb_task.clear()
        self.cb_task.addItem("全部任务")
        if text and text != "全部应用":
            self.cb_task.addItems(_list_tasks_for_app(text))

    def _build_cmd(self):
        cmd = [sys.executable, "evaluation/run_eval.py"]

        app = self.cb_app.currentText()
        if app and app != "全部应用":
            cmd.extend(["--app", app])
            task = self.cb_task.currentText()
            if task and task != "全部任务":
                cmd.extend(["--task", task])

        cmd.extend(["--model", self.cb_model.currentText()])
        cmd.extend(["--env-backend", self.cb_backend.currentText()])
        cmd.extend(["--max-iterations", str(self.sp_max_iter.value())])
        cmd.extend(["--sandbox-timeout", str(self.sp_timeout.value())])
        cmd.extend(["--parallel", str(self.sp_parallel.value())])

        tpa = self.sp_tasks_per_app.value()
        if tpa > 0:
            cmd.extend(["--tasks-per-app", str(tpa)])

        resume = self.le_resume.text().strip()
        if resume:
            cmd.extend(["--resume", resume])

        endpoint = self.le_endpoint.text().strip()
        if endpoint:
            cmd.extend(["--endpoint-url", endpoint])

        ep_port = self.sp_endpoint_port.value()
        if ep_port > 0:
            cmd.extend(["--endpoint-port", str(ep_port)])

        skip = self.le_skip_app.text().strip()
        if skip:
            for s in skip.split(","):
                s = s.strip()
                if s:
                    cmd.extend(["--skip-app", s])

        if self.chk_keep_alive.isChecked():
            cmd.append("--keep-alive")
        if self.chk_ready_only.isChecked():
            cmd.append("--ready-check-only")

        return cmd

    def _run_cmd(self, cmd):
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(self, "提示", "已有任务正在运行，请先停止。")
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
        self._set_status("运行中...", "#fdcb6e")

    def _start_eval(self):
        self._run_cmd(self._build_cmd())

    def _list_apps_cmd(self):
        self._run_cmd([sys.executable, "evaluation/run_eval.py", "--list-apps"])

    def _list_models_cmd(self):
        self._run_cmd([sys.executable, "evaluation/run_eval.py", "--list-models"])

    def _stop_eval(self):
        if self._worker:
            self._worker.cancel()
            self.log_area.appendPlainText("\n[用户] 正在停止...\n")

    def _on_finished(self, code):
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress.setVisible(False)
        if code == 0:
            self._set_status("完成", "#00b894")
        else:
            self._set_status(f"结束 (退出码: {code})", "#d63031")
        self.log_area.appendPlainText(f"\n--- 结束 (退出码: {code}) ---\n")
        self._worker = None

    def _set_status(self, text, color):
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"color:{color};font-weight:bold;")
