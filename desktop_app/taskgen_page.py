"""
Task generation pipeline page: view proposals, evaluated tasks, and run generation stages.
Covers the 4-stage pipeline: Propose -> Evaluate -> Verify & Finalize -> Synthesize Env.
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
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from worker import project_root


def _list_apps():
    v_dir = project_root() / "verifiers"
    apps = []
    if v_dir.exists():
        for d in sorted(v_dir.iterdir()):
            if d.is_dir() and (d / f"{d.name}.py").exists():
                apps.append(d.name)
    return apps


def _load_proposals(app_name):
    tasks_dir = project_root() / "task_generator" / "tasks"
    path = tasks_dir / f"proposals_{app_name}.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _load_evaluated(app_name):
    tasks_dir = project_root() / "task_generator" / "tasks"
    path = tasks_dir / f"evaluated_{app_name}.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _load_app_tasks(app_name):
    tasks_dir = project_root() / "task_generator" / "tasks"
    path = tasks_dir / f"{app_name}_tasks.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Fallback: scan task dirs
    tasks = []
    for td in sorted(tasks_dir.iterdir()):
        if not td.is_dir():
            continue
        tf = td / "task.json"
        if tf.exists():
            try:
                data = json.loads(tf.read_text(encoding="utf-8"))
                if data.get("app") == app_name:
                    tasks.append(data)
            except Exception:
                pass
    return tasks


def _load_lessons():
    path = project_root() / "task_generator" / "LESSONS.md"
    if path.exists():
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            pass
    return "（LESSONS.md 文件未找到）"


class TaskGenPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 20, 30, 20)

        title = QLabel("任务生成流水线")
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        subtitle = QLabel(
            "查看任务生成流水线的各阶段产物："
            "提案 (proposals) → 评估 (evaluated) → 最终任务 (finalized)。"
            "同时可查看 LESSONS.md 记录的经验教训。"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        outer.addWidget(subtitle)

        # App selector
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("选择应用:"))
        self.cb_app = QComboBox()
        self.cb_app.addItems(_list_apps())
        self.cb_app.currentTextChanged.connect(self._on_app_changed)
        sel_row.addWidget(self.cb_app, 1)

        btn_refresh = QPushButton("刷新")
        btn_refresh.setObjectName("btnSecondary")
        btn_refresh.clicked.connect(self._refresh)
        sel_row.addWidget(btn_refresh)

        btn_lessons = QPushButton("查看 LESSONS.md")
        btn_lessons.clicked.connect(self._show_lessons)
        sel_row.addWidget(btn_lessons)

        outer.addLayout(sel_row)

        # Stats bar
        self.lbl_stats = QLabel("")
        self.lbl_stats.setStyleSheet(
            "background:#ffffff;border:1px solid #dfe6e9;border-radius:8px;"
            "padding:10px;font-size:13px;"
        )
        outer.addWidget(self.lbl_stats)

        # Splitter: table + detail
        splitter = QSplitter(Qt.Horizontal)

        # Left: table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "阶段", "难度", "复杂度", "目标/描述"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.currentCellChanged.connect(self._on_select)
        splitter.addWidget(self.table)

        # Right: detail
        self.detail = QTextBrowser()
        self.detail.setOpenExternalLinks(True)
        self.detail.setPlaceholderText("点击左侧条目查看详情...")
        splitter.addWidget(self.detail)

        splitter.setSizes([500, 400])
        outer.addWidget(splitter, 1)

    def _refresh(self):
        self.cb_app.clear()
        self.cb_app.addItems(_list_apps())

    def _on_app_changed(self, app_name):
        if not app_name:
            return
        proposals = _load_proposals(app_name)
        evaluated = _load_evaluated(app_name)
        finalized = _load_app_tasks(app_name)

        self._all_items = []
        for p in proposals:
            self._all_items.append(("提案", p))
        for e in evaluated:
            self._all_items.append(("已评估", e))
        for f in finalized:
            self._all_items.append(("最终", f))

        self.lbl_stats.setText(
            f"<b>{app_name}</b> — "
            f"提案: <b>{len(proposals)}</b>  |  "
            f"已评估: <b>{len(evaluated)}</b>  |  "
            f"最终任务: <b>{len(finalized)}</b>"
        )

        self.table.setRowCount(len(self._all_items))
        for i, (stage, item) in enumerate(self._all_items):
            tid = item.get("id", item.get("task_id", ""))
            self.table.setItem(i, 0, QTableWidgetItem(tid))
            self.table.setItem(i, 1, QTableWidgetItem(stage))

            meta = item.get("metadata", {})
            diff = str(meta.get("estimated_difficulty", item.get("estimated_difficulty", "")))
            self.table.setItem(i, 2, QTableWidgetItem(diff))

            cplx = str(meta.get("complexity", item.get("complexity", "")))
            self.table.setItem(i, 3, QTableWidgetItem(cplx))

            desc = item.get("task", item.get("objective", ""))
            if len(desc) > 80:
                desc = desc[:80] + "..."
            self.table.setItem(i, 4, QTableWidgetItem(desc))

    def _on_select(self, row, col, prev_row, prev_col):
        if row < 0 or row >= len(self._all_items):
            self.detail.clear()
            return
        stage, item = self._all_items[row]
        raw = json.dumps(item, indent=2, ensure_ascii=False)
        tid = item.get("id", item.get("task_id", "N/A"))
        desc = item.get("task", item.get("objective", "N/A"))
        meta = item.get("metadata", {})

        html = f"<h2 style='color:#0984e3;'>{tid}</h2>"
        html += f"<p><b>阶段:</b> {stage}</p>"
        html += f"<h3>描述/目标</h3>"
        html += f"<p style='background:#f5f6fa;padding:12px;border-radius:6px;'>{desc}</p>"

        criteria = item.get("success_criteria", [])
        if criteria:
            html += "<h3>成功标准</h3><ul>"
            for c in criteria:
                html += f"<li>{c}</li>"
            html += "</ul>"

        verif = item.get("verification", [])
        if verif:
            html += "<h3>验证命令</h3>"
            for v in verif:
                cmd = v.get("command", "")
                desc_v = v.get("description", "")
                html += f"<div style='background:#f5f6fa;padding:8px;border-radius:6px;margin-bottom:4px;'>"
                html += f"<code>{cmd}</code><br/><span style='color:#636e72;'>{desc_v}</span></div>"

        html += f"<h3>原始 JSON</h3>"
        html += f"<pre style='background:#2d3436;color:#dfe6e9;padding:12px;border-radius:6px;font-size:12px;'>{raw}</pre>"
        self.detail.setHtml(html)

    def _show_lessons(self):
        text = _load_lessons()
        self.detail.setPlainText(text)
