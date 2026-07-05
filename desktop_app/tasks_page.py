"""
Task browser page: browse, search, and inspect all generated tasks.
"""

import json
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


def _project_root():
    return Path(__file__).resolve().parent.parent


def _load_all_tasks():
    tasks_dir = _project_root() / "task_generator" / "tasks"
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
                data["_dir"] = str(td)
                tasks.append(data)
            except Exception:
                pass
    return tasks


class TasksPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tasks = []
        self._init_ui()
        self._refresh()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 20, 30, 20)

        title = QLabel("任务浏览器")
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        subtitle = QLabel("浏览所有已生成的评估任务，点击任务查看详细信息。")
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        # ── Filter bar ──
        filter_row = QHBoxLayout()

        filter_row.addWidget(QLabel("应用筛选:"))
        self.cb_filter_app = QComboBox()
        self.cb_filter_app.addItem("全部")
        self.cb_filter_app.setMinimumWidth(150)
        self.cb_filter_app.currentTextChanged.connect(self._apply_filter)
        filter_row.addWidget(self.cb_filter_app)

        filter_row.addWidget(QLabel("搜索:"))
        self.le_search = QLineEdit()
        self.le_search.setPlaceholderText("输入关键词搜索任务...")
        self.le_search.textChanged.connect(self._apply_filter)
        filter_row.addWidget(self.le_search, 1)

        self.lbl_count = QLabel("共 0 个任务")
        filter_row.addWidget(self.lbl_count)

        outer.addLayout(filter_row)

        # ── Splitter: table + detail ──
        splitter = QSplitter(Qt.Horizontal)

        # Left: task table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["任务 ID", "应用", "难度", "复杂度", "任务描述"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.currentCellChanged.connect(self._on_select)
        self.table.verticalHeader().setVisible(False)
        splitter.addWidget(self.table)

        # Right: detail view
        self.detail = QTextBrowser()
        self.detail.setOpenExternalLinks(True)
        self.detail.setPlaceholderText("点击左侧任务查看详情...")
        splitter.addWidget(self.detail)

        splitter.setSizes([500, 400])
        outer.addWidget(splitter, 1)

    def _refresh(self):
        self._tasks = _load_all_tasks()

        apps = sorted(set(t.get("app", "") for t in self._tasks))
        self.cb_filter_app.clear()
        self.cb_filter_app.addItem("全部")
        self.cb_filter_app.addItems(apps)

        self._apply_filter()

    def _apply_filter(self):
        app_filter = self.cb_filter_app.currentText()
        search = self.le_search.text().lower()

        filtered = []
        for t in self._tasks:
            if app_filter != "全部" and t.get("app") != app_filter:
                continue
            if search:
                searchable = f"{t.get('id', '')} {t.get('app', '')} {t.get('task', '')}".lower()
                if search not in searchable:
                    continue
            filtered.append(t)

        self.table.setRowCount(len(filtered))
        self._filtered = filtered

        for i, t in enumerate(filtered):
            meta = t.get("metadata", {})
            self.table.setItem(i, 0, QTableWidgetItem(t.get("id", "")))
            self.table.setItem(i, 1, QTableWidgetItem(t.get("app", "")))

            diff = str(meta.get("estimated_difficulty", meta.get("difficulty", "")))
            item_diff = QTableWidgetItem(diff)
            item_diff.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 2, item_diff)

            cplx = str(meta.get("complexity", ""))
            item_cplx = QTableWidgetItem(cplx)
            item_cplx.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 3, item_cplx)

            desc = t.get("task", "")
            if len(desc) > 100:
                desc = desc[:100] + "..."
            self.table.setItem(i, 4, QTableWidgetItem(desc))

        self.lbl_count.setText(f"共 {len(filtered)} 个任务")

    def _on_select(self, row, col, prev_row, prev_col):
        if row < 0 or row >= len(self._filtered):
            self.detail.clear()
            return

        t = self._filtered[row]
        meta = t.get("metadata", {})
        env_data = t.get("env", {})
        verif = t.get("verification", [])

        html = f"""
        <h2 style="color:#0984e3;">{t.get('id', 'N/A')}</h2>
        <table style="margin-bottom:12px;">
            <tr><td style="padding-right:16px;color:#636e72;"><b>应用</b></td>
                <td>{t.get('app', 'N/A')}</td></tr>
            <tr><td style="padding-right:16px;color:#636e72;"><b>难度</b></td>
                <td>{meta.get('estimated_difficulty', meta.get('difficulty', 'N/A'))}</td></tr>
            <tr><td style="padding-right:16px;color:#636e72;"><b>复杂度</b></td>
                <td>{meta.get('complexity', 'N/A')}</td></tr>
            <tr><td style="padding-right:16px;color:#636e72;"><b>数据可生成性</b></td>
                <td>{meta.get('data_generatability', 'N/A')}</td></tr>
        </table>

        <h3 style="color:#2d3436;">任务描述</h3>
        <p style="background:#f5f6fa;padding:12px;border-radius:6px;">
            {t.get('task', 'N/A')}
        </p>
        """

        # Env files
        files = env_data.get("files", [])
        if files:
            html += "<h3 style='color:#2d3436;'>环境文件</h3><ul>"
            for f in files:
                html += f"<li><code>{f.get('filename', '')}</code> -> <code>{f.get('sandbox_path', '')}</code></li>"
            html += "</ul>"

        # Verification
        if verif:
            html += "<h3 style='color:#2d3436;'>验证命令</h3>"
            for i, v in enumerate(verif):
                html += f"""
                <div style="background:#f5f6fa;padding:10px;border-radius:6px;margin-bottom:8px;">
                    <b>检查 {i+1}:</b> <code>{v.get('command', '')}</code><br/>
                    <span style="color:#636e72;">键: {v.get('key', '')} | 期望: {v.get('expected', '')}</span><br/>
                    <span style="color:#636e72;">{v.get('description', '')}</span>
                </div>
                """

        # Raw JSON
        raw = json.dumps(t, indent=2, ensure_ascii=False)
        html += f"""
        <h3 style="color:#2d3436;">原始 JSON</h3>
        <pre style="background:#2d3436;color:#dfe6e9;padding:12px;border-radius:6px;font-size:12px;overflow-x:auto;">{raw}</pre>
        """

        self.detail.setHtml(html)
